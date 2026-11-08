/* Özgün, Web Audio ile sentezlenen yarışma sesleri. Dış ses dosyası, telifli melodi veya ağ isteği yoktur. */
'use strict';
(()=>{
  const A=window.AudioContext||window.webkitAudioContext;
  let context=null,master=null,enabled=false,isHost=false,lastKey='',lastTick=-1;
  let musicTimer=null,musicStep=0;
  const state={phase:'lobby',index:0};
  let volume=0.30;
  const $=id=>document.getElementById(id);
  function connect(){if(!A)return false;try{if(!context){context=new A();master=context.createGain();master.gain.value=volume;master.connect(context.destination)}if(context.state==='suspended')context.resume().catch(()=>{});return true}catch(e){return false}}
  function tone(freq,time=0.14,gain=0.15,wave='sine',delay=0){if(!enabled||!isHost||!connect())return;const t=context.currentTime+delay;const o=context.createOscillator(),g=context.createGain();o.type=wave;o.frequency.setValueAtTime(freq,t);g.gain.setValueAtTime(0.0001,t);g.gain.exponentialRampToValueAtTime(Math.max(.001,gain),t+.018);g.gain.exponentialRampToValueAtTime(.0001,t+time);o.connect(g);g.connect(master);o.start(t);o.stop(t+time+.02)}
  function intro(){[392,494,587,784,659,880].forEach((n,i)=>tone(n,i===5?.4:.20,.14,'triangle',i*.13))}
  function good(){[523,659,784,1047].forEach((n,i)=>tone(n,.19,.15,'triangle',i*.085))}
  function bad(){tone(330,.3,.15,'sawtooth');tone(294,.3,.12,'sawtooth',.16);tone(220,.37,.12,'triangle',.34)}
  function tick(){tone(990,.055,.10,'square');tone(440,.06,.06,'triangle',.07)}
  function finalSound(){[392,523,659,784,1047].forEach((n,i)=>tone(n,.4,.10,'triangle',i*.12))}
  // Yarışma için özgün, düşük sesli 8 ölçülük elektronik ostinato.
  const line=[196,247,294,247,220,262,330,262,174.61,220,261.63,220,196,246.94,293.66,392];
  function pulse(){if(!enabled||!isHost||!['lobby','question'].includes(state.phase))return;const n=line[musicStep%line.length],beat=musicStep%4;
    tone(n,.23,.025,'sine');if(musicStep%2===0)tone(n*2,.12,.013,'triangle',.05);
    if(beat===0)tone(98,.2,.025,'sine');musicStep++;
  }
  function syncMusic(){if(enabled&&isHost&&['lobby','question'].includes(state.phase)){if(!musicTimer){musicTimer=setInterval(pulse,430);pulse()}}else if(musicTimer){clearInterval(musicTimer);musicTimer=null}}
  function ui(){const box=$('hostAudio');if(!box)return;box.classList.toggle('hidden',!isHost);const b=$('audioToggle');if(b){b.textContent=enabled?'🔊 Sesi kapat':'🔈 Sesi aç';b.classList.toggle('active',enabled)}}
  function enableForHost(){isHost=true;enabled=true;connect();intro();ui();syncMusic()}
  function setHost(v){isHost=!!v;if(!v){enabled=false;lastKey='';syncMusic()}ui()}
  function onState(s,host){if(!host){setHost(false);return;}setHost(true);state.phase=s.phase;state.index=s.index;
    const key=s.code+'|'+s.phase+'|'+s.index;
    if(key!==lastKey){lastKey=key;lastTick=-1;syncMusic();if(enabled){if(s.phase==='question')tone(660,.18,.09,'triangle');
      else if(s.phase==='reveal'){const st=s.roundStats;if(st){if(st.correct>0)good();else bad()}}
      else if(s.phase==='finished')finalSound()}}
  }
  // Ses açılması kullanıcı hareketi gerektirir; öğrencide çalışmaz.
  function countdown(s){if(!enabled||!isHost||s>=6||s<1||state.phase!=='question'||s===lastTick)return;lastTick=s;tick()}
  function init(){const toggle=$('audioToggle');if(!toggle)return;
    toggle.addEventListener('click',()=>{isHost=true;enabled=!enabled;if(enabled){connect();intro()}syncMusic();ui()});
    $('audioVolume').addEventListener('input',e=>{volume=Number(e.target.value)/100;if(master)master.gain.value=volume});
    $('previewCorrect').addEventListener('click',()=>{if(!enabled){enabled=true;connect()}ui();good()});
    $('previewWrong').addEventListener('click',()=>{if(!enabled){enabled=true;connect()}ui();bad()});
    $('previewIntro').addEventListener('click',()=>{if(!enabled){enabled=true;connect()}ui();intro()});
    // Sayfadan çıkarken müziği kes.
    window.addEventListener('pagehide',()=>{if(musicTimer)clearInterval(musicTimer)});
  }
  document.addEventListener('DOMContentLoaded',init);
  window.AutoQuizAudio={enableForHost,setHost,onState,countdown};
})();
