let allVideos=[];let activeTaste='';
const $=id=>document.getElementById(id);
function optionize(id,vals){$(id).insertAdjacentHTML('beforeend',vals.map(v=>`<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join(''));}
function currentFilters(){return {q:$('search').value.trim().toLowerCase(),category:$('category').value,year:$('year').value,era:$('era').value,format:$('format').value,duration:$('duration').value,views:$('views').value,sort:$('sort').value};}
function draw(){const f=currentFilters();let rows=allVideos.filter(v=>{
 const hay=(v.title+' '+v.category+' '+v.era+' '+v.taste.join(' ')).toLowerCase();
 return (!f.q||hay.includes(f.q))&&(!f.category||v.category===f.category)&&(!f.year||v.published_date.startsWith(f.year))&&(!f.era||v.era===f.era)&&(!f.format||v.format===f.format)&&(!f.duration||v.duration_band===f.duration)&&(!f.views||v.view_band===f.views)&&(!activeTaste||v.taste.includes(activeTaste));
});
 rows.sort((a,b)=>f.sort==='oldest'?a.published_date.localeCompare(b.published_date):f.sort==='views'?b.views-a.views:f.sort==='likes'?b.likes-a.likes:b.published_date.localeCompare(a.published_date));
 $('result-count').textContent=`${rows.length} videos`; 
 $('video-grid').innerHTML=rows.map(v=>`<article class="video-card"><a href="${v.url}" target="_blank" rel="noreferrer"><div class="video-thumb" style="background-image:url('${v.thumbnail}')"><span>${escapeHtml(v.category)}</span></div></a><div class="video-info"><h3>${escapeHtml(v.title)}</h3><div class="video-meta"><span>${escapeHtml(v.published_date)}</span><span>${formatNumber(v.views)} views</span></div><div class="video-tags">${[v.era,v.format,...v.taste.slice(0,2)].map(x=>`<span class="tag">${escapeHtml(x)}</span>`).join('')}</div><a class="video-link" href="${v.url}" target="_blank" rel="noreferrer">Watch on YouTube ↗</a></div></article>`).join('');
 $('empty').classList.toggle('hidden',rows.length>0);
}
(async()=>{
 allVideos=await fetchVideos(1200);
 const filters=await (await fetch('/api/filters')).json();
 optionize('category',filters.categories);optionize('year',filters.years);optionize('era',filters.eras);optionize('format',filters.formats);optionize('duration',filters.duration_bands);optionize('views',filters.view_bands);
 ['search','category','year','era','format','duration','views','sort'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',draw));
 document.querySelectorAll('[data-taste]').forEach(btn=>btn.addEventListener('click',()=>{const t=btn.dataset.taste;if(activeTaste===t){activeTaste='';btn.classList.remove('active')}else{document.querySelectorAll('[data-taste]').forEach(x=>x.classList.remove('active'));activeTaste=t;btn.classList.add('active')}draw()}));
 $('reset-filters').addEventListener('click',()=>{['search','category','year','era','format','duration','views'].forEach(id=>$(id).value='');$('sort').value='latest';activeTaste='';document.querySelectorAll('[data-taste]').forEach(x=>x.classList.remove('active'));draw();});
 draw();
})();
