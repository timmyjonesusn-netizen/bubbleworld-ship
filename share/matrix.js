// static/matrix.js — lightweight falling glyphs backdrop
(() => {
  const c = document.getElementById('matrix'); if(!c) return;
  const d = c.getContext('2d'); let W,H,cols,yd=[];
  const glyphs = "01⚡︎ΛΞ01⟡Σ01"; // simple mix, soft
  function size(){
    W = c.width = innerWidth; H = c.height = innerHeight;
    cols = Math.floor(W/16); yd = Array(cols).fill(0);
  }
  addEventListener('resize', size, {passive:true}); size();
  function step(){
    d.fillStyle = "rgba(0,0,0,0.08)"; d.fillRect(0,0,W,H);
    const g1=getComputedStyle(document.body).getPropertyValue('--g1').trim()||'#C8FFF1';
    d.fillStyle = g1; d.font = "16px monospace";
    for(let i=0;i<cols;i++){
      const ch = glyphs[Math.floor(Math.random()*glyphs.length)];
      d.fillText(ch, i*16, yd[i]*16);
      if(yd[i]*16 > H || Math.random() > .975) yd[i]=0;
      yd[i]++;
    }
    requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
})();
