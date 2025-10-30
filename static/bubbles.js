// Minimal bubble field (top layer under UI)
(function(){
  const c = document.getElementById('bubble-canvas');
  if(!c) return;
  const ctx = c.getContext('2d');
  let w, h, bubbles=[];
  function resize(){
    w = c.width = innerWidth * devicePixelRatio;
    h = c.height = innerHeight * devicePixelRatio;
  }
  addEventListener('resize', resize, {passive:true});
  resize();

  function spawn(){
    const r = (Math.random()*24+8)*devicePixelRatio;
    bubbles.push({
      x: Math.random()*w,
      y: h + r + Math.random()*h*0.2,
      r,
      a: 0.05 + Math.random()*0.12,
      drift: (Math.random()-0.5)*0.4*devicePixelRatio
    });
  }
  for(let i=0;i<36;i++) spawn();

  function tick(){
    ctx.clearRect(0,0,w,h);
    for(const b of bubbles){
      b.y -= b.a*28*devicePixelRatio;
      b.x += b.drift;
      ctx.beginPath();
      ctx.arc(b.x,b.y,b.r,0,Math.PI*2);
      ctx.fillStyle = 'rgba(255,244,255,0.10)';
      ctx.fill();
      ctx.strokeStyle = 'rgba(255,244,255,0.25)';
      ctx.lineWidth = 1*devicePixelRatio;
      ctx.stroke();
    }
    bubbles = bubbles.filter(b => b.y + b.r > -40*devicePixelRatio);
    while(bubbles.length < 36) spawn();
    requestAnimationFrame(tick);
  }
  tick();
})();
