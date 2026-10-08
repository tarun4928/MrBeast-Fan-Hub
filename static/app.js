function formatNumber(n){
  if(!n) return '—';
  if(n>=1e9) return (n/1e9).toFixed(1).replace('.0','')+'B';
  if(n>=1e6) return (n/1e6).toFixed(1).replace('.0','')+'M';
  if(n>=1e3) return (n/1e3).toFixed(1).replace('.0','')+'K';
  return String(n);
}
function escapeHtml(s){return String(s ?? '').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
async function fetchVideos(limit=120){const r=await fetch('/api/videos?limit='+limit);const j=await r.json();return j.videos||[];}
