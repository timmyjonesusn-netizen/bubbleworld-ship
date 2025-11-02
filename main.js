// BubbleWorld Ship Core v3.3.1 — Routing + Bubbles + Room Control

(function(){
  const rooms = [
    'engine','room1','room2','room3','room4',
    'room5','room6','room7','room8','room9'
  ];

  function route() {
    const hash = normalize(window.location.hash || '#engine');
    rooms.forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;
      if (hash === `#${id}`) show(el);
      else hide(el);
    });
    if (hash === '#room1') seedBubbles();
    else clearBubbles();
  }

  function normalize(h){
    if(!h || h==='#') return '#engine';
    return h.trim().toLowerCase().replace(/^#*!?\/?/, '#');
  }

  function show(el){ el.classList.remove('hidden'); }
  function hide(el){ el.classList.add('hidden'); }

  function clearBubbles(){
    const layer=document.getElementById('bubble-layer');
    if(layer) layer.innerHTML='';
  }

  function seedBubbles(){
    const layer=document.getElementById('bubble-layer');
    if(!layer) return;
    layer.innerHTML='';
    const n=36;
    for(let i=0;i<n;i++){
      const b=document.createElement('div');
      b.className='bubble';
      const size=24+Math.random()*120;
      b.style.width=size+'px';
      b.style.height=size+'px';
      b.style.left=Math.random()*100+'vw';
      b.style.animationDuration=(8000+Math.random()*10000)+'ms';
      b.style.animationDelay=Math.random()*6000+'ms';
      b.style.background='radial-gradient(circle at 30% 30%,rgba(255,255,255,.9),rgba(255,255,255,.15))';
      layer.appendChild(b);
    }
  }

  // listeners
  window.addEventListener('hashchange',route,false);
  window.addEventListener('load',route,false);
  setTimeout(route,100); // iOS safety poke
})();
