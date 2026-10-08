document.getElementById('join-form').addEventListener('submit',async e=>{
 e.preventDefault();const form=e.currentTarget;const status=document.getElementById('join-status');status.className='form-status';status.textContent='Saving your entry…';
 const payload=Object.fromEntries(new FormData(form).entries());
 try{const r=await fetch('/api/join',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await r.json();if(!r.ok)throw new Error(j.error||'Something went wrong');status.className='form-status success';status.textContent=j.message;form.reset();}catch(err){status.className='form-status error';status.textContent=err.message;}
});
