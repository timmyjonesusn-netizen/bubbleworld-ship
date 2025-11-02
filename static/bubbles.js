// Classic bubbles for Room 1 page (separate-page build)
(function(){
  const layer = document.getElementById('bubble-layer');
  if(!layer) return;
  layer.innerHTML = '';
  const n = 36;
  for(let i=0;i<n;i++){
    const b = document.createElement('div');
    b.className = 'bubble';
    const size = 24 + Math.random()*120;
    b.style.width = size+'px';
    b.style.height = size+'px';
    b.style.left = Math.random()*100+'vw';
    b.style.background = 'radial-gradient(circle at 30% 30%, rgba(255,255,255,.9), rgba(255,255,255,.15))';
    b.style.animationDuration = (8000+Math.random()*10000)+'ms';
    b.style.animationDelay = Math.random()*6000+'ms';
    layer.appendChild(b);
  }
})();
