/* Android uses the Storage Access Framework; never expose arbitrary paths to JS. */
if (window.CertFlowNative) {
    const originalClick = HTMLAnchorElement.prototype.click;
    HTMLAnchorElement.prototype.click = function () {
        if (this.download && /^(blob:|data:)/.test(this.href)) {
            const href=this.href, name=this.download;
            (async()=>{
                try {
                    const blob=await (await fetch(href)).blob();
                    const response=await fetch('/local/exports',{method:'POST',headers:{'X-CSRFToken':document.querySelector('meta[name="csrf-token"]').content},body:blob});
                    const data=await response.json();if(!response.ok)throw Error(data.error||'Export failed');
                    CertFlowNative.save(data.token,name);
                }catch(e){alert(e.message);}
            })();return;
        }
        originalClick.call(this);
    };
}

(async()=>{
    // Hosted pages do not have these routes; check only installed runtime pages.
    if (!document.getElementById('localScheduleNote')) return;
    const status=await fetch('/mailer/status').then(r=>r.json()).catch(()=>null);
    if(!status?.local)return;
    const setting=await fetch('/local/background').then(r=>r.json());
    if(setting.platform!=='desktop')return;
    const label=document.createElement('label');label.className='info-box';
    const check=document.createElement('input');check.type='checkbox';check.checked=setting.enabled;
    check.onchange=async()=>{
        const response=await fetch('/local/background',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:check.checked})});
        if(!response.ok){check.checked=!check.checked;alert('Could not save background preference.');}
    };
    label.append(check, ' Continue scheduled email after closing this window (until logout or shutdown).');
    document.getElementById('localScheduleNote').after(label);
})();
