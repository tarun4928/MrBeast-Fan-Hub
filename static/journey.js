(async()=>{
 const videos=await fetchVideos(1200); const box=document.getElementById('era-videos');
 const years=[2012,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026];
 box.innerHTML=years.map(y=>{const rows=videos.filter(v=>Number(v.published_date.slice(0,4))===y);const lead=rows[0];return `<div class="era-card"><div style="display:flex;justify-content:space-between;gap:10px"><strong>${y}</strong><span class="pill">${rows.length} releases</span></div><p>${lead?escapeHtml(lead.title):'No catalogued uploads in the current snapshot.'}</p><a class="video-link" href="/discover?year=${y}">Explore this era →</a></div>`}).join('');
})();
