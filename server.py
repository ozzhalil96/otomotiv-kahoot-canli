#!/usr/bin/env python3
"""Kütüphanesiz SSE/HTTP gerçek zamanlı otomotiv yarışması sunucusu."""
import os, json, time, math, re, secrets, random, threading, queue, io, csv, base64, urllib.request, urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

ROOT=Path(__file__).resolve().parent
QUESTIONS=json.loads((ROOT/'questions.json').read_text(encoding='utf8'))
QUESTION_FILE=ROOT/'questions.json'

PORT=int(os.environ.get('PORT','8000'))
rooms={}
lock=threading.RLock()
listeners=defaultdict(set)
DURATIONS={'Kolay':15,'Orta':25,'Zor':40}
def question_duration(q): return DURATIONS.get(q.get('difficulty'),25)
QUESTION_COUNT=int(os.environ.get('QUESTION_COUNT','30'))
LEVELS=('Kolay','Orta','Zor')
def select_questions():
    chosen=[]
    for level in LEVELS:
        subset=[q for q in QUESTIONS if q.get('difficulty')==level]
        random.shuffle(subset)
        chosen.extend(subset[:10])
    return chosen


def validate_question(raw):
    if not isinstance(raw,dict): raise ValueError('Geçersiz soru verisi')
    q={}
    for field,limit in [('q',500),('topic',90),('explanation',800)]:
        value=str(raw.get(field,'')).strip()
        if not value or len(value)>limit:raise ValueError(field+' alanı boş ya da fazla uzun')
        q[field]=value
    if raw.get('difficulty') not in LEVELS:raise ValueError('Zorluk seviyesi geçersiz')
    q['difficulty']=raw['difficulty']
    opts=raw.get('options')
    if not isinstance(opts,list) or len(opts)!=4 or any(not isinstance(o,str) or not o.strip() or len(o)>200 for o in opts):
        raise ValueError('Dört dolu seçenek gerekli')
    q['options']=[o.strip() for o in opts]
    if len(set(x.casefold() for x in q['options']))!=4:raise ValueError('Şıklar birbirinden farklı olmalı')
    a=raw.get('answer')
    if type(a)!=int or not 0<=a<=3:raise ValueError('Doğru şık A–D arasında olmalı')
    q['answer']=a
    kind=raw.get('kind','standard')
    if kind not in ('standard','visual','fault'):raise ValueError('Soru türü geçersiz')
    q['kind']=kind
    visual=raw.get('visual','drivetrain')
    allowed=('drivetrain','clutch','converter','gearbox','differential','clutch_hotspot','diff_hotspot','converter_hotspot','gearbox_hotspot')
    if visual not in allowed:raise ValueError('Görsel seçimi geçersiz')
    q['visual']=visual
    try:page=int(raw.get('page',36))
    except (ValueError,TypeError):raise ValueError('Kitap sayfası geçersiz')
    if not 1<=page<=1000:raise ValueError('Kitap sayfası geçersiz')
    q['page']=page
    return q


def github_persist(bank):
    token=os.environ.get('GITHUB_WRITE_TOKEN','').strip()
    repo=os.environ.get('GITHUB_REPO','').strip()
    if not token or not repo:
        return False
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):
        raise ValueError('GITHUB_REPO sahibi/depo formatında olmalı')
    url=f'https://api.github.com/repos/{repo}/contents/questions.json'
    headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'OtomotivKahoot-Editor'}
    req=urllib.request.Request(url,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=12) as r: metadata=json.load(r)
        payload={'message':'Otomotiv Kahoot: öğretmen panelinden soru bankası güncellendi',
           'content':base64.b64encode((json.dumps(bank,ensure_ascii=False,indent=2)+'\n').encode()).decode(),
           'sha':metadata['sha']}
        req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={**headers,'Content-Type':'application/json'},method='PUT')
        with urllib.request.urlopen(req,timeout=15) as r:r.read()
    except (urllib.error.URLError,KeyError,ValueError) as e:
        raise ValueError('GitHub kalıcı kayıt başarısız: '+str(e)[:200])
    return True


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
      'deadline':round(r['deadline']*1000),'serverNow':round(now*1000),'duration':question_duration(q) if q else 0,
      'question':({'q':q['q'],'options':q['options'],'topic':q['topic'],'difficulty':q.get('difficulty','Orta'),'visual':q['visual'],'page':q['page'],'kind':q.get('kind','standard'),
         **({'answer':q['answer'],'explanation':q['explanation']} if reveal else {})} if q else None),
      'ranking':ranking(r),'participants':len(r['players']),
      'answered':len(r['answers']),'joined':r['created'],
      'myId':player_id,'myAnswer':r['answers'].get(player_id),'myScore':r['players'].get(player_id,{}).get('score',0),
      'host':role=='host','analysis':r['history'] if role=='host' else None, 'review':(r['review'].get(player_id,[]) if role!='host' and r['phase']=='finished' else None), 'roundStats':({'correct':sum(1 for a in r['answers'].values() if a['correct']), 'wrong':sum(1 for a in r['answers'].values() if not a['correct'])} if role=='host' and reveal else None)}

def emit(code):
    with lock:
      r=rooms.get(code)
      if not r:return
      for role,pid,q in list(listeners[code]):
        try:q.put_nowait(json.dumps(state(r,role,pid),ensure_ascii=False))
        except queue.Full:pass

def finalize_round(r):
    if r['idx'] < 0 or r['idx'] >= len(r['questions']): return
    if any(item['index']==r['idx']+1 for item in r['history']): return
    q=r['questions'][r['idx']]
    answers=list(r['answers'].values()); total=len(r['players']); correct=sum(bool(a['correct']) for a in answers)
    choices=[sum(1 for a in answers if a['choice']==i) for i in range(4)]
    for pid in r['players']:
        ans=r['answers'].get(pid)
        r['review'].setdefault(pid,[]).append({'index':r['idx']+1,'q':q['q'],'topic':q['topic'],
           'options':q['options'],'answer':q['answer'],'choice':ans['choice'] if ans else None,
           'correct':bool(ans and ans['correct']),'explanation':q['explanation'],'page':q['page']})
    r['history'].append({'index':r['idx']+1,'difficulty':q['difficulty'],'topic':q['topic'],
      'question':q['q'],'kind':q.get('kind','standard'),'page':q['page'],'correctChoice':q['answer'],
      'correct':correct,'wrong':len(answers)-correct,'unanswered':max(0,total-len(answers)),
      'total':total,'rate':round(100*correct/total,1) if total else 0,
      'choices':choices,'avgSeconds':round(sum(a['elapsed'] for a in answers)/len(answers),1) if answers else None})

def advance(r):
    r['idx']+=1
    if r['idx']>=len(r['questions']):r['phase']='finished';r['deadline']=0
    else:
      r['phase']='question';r['startedAt']=time.time();r['deadline']=r['startedAt']+question_duration(r['questions'][r['idx']]);r['answers']={}

def tick():
    while True:
      time.sleep(.3)
      with lock:
       for c,r in list(rooms.items()):
        if r['phase']=='question' and time.time()>=r['deadline']:
          finalize_round(r);r['phase']='reveal';emit(c)
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
    if p=='/api/report.csv':
      v=parse_qs(u.query);code=v.get('code',[''])[0].upper()
      with lock:
       r,who,err=self.identify(code,{'code':code,'hostToken':v.get('hostToken',[''])[0]})
       if err or who!='host':return self.respond({'error':'Bu raporu yalnızca öğretmen alabilir'},403)
       rows=list(r['history'])
      output=io.StringIO(); writer=csv.writer(output,delimiter=';')
      writer.writerow(['Soru','Seviye','Konu','Soru metni','Tür','Kitap sayfası','Doğru şık','Doğru','Yanlış','Boş','Katılımcı','Başarı %','Ort. yanıt saniye','A','B','C','D'])
      for x in rows:
       writer.writerow([x['index'],x['difficulty'],x['topic'],x['question'],x['kind'],x['page'],'ABCD'[x['correctChoice']],x['correct'],x['wrong'],x['unanswered'],x['total'],x['rate'],x['avgSeconds'] or '',*x['choices']])
      raw=('\ufeff'+output.getvalue()).encode('utf-8');self.headers_(200,'text/csv; charset=utf-8',len(raw));self.wfile.write(raw);return
    if p=='/api/questions/export':
      v=parse_qs(u.query);code=v.get('code',[''])[0].upper()
      with lock:
       r,who,err=self.identify(code,{'hostToken':v.get('hostToken',[''])[0]})
       if err or who!='host':return self.respond({'error':'Öğretmen izni gerekli'},403)
       raw=(json.dumps(QUESTIONS,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
      self.headers_(200,'application/json; charset=utf-8',len(raw));self.wfile.write(raw);return
    if p=='/api/questions':
      v=parse_qs(u.query);code=v.get('code',[''])[0].upper()
      with lock:
       r,who,err=self.identify(code,{'hostToken':v.get('hostToken',[''])[0]})
       if err or who!='host':return self.respond({'error':'Öğretmen izni gerekli'},403)
       return self.respond({'questions':QUESTIONS,'persistent':bool(os.environ.get('GITHUB_WRITE_TOKEN') and os.environ.get('GITHUB_REPO')),
          'message':'GitHub kaydı etkin' if os.environ.get('GITHUB_WRITE_TOKEN') and os.environ.get('GITHUB_REPO') else 'Kalıcı GitHub kaydı ayarlı değil; yapılan değişiklikler sunucu yeniden başlatılınca kaybolabilir. JSON yedeğini indiriniz.'})
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
        'questions':select_questions()[:QUESTION_COUNT],'players':{},'answers':{},'history':[],'review':{},'deadline':0}
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
    if path=='/api/questions/save':
     with lock:
      r,who,err=self.identify(code,d)
      if err or who!='host':return self.respond({'error':'Sadece öğretmen soru düzenleyebilir'},403)
      if r['phase'] not in ('lobby','finished'):
       return self.respond({'error':'Yarışma sürerken soru düzenleme kapalı'},409)
      global QUESTIONS
      try:
       operation=d.get('operation');index=d.get('index')
       bank=list(QUESTIONS)
       if operation=='add':
        if len(bank)>=150:raise ValueError('Soru limiti: 150')
        bank.append(validate_question(d.get('question')))
       elif operation=='edit':
        if type(index)!=int or not 0<=index<len(bank):raise ValueError('Soru seçimi geçersiz')
        bank[index]=validate_question(d.get('question'))
       elif operation=='delete':
        if type(index)!=int or not 0<=index<len(bank):raise ValueError('Soru seçimi geçersiz')
        if sum(q['difficulty']==bank[index]['difficulty'] for q in bank)<=1:
            raise ValueError('Her düzeyde en az bir soru bulunmalı')
        bank.pop(index)
       else:raise ValueError('Geçersiz işlem')
       # Remote persistence before applying local changes.
       persistent=github_persist(bank)
       tmp=QUESTION_FILE.with_suffix('.tmp')
       try:
        tmp.write_text(json.dumps(bank,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        tmp.replace(QUESTION_FILE)
       except OSError:
        # Read-only deployment filesystem: current server remains functional.
        pass
       QUESTIONS=bank
       # Lobby refreshes selection from updated bank, without disturbing players.
       if r['phase']=='lobby':r['questions']=select_questions()[:QUESTION_COUNT]
       emit(code)
      except (ValueError,TypeError) as exc:
       return self.respond({'error':str(exc)},400)
     return self.respond({'ok':True,'persistent':persistent,'count':len(QUESTIONS)})
    if path=='/api/action':
     with lock:
      r,who,err=self.identify(code,d)
      if err:return self.respond({'error':err},403)
      action=d.get('action')
      if who=='host':
       if action=='start' and r['phase']=='lobby':
        if len(r['players'])<1:return self.respond({'error':'Önce en az bir öğrenci katılmalı'},409)
        advance(r)
       elif action=='reveal' and r['phase']=='question':finalize_round(r);r['phase']='reveal'
       elif action=='next' and r['phase']=='reveal':advance(r)
       elif action=='finish' and r['phase'] in ('question','reveal'):
        if r['phase']=='question':finalize_round(r)
        r['phase']='finished';r['deadline']=0
       elif action=='restart':
        r['questions']=select_questions()[:QUESTION_COUNT]
        r['idx']=-1;r['phase']='lobby';r['answers']={};r['history']=[];r['review']={};r['deadline']=0
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
       gained=(1000+round(remaining/question_duration(question)*500)+min(p['streak'],4)*100) if correct else 0
       if correct:p['correct']+=1;p['streak']+=1;p['score']+=gained
       else:p['streak']=0
       r['answers'][who]={'choice':answer,'correct':correct,'gained':gained,'elapsed':round(time.time()-r['startedAt'],2)}
       if len(r['answers'])==len(r['players']):finalize_round(r);r['phase']='reveal'
      else:return self.respond({'error':'Yetkisiz işlem'},403)
      emit(code)
     return self.respond({'ok':True})
    return self.respond({'error':'Bilinmeyen işlem'},404)

if __name__=='__main__':
 print(f'Otomotiv Kahoot | http://localhost:{PORT} | {len(QUESTIONS)} soru',flush=True)
 ThreadingHTTPServer(('0.0.0.0',PORT),Handler).serve_forever()
