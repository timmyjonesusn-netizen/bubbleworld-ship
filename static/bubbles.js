// static/bubbles.js — soft neon bubbles (visible)
(() => {
  const c = document.getElementById('bubbles'); if(!c) return;
  const d = c.getContext('2d'); let W,H,bs=[];
  function size(){ W=c.width=innerWidth; H=c.height=innerHeight; } addEventListener('resize',size,{passive:true}); size();
  const N = Math.min(150, Math.floor(W*H/9000));
  function newB(){ return {x:Math.random()*W, y:H+Math.random()*H*0.25, r:2+Math.random()*9, s:.45+Math.random()*1.1, a:.1+Math.random()*.2, t:Math.random()*6.28};}
  for(let i=0;i<N;i++) bs.push(newB());
  function rgba(hex,a){ if(hex.startsWith('rgb')){const k=hex.match(/[\d.]+/g)||[200,255,241]; return `rgba(${k[0]},${k[1]},${k[2]},${a})`; }
    let h=hex.replace('#',''); if(h.length===3)h=h.split('').map(x=>x+x).join('');
    const r=parseInt(h.slice(0,2),16),g=parseInt(h.slice(2,4),16),b=parseInt(h.slice(4,6),16); return `rgba(${r},${g},${b},${a})`; }
  function step(){
    d.clearRect(0,0,W,H);
    const g1=getComputedStyle(document.body).getPropertyValue('--g1').trim()||'#C8FFF1';
    const g2=getComputedStyle(document.body).getPropertyValue('--g2').trim()||'#00FFD0';
    for(const b of bs){
      b.y-=b.s; b.x+=Math.sin(b.t+=.008)*.2;
      d.beginPath(); d.arc(b.x,b.y,b.r*2.4,0,6.28); d.fillStyle=rgba(g2,b.a*.35); d.fill();
      d.beginPath(); d.arc(b.x,b.y,b.r,0,6.28); d.fillStyle=rgba(g1,b.a); d.fill();
      if(b.y<-20) Object.assign(b,newB(),{y:H+20});
    }
    requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
})();
