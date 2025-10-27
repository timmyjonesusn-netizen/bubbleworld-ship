const field = document.getElementById('bubbleField');
function spawnBubble() {
  const b = document.createElement('div');
  b.className = 'bubble';
  const s = 40 + Math.random() * 120;
  b.style.width = s + 'px';
  b.style.height = s + 'px';
  b.style.left = Math.random() * 100 + 'vw';
  b.style.bottom = '-160px';
  const d = 10 + Math.random() * 12;
  b.style.animationDuration = d + 's';
  field.appendChild(b);
  setTimeout(()=>field.removeChild(b), d * 1000);
}
setInterval(()=>{spawnBubble();if(Math.random()<0.4)spawnBubble();},1200);
