/* Native-image coordinates throughout. CSS pixels are only a view transform. */
class CertificateEditor {
    constructor(root) {
        this.root = root; this.fields = []; this.columns = []; this.records = [];
        this.selected = -1; this.record = 0; this.zoom = 1; this.history = []; this.future = []; this.version = 0;
        root.innerHTML = `<div class="editor-toolbar">
            <button type="button" data-action="add">Add text</button><button type="button" data-action="duplicate">Duplicate</button><button type="button" data-action="delete">Delete</button>
            <button type="button" data-action="undo">Undo</button><button type="button" data-action="redo">Redo</button>
            <button type="button" data-action="out" aria-label="Zoom out">−</button><output class="editor-zoom">100%</output><button type="button" data-action="in" aria-label="Zoom in">+</button>
            <button type="button" data-action="fit">Fit</button><button type="button" data-action="reset">100%</button>
            <label><input type="checkbox" class="editor-snap" checked> Snap to center</label>
            <button type="button" data-action="save">Save layout</button><label class="editor-load">Open layout<input type="file" accept=".json,application/json" hidden></label>
            <label>Record <input class="editor-record" type="number" min="1" value="1"></label>
        </div><p class="editor-message" role="status">Upload a PNG or JPG template to begin. Drag text; use arrow keys for precision. Scroll to pan when zoomed.</p>
        <div class="editor-workspace"><div class="editor-viewport"><div class="editor-stage" tabindex="0" aria-label="Certificate editing canvas"><img class="editor-template" alt="Certificate template" draggable="false"><div class="editor-guide"></div></div></div>
        <aside class="editor-properties"><label>Layers<select class="editor-layers" size="4" aria-label="Text layers"></select></label><div class="editor-controls"></div></aside></div>`;
        this.stage = root.querySelector('.editor-stage'); this.viewport = root.querySelector('.editor-viewport');
        this.template = root.querySelector('.editor-template'); this.controls = root.querySelector('.editor-controls');
        this.layers = root.querySelector('.editor-layers');
        root.querySelectorAll('[data-action]').forEach(b => b.onclick = () => this.action(b.dataset.action));
        this.layers.onchange = () => { this.selected = Number(this.layers.value); this.properties(); this.paint(); };
        root.querySelector('.editor-record').onchange = e => { this.record = Math.max(0, Math.min(this.records.length - 1, Number(e.target.value) - 1)); this.refresh(); };
        root.querySelector('.editor-load input').onchange = async e => {
            try {
                const file = e.target.files[0]; if (!file || file.size > 200000) throw Error('Layout exceeds 200 KB.');
                const data = JSON.parse(await file.text());
                if (data.version !== 2 || !Array.isArray(data.fields) || data.fields.length > 100) throw Error('Unsupported layout.');
                const response = await fetch('/editor/text', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({fields:data.fields})});
                if (!response.ok) throw Error('Invalid layout fields.');
                if (this.template.naturalWidth && (data.width !== this.template.naturalWidth || data.height !== this.template.naturalHeight)) throw Error('Load a template with the layout’s original dimensions first.');
                this.remember(); this.fields = (await response.json()).normalizedFields; this.selected = this.fields.length ? 0 : -1; this.properties(); this.refresh();
            } catch (e) { this.message(e.message); }
        };
        this.stage.onkeydown = e => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') { e.preventDefault(); this.action(e.shiftKey ? 'redo':'undo'); return; }
            const f = this.fields[this.selected]; if (!f) return;
            if (e.key === 'Delete' || e.key === 'Backspace') {e.preventDefault(); this.action('delete'); return;}
            const d = {ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[e.key];
            if (d) {e.preventDefault(); this.remember(); f.X += d[0]*(e.shiftKey?10:1); f.Y += d[1]*(e.shiftKey?10:1); this.properties(); this.paint();}
        };
        new ResizeObserver(() => this.scale()).observe(this.viewport);
    }
    message(text) { this.root.querySelector('.editor-message').textContent = text; }
    snapshot() { return JSON.stringify(this.fields); }
    remember() { this.history.push(this.snapshot()); if(this.history.length>100)this.history.shift(); this.future=[]; }
    async loadTemplate(url) {
        this.template.src = url;
        try { await this.template.decode(); this.zoom=1; this.scale(); this.refresh(); }
        catch {this.message('Interactive editing requires an image template. PDF generation remains available in the existing workflow.');}
    }
    setData(columns, records) { this.columns=columns; this.records=records; this.record=0; this.root.querySelector('.editor-record').max=Math.max(1,records.length); this.properties(); this.refresh(); }
    action(action) {
        if (action === 'undo' || action === 'redo') {
            const from = action==='undo'?this.history:this.future, to=action==='undo'?this.future:this.history;
            if(!from.length)return; to.push(this.snapshot()); this.fields=JSON.parse(from.pop()); this.selected=Math.min(this.selected,this.fields.length-1);
        } else if (['in','out','fit','reset'].includes(action)) {
            this.zoom=action==='fit'?1:action==='reset'?1/this.fitScale():Math.max(.2,Math.min(8,this.zoom*(action==='in'?1.25:.8))); this.scale(); return;
        } else if (action==='save') {
            const blob=new Blob([JSON.stringify({version:2,width:this.template.naturalWidth,height:this.template.naturalHeight,columns:this.columns,fields:this.fields},null,2)],{type:'application/json'});
            const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='certflow-layout.json'; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),10000); return;
        } else {
            if(action!=='add' && this.selected<0)return; this.remember();
            if(action==='add') {this.fields.push({column:this.columns.length?0:-1,Text:'Your text',X:Math.round((this.template.naturalWidth||800)/2),Y:Math.round((this.template.naturalHeight||500)/2),FontSize:38,Font:'arial.ttf',Color:'#000000',Bold:false,Align:'center',Anchor:'top'});this.selected=this.fields.length-1;}
            if(action==='duplicate') {const f=structuredClone(this.fields[this.selected]);f.X+=20;f.Y+=20;this.fields.push(f);this.selected=this.fields.length-1;}
            if(action==='delete') {this.fields.splice(this.selected,1);this.selected=Math.min(this.selected,this.fields.length-1);}
        }
        this.properties();this.refresh();
    }
    fitScale() { return Math.min(1, Math.max(100,this.viewport.clientWidth-24)/(this.template.naturalWidth||800)); }
    scale() {
        this.factor=this.fitScale()*this.zoom;
        this.stage.style.width=`${(this.template.naturalWidth||800)*this.factor}px`;
        this.stage.style.height=`${(this.template.naturalHeight||500)*this.factor}px`;
        this.root.querySelector('.editor-zoom').textContent=`${Math.round(this.factor*100)}%`;this.paint();
    }
    properties() {
        this.layers.replaceChildren(); this.fields.forEach((f,i)=>this.layers.add(new Option(f.column===-1?f.Text:(this.columns[f.column]||`Column ${f.column+1}`),i)));this.layers.value=this.selected;
        this.controls.replaceChildren(); const f=this.fields[this.selected];if(!f)return;
        const add=(name,key,type,options)=> {
            const label=document.createElement('label');label.textContent=name;
            const input=document.createElement(options?'select':'input');input.dataset.key=key;
            if(options)options.forEach(([value,title])=>input.add(new Option(title,value)));else input.type=type;
            if(type==='checkbox')input.checked=f[key];else input.value=f[key];
            if(type==='number'){input.step=1;if(key==='FontSize'){input.min=1;input.max=400;}}
            if(key==='Text')input.maxLength=200;
            input.oninput=()=> {this.remember();f[key]=type==='checkbox'?input.checked:type==='number'||key==='column'?Number(input.value):input.value;
                if(type==='number')f[key]=Math.round(Math.max(key==='FontSize'?1:-10000,Math.min(key==='FontSize'?400:10000,f[key]||0)));
                this.refresh();};label.append(input);this.controls.append(label);
        };
        add('Content','column','', [[-1,'Static text'],...this.columns.map((c,i)=>[i,c])]);add('Static text','Text','text');
        add('Font','Font','',[['arial.ttf','Noto Sans'],['georgia.ttf','Noto Serif'],['times.ttf','Noto Serif (Times)']]);
        add('Size (original pixels)','FontSize','number');add('Bold','Bold','checkbox');add('Color','Color','color');
        add('Alignment','Align','',[['left','Left'],['center','Center'],['right','Right']]);
        const advanced=document.createElement('details');const summary=document.createElement('summary');summary.textContent='Precise position';advanced.append(summary);
        add('X (anchor)','X','number');advanced.append(this.controls.lastChild);add('Y (ink top)','Y','number');advanced.append(this.controls.lastChild);this.controls.append(advanced);
    }
    refresh() {
        clearTimeout(this.timer);const version=++this.version;
        this.timer=setTimeout(async()=>{
            try {
                const response=await fetch('/editor/text',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fields:this.fields,values:this.records[this.record]?.values||[]})});
                const data=await response.json();if(!response.ok)throw Error(data.error||'Preview unavailable');if(version!==this.version)return;
                this.tiles=data.fields;this.paint();this.message('Drag to move. Drag the corner to resize. Arrow keys nudge 1 px; Shift nudges 10 px.');
            }catch(e){if(version===this.version)this.message(e.message);}
        },100);
    }
    paint() {
        this.stage.querySelectorAll('.editor-object').forEach(e=>e.remove());
        this.fields.forEach((f,i)=>{
            const t=this.tiles?.[i];if(!t)return;
            const el=document.createElement('div');el.className='editor-object'+(i===this.selected?' selected':'');el.dataset.index=i;
            const sizeRatio=f.FontSize/(t.fontSize||f.FontSize);
            Object.assign(el.style,{left:`${(f.X+t.offset*sizeRatio)*this.factor}px`,top:`${f.Y*this.factor}px`,width:`${t.width*sizeRatio*this.factor}px`,height:`${t.height*sizeRatio*this.factor}px`});
            const img=new Image();img.src=t.image;img.draggable=false;el.append(img);
            const handle=document.createElement('span');handle.className='editor-resize';el.append(handle);
            el.onpointerdown=e=> {
                e.preventDefault();this.selected=i;this.properties();this.stage.focus();this.remember();
                const resizing=e.target===handle, start={x:e.clientX,y:e.clientY,X:f.X,Y:f.Y,size:f.FontSize};
                // Capture on the stable stage because paint replaces layer elements.
                this.stage.setPointerCapture(e.pointerId);
                this.stage.onpointermove=ev=> {
                    const dx=(ev.clientX-start.x)/this.factor,dy=(ev.clientY-start.y)/this.factor;
                    if(resizing) {f.FontSize=Math.max(1,Math.min(400,Math.round(start.size+dy)));t.fontSize=start.size;}
                    else {f.X=Math.round(start.X+dx);f.Y=Math.round(start.Y+dy);
                        const center=this.template.naturalWidth/2;
                        const snap=this.root.querySelector('.editor-snap').checked&&Math.abs(f.X-center)<8/this.factor;
                        if(snap)f.X=Math.round(center);this.stage.classList.toggle('snapping',snap);}
                    this.paint();
                };
                const finish=()=>{this.stage.onpointermove=null;this.stage.onpointerup=null;this.stage.onpointercancel=null;this.stage.classList.remove('snapping');this.properties();this.refresh();};
                this.stage.onpointerup=finish;this.stage.onpointercancel=finish;this.paint();
            };this.stage.append(el);
        });
    }
}
