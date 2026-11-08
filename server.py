#!/usr/bin/env python3
"""Kütüphanesiz SSE/HTTP gerçek zamanlı otomotiv yarışması sunucusu."""
import os, json, time, math, re, secrets, random, threading, queue, io
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

ROOT=Path(__file__).resolve().parent
QUESTIONS=json.loads((ROOT/'questions.json').read_text(encoding='utf8'))
PORT=int(os.environ.get('PORT','8000'))
rooms={}
lock=threading.RLock()
listeners=defaultdict(set)
DURATION=int(os.environ.get('QUESTION_SECONDS','25'))
QUESTION_COUNT=int(os.environ.get('QUESTION_COUNT','15'))


def code_new():
    alphabet='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    while True:
        code=''.join(secrets.choice(alphabet) for _ in range(6))
        if code not in rooms:return code

def ranking(r):
    return sorted([{'id':p['id'],'name':p['name'],'score':p['score'],'correct':p['correct'],'streak':p['streak'],'online':p['online']} for p in r['players'].values()],key=lambda p:(-p['score'],-p['correct'],p['name'].lower()))

def state(r,role,player_id=None):
    now=time.time(); ix=r['idx']; q=r['questions'][ix] if 0 <= ix < len(r['questions']) else None
    reveal=r['phase'] in ('reveal','finished')
    return {'code':r['code'],'phase':r['phase'],'index':ix+1 if ix>=0 else 0,'total':len(r['questions']),
      'deadline':round(r['deadline']*1000),'serverNow':round(now*1000),'duration':DURATION,
      'question':({'q':q['q'],'options':q['options'],'topic':q['topic'],'visual':q['visual'],'page':q['page'],
         **({'answer':q['answer'],'explanation':q['explanation']} if reveal else {})} if q else None),
      'ranking':ranking(r),'participants':len(r['players']),
      'answered':len(r['answers']),'joined':r['created'],
      'myId':player_id,'myAnswer':r['answers'].get(player_id),'myScore':r['players'].get(player_id,{}).get('score',0),
      'host':role=='host'}

def emit(code):
    with lock:
      r=rooms.get(code)
      if not r:return
      for role,pid,q in list(listeners[code]):
        try:q.put_nowait(json.dumps(state(r,role,pid),ensure_ascii=False))
        except queue.Full:pass

def advance(r):
    r['idx']+=1
    if r['idx']>=len(r['questions']):r['phase']='finished';r['deadline']=0
    else:r['phase']='question';r['deadline']=time.time()+DURATION;r['answers']={};r['startedAt']=time.time()

def tick():
    while True:
      time.sleep(.3)
      with lock:
       for c,r in list(rooms.items()):
        if r['phase']=='question' and time.time()>=r['deadline']:
          r['phase']='reveal';emit(c)
threading.Thread(target=tick,daemon=True).start()

class Handler(BaseHTTPRequestHandler):
 protocol_version='HTTP/1.1'
 def log_message(self,*args):pass
 def headers_(self,status=200,ctype='application/json; charset=utf-8',length=None):
    self.send_response(status);self.send_header('Content-Type',ctype)
    self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
    if length is not None:self.send_header('Content-Length',str(length))
    self.end_headers()
 def respond(self,data,status=200):
    b=json.dumps(data,ensure_ascii=False).encode();self.headers_(status,length=len(b));self.wfile.write(b)
 def read_json(self):
    try:
      n=int(self.headers.get('Content-Length','0'))
      if n>8192 or n<0:raise ValueError('İstek çok büyük')
      return json.loads(self.rfile.read(n) or '{}')
    except Exception: return {}
 def identify(self,code,d):
    r=rooms.get(code)
    if not r:return None,None,'Oda bulunamadı'
    if d.get('hostToken')==r['hostToken']:return r,'host',None
    pid=d.get('playerId');token=d.get('playerToken')
    if pid in r['players'] and r['players'][pid]['token']==token:return r,pid,None
    return r,None,'Oturum izni yok'
 def do_GET(self):
    u=urlparse(self.path);p=u.path
    if p=='/health':return self.respond({'ok':True,'rooms':len(rooms)})
    if p=='/api/events':
      v=parse_qs(u.query);code=v.get('code',[''])[0].upper();data={k:vv[0] for k,vv in v.items()};
      with lock:
       r,who,err=self.identify(code,data)
       if err:return self.respond({'error':err},403)
       role='host' if who=='host' else 'player';pid=None if role=='host' else who
       q=queue.Queue(maxsize=30);listener=(role,pid,q);listeners[code].add(listener)
       initial=json.dumps(state(r,role,pid),ensure_ascii=False)
      self.headers_(200,'text/event-stream; charset=utf-8');self.wfile.flush()
      try:
       self.wfile.write(('data: '+initial+'\n\n').encode());self.wfile.flush()
       while True:
        try:msg=q.get(timeout=15);chunk='data: '+msg+'\n\n'
        except queue.Empty:chunk=': keepalive\n\n'
        self.wfile.write(chunk.encode());self.wfile.flush()
      except (BrokenPipeError,ConnectionResetError,TimeoutError,OSError):pass
      finally:
       with lock:listeners[code].discard(listener)
      return
    if p=='/api/qr':
      v=parse_qs(u.query);code=v.get('code',[''])[0].upper();
      if code not in rooms:return self.respond({'error':'Oda yok'},404)
      origin=self.headers.get('X-Forwarded-Proto','http').split(',')[0]+'://'+self.headers.get('Host','localhost:'+str(PORT))
      link=origin+'/join?code='+code
      try:
       import qrcode
       img=qrcode.make(link)
       b=io.BytesIO();img.save(b,format='PNG');raw=b.getvalue()
       self.headers_(200,'image/png',len(raw));self.wfile.write(raw)
      except ImportError:
       return self.respond({'error':'QR kod oluşturmak için pip install qrcode[pil] çalıştırın','link':link},503)
      return
    # Frontend routes
    file='index.html'
    if p.startswith('/assets/'):
      file=p[len('/'):]
    path=(ROOT/'public'/file).resolve()
    if not path.is_relative_to((ROOT/'public').resolve()) or not path.is_file():return self.respond({'error':'Bulunamadı'},404)
    buf=path.read_bytes();ext=path.suffix
    mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml'}
    self.headers_(200,mime.get(ext,'application/octet-stream'),len(buf));self.wfile.write(buf)
 def do_POST(self):
    path=urlparse(self.path).path;d=self.read_json();code=str(d.get('code','')).upper().strip()
    if path=='/api/create':
     with lock:
      code=code_new();r={'code':code,'hostToken':secrets.token_urlsafe(24),'created':time.time(),'phase':'lobby','idx':-1,
        'questions':random.sample(QUESTIONS,min(QUESTION_COUNT,len(QUESTIONS))),'players':{},'answers':{},'deadline':0}
      rooms[code]=r
     return self.respond({'code':code,'hostToken':r['hostToken']})
    if path=='/api/join':
     name=re.sub(r'\s+',' ',str(d.get('name','')).strip())[:25]
     if len(name)<2:return self.respond({'error':'İsim en az 2 karakter olmalı'},400)
     with lock:
      r=rooms.get(code)
      if not r:return self.respond({'error':'Geçersiz oda kodu'},404)
      if r['phase']!='lobby':return self.respond({'error':'Yarışma başladı. Yeni katılım kapalı.'},409)
      if len(r['players'])>=80:return self.respond({'error':'Oda dolu'},409)
      if any(p['name'].casefold()==name.casefold() for p in r['players'].values()):return self.respond({'error':'Bu isim kullanılıyor'},409)
      pid=secrets.token_urlsafe(9);token=secrets.token_urlsafe(24)
      r['players'][pid]={'id':pid,'token':token,'name':name,'score':0,'correct':0,'streak':0,'online':True}
      emit(code)
     return self.respond({'code':code,'playerId':pid,'playerToken':token})
    if path=='/api/action':
     with lock:
      r,who,err=self.identify(code,d)
      if err:return self.respond({'error':err},403)
      action=d.get('action')
      if who=='host':
       if action=='start' and r['phase']=='lobby':
        if len(r['players'])<1:return self.respond({'error':'Önce en az bir öğrenci katılmalı'},409)
        advance(r)
       elif action=='reveal' and r['phase']=='question':r['phase']='reveal'
       elif action=='next' and r['phase']=='reveal':advance(r)
       elif action=='finish' and r['phase'] in ('question','reveal'):r['phase']='finished';r['deadline']=0
       elif action=='restart':
        r['questions']=random.sample(QUESTIONS,min(QUESTION_COUNT,len(QUESTIONS)))
        r['idx']=-1;r['phase']='lobby';r['answers']={};r['deadline']=0
        for p in r['players'].values():p.update(score=0,correct=0,streak=0)
       else:return self.respond({'error':'Bu işlem şu anda kullanılamaz'},409)
      elif action=='answer':
       if r['phase']!='question' or time.time()>=r['deadline']:return self.respond({'error':'Yanıt süresi doldu'},409)
       if who in r['answers']:return self.respond({'error':'Bu soruyu zaten cevapladınız'},409)
       try:answer=int(d.get('answer'))
       except: return self.respond({'error':'Geçersiz seçenek'},400)
       if answer not in (0,1,2,3):return self.respond({'error':'Geçersiz seçenek'},400)
       question=r['questions'][r['idx']];p=r['players'][who]
       correct=answer==question['answer']
       remaining=max(0,r['deadline']-time.time())
       gained=(1000+round(remaining/DURATION*500)+min(p['streak'],4)*100) if correct else 0
       if correct:p['correct']+=1;p['streak']+=1;p['score']+=gained
       else:p['streak']=0
       r['answers'][who]={'choice':answer,'correct':correct,'gained':gained}
       if len(r['answers'])==len(r['players']):r['phase']='reveal'
      else:return self.respond({'error':'Yetkisiz işlem'},403)
      emit(code)
     return self.respond({'ok':True})
    return self.respond({'error':'Bilinmeyen işlem'},404)

if __name__=='__main__':
 print(f'Otomotiv Kahoot | http://localhost:{PORT} | {len(QUESTIONS)} soru',flush=True)
 ThreadingHTTPServer(('0.0.0.0',PORT),Handler).serve_forever()
