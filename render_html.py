#!/usr/bin/env python3
"""Render the shared Claude Calendar (tasks.json) as one self-contained interactive HTML page: python render_html.py [out.html]
Compact view: a month you can click through, the selected day's outline underneath, next few tasks. 'Full view' shows every month."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent

CSS = """
:root{--bg:#f5f7f8;--surface:#ffffff;--ink:#16222b;--muted:#5d6e7a;--line:#d9e1e6;--accent:#0b6e8a;--accent-soft:#dcedf2;
--late:#b3261e;--late-soft:#fbe4e1;--ok:#2f7d4f;--ok-soft:#e1f1e8;--auto:#7a4fb5;--auto-soft:#ece4f7;--today:#fff4cf;--sel:#0b6e8a;--selink:#ffffff;
--sans:'IBM Plex Sans',system-ui,-apple-system,'Segoe UI',sans-serif;--mono:'IBM Plex Mono',ui-monospace,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f171c;--surface:#17232a;--ink:#e6eef2;--muted:#93a5b0;--line:#2a3a43;
--accent:#5cc2de;--accent-soft:#143946;--late:#ff8a80;--late-soft:#3d1f1d;--ok:#6fd09a;--ok-soft:#17352a;--auto:#c3a4f0;--auto-soft:#2b2140;--today:#3b3414;--sel:#5cc2de;--selink:#0f171c;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0f171c;--surface:#17232a;--ink:#e6eef2;--muted:#93a5b0;--line:#2a3a43;
--accent:#5cc2de;--accent-soft:#143946;--late:#ff8a80;--late-soft:#3d1f1d;--ok:#6fd09a;--ok-soft:#17352a;--auto:#c3a4f0;--auto-soft:#2b2140;--today:#3b3414;--sel:#5cc2de;--selink:#0f171c;color-scheme:dark}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:14px;line-height:1.45;
padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:14px 32px}
.wrap{max-width:1100px;margin:0 auto;display:flex;flex-direction:column;gap:14px}
.top{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px}
h1{font-size:1.15rem;font-weight:600;margin:0}
.sub{color:var(--muted);font-size:.8rem}
button{font:inherit;color:var(--ink);background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:4px 10px;cursor:pointer}
button:hover{border-color:var(--accent)}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
button[aria-pressed="true"]{background:var(--accent-soft);border-color:var(--accent);color:var(--accent)}
.tools{display:flex;gap:6px;flex-wrap:wrap}
.layout{display:grid;grid-template-columns:minmax(0,1fr);gap:14px}
.full .layout{grid-template-columns:minmax(0,1.6fr) minmax(260px,1fr);align-items:start}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px}
.head{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.head h2{font-size:1rem;margin:0;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:3px}
.dow{font-size:.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;text-align:center;padding:2px 0}
.cell{position:relative;min-height:44px;border:1px solid var(--line);border-radius:6px;background:transparent;padding:3px;display:flex;flex-direction:column;gap:2px;text-align:left;min-width:0}
.cell.out{opacity:.4}
.cell.today{background:var(--today)}
.cell.sel{background:var(--sel);color:var(--selink);border-color:var(--sel)}
.cell .n{font-family:var(--mono);font-size:.75rem;font-variant-numeric:tabular-nums}
.dots{display:flex;gap:3px;flex-wrap:wrap}
.dot{width:7px;height:7px;border-radius:50%;background:var(--accent)}
.dot.late{background:var(--late)}.dot.auto{background:var(--auto)}.dot.done{background:var(--ok)}
.cell.sel .dot{outline:1px solid var(--selink)}
.full .cell{min-height:84px}
.full .ev{display:block}
.ev{display:none;font-size:.7rem;line-height:1.25;padding:1px 4px;border-radius:3px;background:var(--accent-soft);color:var(--ink);overflow-wrap:anywhere}
.ev.late{background:var(--late-soft);color:var(--late)}.ev.auto{background:var(--auto-soft)}.ev.done{opacity:.55;text-decoration:line-through}
.cell.sel .ev{background:rgba(255,255,255,.2);color:var(--selink)}
.full .dots{display:none}
.out-day h2{font-size:.95rem;margin:0 0 8px}
.item{border-top:1px solid var(--line);padding:8px 0;display:flex;flex-direction:column;gap:3px}
.item:first-of-type{border-top:0}
.item .t{overflow-wrap:anywhere}
.item .when{font-family:var(--mono);font-size:.78rem;color:var(--muted)}
.item details{color:var(--muted);font-size:.82rem}
.item summary{cursor:pointer;color:var(--accent)}
.item.late .t{color:var(--late)}
.chips{display:flex;flex-wrap:wrap;gap:5px}
.chip{font-size:.7rem;padding:0 7px;border-radius:99px;background:var(--accent-soft);color:var(--accent);font-family:var(--mono)}
.chip.auto{background:var(--auto-soft);color:var(--auto)}.chip.manual,.chip.late{background:var(--late-soft);color:var(--late)}.chip.done{background:var(--ok-soft);color:var(--ok)}
.empty{color:var(--muted);font-size:.85rem}
.months{display:flex;flex-direction:column;gap:14px}
.next .row{display:grid;grid-template-columns:96px 1fr;gap:8px;padding:5px 0;border-top:1px solid var(--line);cursor:pointer;background:none;border-left:0;border-right:0;border-bottom:0;border-radius:0;width:100%;text-align:left}
.next .row:first-of-type{border-top:0}
.next .w{font-family:var(--mono);font-size:.75rem;color:var(--muted)}
.next .row.late .w{color:var(--late)}
.chatrow{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:2px}.chatname{font-size:.85rem;color:var(--accent)}.chatcopy{font-size:.75rem}
.chatlink{align-self:flex-start;font-size:.85rem;color:var(--accent);margin-top:2px}.item.late .chatlink{color:var(--accent)}
.runbtn{align-self:flex-start;margin-top:4px;border-color:var(--auto);color:var(--auto)}.runbtn:disabled{opacity:.6;cursor:default}
.pet{display:flex;align-items:center;gap:12px;background:var(--auto-soft)}.petface{font-size:1.4rem;white-space:nowrap}.petmsg{font-size:.9rem}
.pet{flex-wrap:wrap}.petsay{display:flex;flex-direction:column;flex:1;min-width:140px}.petname{font-size:.7rem;color:var(--muted);font-family:var(--mono)}.petchg{font-size:.75rem}.petface{background:none;border:0;padding:0;font-size:1.4rem;cursor:pointer}.petpick{display:flex;flex-wrap:wrap;gap:8px;width:100%;margin-top:6px}.petopt{display:flex;flex-direction:column;align-items:flex-start;gap:1px;text-align:left;min-width:128px}.petopt.on{border-color:var(--accent);background:var(--accent-soft)}.petopt .pf{font-size:1.1rem}.petopt .pl{font-weight:600}.petopt .pb{font-size:.7rem;color:var(--muted)}.petlabel{display:flex;align-items:center;gap:6px;font-size:.8rem}.petinput{font:inherit;border:1px solid var(--line);border-radius:6px;padding:3px 6px;background:var(--surface);color:var(--ink);width:10ch}
.cmdrow{display:grid;grid-template-columns:92px 1fr;gap:8px;padding:3px 0;font-size:.85rem}.cmdname{font-family:var(--mono);color:var(--accent)}.cmddesc{color:var(--ink)}
.foot{color:var(--muted);font-size:.75rem}
@media (max-width:560px){.full .layout{grid-template-columns:minmax(0,1fr)}.full .cell{min-height:56px}.full .ev{display:none}.full .dots{display:flex}}
"""

JS = r"""
(function(){
var D=JSON.parse(document.getElementById('data').textContent);
var MON=['January','February','March','April','May','June','July','August','September','October','November','December'];
var DOW=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
function pad(n){return String(n).padStart(2,'0')}
function key(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate())}
function hm(d){return pad(d.getHours())+':'+pad(d.getMinutes())}
var now=new Date(D.generated), todayKey=key(now);
var tasks=D.tasks.map(function(t){t.d=new Date(t.due);return t}).sort(function(a,b){return a.d-b.d});
var byDay={};tasks.forEach(function(t){if(t.status==='skipped')return;(byDay[key(t.d)]=byDay[key(t.d)]||[]).push(t)});
var live=tasks.filter(function(t){return t.status==='open'||t.status==='blocked'||t.status==='review'||t.status==='running'});
var st={y:now.getFullYear(),m:now.getMonth(),sel:todayKey,full:false};
try{var saved=JSON.parse(localStorage.getItem('cc-view')||'{}');if(saved.full)st.full=true}catch(e){}
var app=document.getElementById('app');
var DB=null,reqs={};
try{if(window.claude&&claude.use)claude.use('db').then(function(db){if(!db)return;DB=db;
  db.collection('runRequests').onSnapshot(function(sn){reqs={};sn.docs.forEach(function(d){if(d.exists)reqs[d.id]=d.data()});render()},function(){});render()}).catch(function(){})}catch(e){}
function el(tag,cls,text){var e=document.createElement(tag);if(cls)e.className=cls;if(text!=null)e.textContent=text;return e}
function kind(t){return t.auto?'auto':(t.sched?'scheduled':'manual')}
function isLate(t){return t.status==='open'&&t.d<now-(t.auto?15*60000:0)}
function dotClass(t){return t.status==='done'?'done':isLate(t)?'late':t.auto?'auto':''}
function monthGrid(y,m,compact){
  var card=el('div','card'),head=el('div','head');
  var prev=el('button',null,'‹');prev.setAttribute('aria-label','Previous month');
  var next=el('button',null,'›');next.setAttribute('aria-label','Next month');
  head.appendChild(compact?prev:el('span'));head.appendChild(el('h2',null,MON[m]+' '+y));head.appendChild(compact?next:el('span'));
  prev.onclick=function(){st.m--;if(st.m<0){st.m=11;st.y--}render()};
  next.onclick=function(){st.m++;if(st.m>11){st.m=0;st.y++}render()};
  card.appendChild(head);
  var g=el('div','grid');DOW.forEach(function(d){g.appendChild(el('div','dow',d))});
  var first=new Date(y,m,1),lead=(first.getDay()+6)%7,start=new Date(y,m,1-lead);
  var weeks=Math.ceil((lead+new Date(y,m+1,0).getDate())/7);
  for(var i=0;i<weeks*7;i++){
    var d=new Date(start.getFullYear(),start.getMonth(),start.getDate()+i),k=key(d),evs=byDay[k]||[];
    var c=el('button','cell'+(d.getMonth()!==m?' out':'')+(k===todayKey?' today':'')+(k===st.sel?' sel':''));
    c.type='button';c.setAttribute('aria-label',d.toDateString()+', '+evs.length+' tasks');
    c.appendChild(el('span','n',String(d.getDate())));
    var dots=el('span','dots');evs.slice(0,4).forEach(function(t){dots.appendChild(el('span','dot '+dotClass(t)))});c.appendChild(dots);
    evs.slice(0,3).forEach(function(t){c.appendChild(el('span','ev '+dotClass(t),hm(t.d)+' '+t.title.slice(0,48)))});
    (function(kk,dd){c.onclick=function(){st.sel=kk;st.y=dd.getFullYear();st.m=dd.getMonth();render()}})(k,d);
    g.appendChild(c);
  }
  card.appendChild(g);return card;
}
function outline(){
  var card=el('div','card out-day'),parts=st.sel.split('-'),d=new Date(+parts[0],+parts[1]-1,+parts[2]);
  card.appendChild(el('h2',null,d.toLocaleDateString(undefined,{weekday:'long',month:'long',day:'numeric',year:'numeric'})+(st.sel===todayKey?' (today)':'')));
  var evs=byDay[st.sel]||[];
  if(!evs.length){card.appendChild(el('p','empty','Nothing scheduled. Ask Claude to put something here, or use /calendar add.'));return card}
  evs.forEach(function(t){
    var it=el('div','item'+(isLate(t)?' late':''));
    it.appendChild(el('div','when',hm(t.d)+' · '+t.project+(t.repeat?' · repeats '+t.repeat:'')));
    it.appendChild(el('div','t',t.title));
    var ch=el('div','chips');ch.appendChild(el('span','chip '+(t.auto?'auto':''),kind(t)));
    ch.appendChild(el('span','chip '+(t.status==='done'?'done':t.status==='blocked'||t.status==='review'||isLate(t)?'late':''),isLate(t)?'overdue':t.status));
    it.appendChild(ch);
    if(t.session){var cw=el('div','chatrow'),url='claude://claude.ai/epitaxy/'+t.session;
      cw.appendChild(el('span','chatname',(t.status==='review'?'Waiting for you in chat: ':'Chat: ')+(t.sessionTitle||t.session)));
      var cb=el('button','chatcopy','Copy chat link');cb.type='button';
      (function(u,b){b.onclick=function(){var done=function(ok){b.textContent=ok?'Copied ✓ paste in your browser bar':'Select and copy: '+u;if(!ok){var inp=el('input');inp.value=u;inp.readOnly=true;inp.style.width='100%';b.parentNode.appendChild(inp);inp.select()}};
        try{navigator.clipboard.writeText(u).then(function(){done(true)},function(){done(false)})}catch(e){done(false)}}})(url,cb);
      cw.appendChild(cb);it.appendChild(cw)}
    var more=[];if(t.prompt)more.push(['What to do',t.prompt]);if(t.result)more.push(['Result',t.result]);
    (t.notes||[]).forEach(function(n){more.push(['Note',n.text])});
    if(t.sched)more.push(['Scheduled task',t.sched]);
    if((t.auto||t.sched)&&(t.status==='open'||t.status==='blocked')){
      var rq=reqs[t.id],rb=el('button','runbtn',rq&&rq.status==='requested'?'Requested ✓ (starts at the next dispatcher tick)':'Run now');
      rb.type='button';rb.disabled=!DB||!!(rq&&rq.status==='requested');
      if(!DB)rb.title='Needs the page database; open the page in claude.ai';
      (function(tt,b){b.onclick=function(){if(!DB)return;
        b.disabled=true;b.textContent='Requesting...';
        DB.doc('runRequests/'+tt.id).set({taskId:tt.id,title:tt.title,status:'requested',requestedAt:new Date().toISOString()}).catch(function(){b.disabled=false;b.textContent='Run now (failed, retry)'})}})(t,rb);
      it.appendChild(rb);
    }
    if(more.length){var dt=el('details');dt.appendChild(el('summary',null,'Details'));more.forEach(function(p){dt.appendChild(el('div',null,p[0]+': '+p[1]))});it.appendChild(dt)}
    card.appendChild(it);
  });
  return card;
}
function upNext(){
  var card=el('div','card next');card.appendChild(el('div','head')).appendChild(el('h2',null,'Up next'));
  live.slice(0,st.full?12:5).forEach(function(t){
    var r=el('button','row'+(isLate(t)?' late':''));r.type='button';
    r.appendChild(el('span','w',t.d.toLocaleDateString(undefined,{month:'short',day:'numeric'})+' '+hm(t.d)));
    r.appendChild(el('span',null,t.title));
    r.onclick=function(){st.sel=key(t.d);st.y=t.d.getFullYear();st.m=t.d.getMonth();render();window.scrollTo(0,0)};
    card.appendChild(r);
  });
  if(!live.length)card.appendChild(el('p','empty','No open tasks.'));
  return card;
}
function render(){
  app.innerHTML='';app.className='wrap'+(st.full?' full':'');
  var late=live.filter(isLate).length,week=live.filter(function(t){return t.d>=now&&t.d-now<7*864e5}).length;
  var top=el('div','top'),l=el('div');l.appendChild(el('h1',null,'Claude Calendar'));
  l.appendChild(el('div','sub',late+' overdue · '+week+' in the next 7 days · '+live.length+' open · updated '+now.toLocaleString(undefined,{weekday:'short',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})));
  var tk=el('div','sub tick');tk.id='tick';l.appendChild(tk);
  top.appendChild(l);
  var tools=el('div','tools'),tb=el('button',null,'Today');tb.onclick=function(){st.sel=todayKey;st.y=now.getFullYear();st.m=now.getMonth();render()};
  var fv=el('button',null,st.full?'Compact view':'Full view');fv.setAttribute('aria-pressed',String(st.full));
  fv.onclick=function(){st.full=!st.full;try{localStorage.setItem('cc-view',JSON.stringify({full:st.full}))}catch(e){}render()};
  tools.appendChild(tb);tools.appendChild(fv);top.appendChild(tools);app.appendChild(top);
  var P=D.pets&&D.pets.styles?D.pets:null;
  var petOn=(function(){var v='';try{v=localStorage.getItem('cc-pet-on')||''}catch(e){}return v==='1'?true:v==='0'?false:!(D.pet&&D.pet.enabled===false)})();
  if(P&&!petOn){var sp=el('button','petchg','Show pet');sp.type='button';sp.onclick=function(){try{localStorage.setItem('cc-pet-on','1')}catch(e){}render()};tools.appendChild(sp)}
  if(P&&petOn){
    var ls=function(k){try{return localStorage.getItem(k)||''}catch(e){return ''}},ss=function(k,v){try{localStorage.setItem(k,v)}catch(e){}};
    var sty=ls('cc-pet'),cp=D.pet||{};
    if(!P.styles[sty])sty=(cp.style&&P.styles[cp.style])?cp.style:P.default;
    var ps=P.styles[sty],pname=ls('cc-petname-'+sty)||cp.name||ps.name;
    var cnt=function(f){return tasks.filter(f).length};
    var rev=cnt(function(t){return t.status==='review'}),blk=cnt(function(t){return t.status==='blocked'}),run=cnt(function(t){return t.status==='running'});
    var mood,n;
    if(rev){mood='review';n=rev}else if(blk){mood='blocked';n=blk}else if(late){mood='late';n=late}else if(run){mood='running';n=run}
    else{mood=(new Date().getHours()>=23||new Date().getHours()<6)?'sleepy':'idle';n=0}
    var lines=ps.lines[mood]||ps.lines.idle||[''],line=lines[(st.petI||0)%lines.length];
    line=line.replace('{n}',n).replace('{s}',n===1?'':'s').replace('{name}',pname);
    var pet=el('div','card pet'),face=el('button','petface',ps.faces[mood]||'');
    face.type='button';face.title='Click for another line';face.setAttribute('aria-label',pname+': '+line);
    face.onclick=function(){st.petI=(st.petI||0)+1;render()};
    if(!ps.faces[mood])face.style.display='none';
    var say=el('div','petsay');say.appendChild(el('span','petname',pname));say.appendChild(el('span','petmsg',line));
    var chg=el('button','petchg',st.petOpen?'Done':'Change pet');chg.type='button';
    chg.onclick=function(){st.petOpen=!st.petOpen;render()};
    pet.appendChild(face);pet.appendChild(say);pet.appendChild(chg);
    if(st.petOpen){
      var pick=el('div','petpick');
      Object.keys(P.styles).forEach(function(k){var v=P.styles[k],b=el('button','petopt'+(k===sty?' on':''));b.type='button';
        b.appendChild(el('span','pf',v.faces.idle||'Aa'));b.appendChild(el('span','pl',v.label));b.appendChild(el('span','pb',v.blurb));
        b.onclick=function(){ss('cc-pet',k);render()};pick.appendChild(b)});
      var nm=el('input','petinput');nm.value=pname;nm.maxLength=20;nm.setAttribute('aria-label','Pet name');
      nm.onchange=function(){ss('cc-petname-'+sty,nm.value.trim());render()};
      var nl=el('label','petlabel','Name ');nl.appendChild(nm);pick.appendChild(nl);
      var off=el('button','petchg','Turn pet off');off.type='button';off.onclick=function(){ss('cc-pet-on','0');st.petOpen=false;render()};
      pick.appendChild(off);
      pet.appendChild(pick);
    }
    app.appendChild(pet);
  }
  var lay=el('div','layout'),a=el('div','months'),b=el('div','months');
  if(st.full){
    var last=live.length?live[live.length-1].d:now,y=now.getFullYear(),m=now.getMonth(),n=0;
    while((y<last.getFullYear()||(y===last.getFullYear()&&m<=last.getMonth()))&&n<8){a.appendChild(monthGrid(y,m,false));m++;if(m>11){m=0;y++}n++}
    b.appendChild(outline());b.appendChild(upNext());b.style.position='sticky';b.style.top='8px';
    lay.appendChild(a);lay.appendChild(b);
  }else{
    a.appendChild(monthGrid(st.y,st.m,true));a.appendChild(outline());a.appendChild(upNext());lay.appendChild(a);
  }
  app.appendChild(lay);
  var cmds=[['/next','What is waiting for your attention, with links to the chats'],['/scan','Scan your project folders and add the ones you care about'],['/sort','Re-sort the calendar by priority'],['/calendar','Bring up this calendar'],['/pet','Change your pet, or turn it off']];
  var ch=el('div','card cmds');ch.appendChild(el('div','head')).appendChild(el('h2',null,'Commands'));
  cmds.forEach(function(c){var row=el('div','cmdrow');row.appendChild(el('code','cmdname',c[0]));row.appendChild(el('span','cmddesc',c[1]));ch.appendChild(row)});
  ch.appendChild(el('p','empty','These are always here. Type them in any chat.'));
  app.appendChild(ch);
  app.appendChild(el('p','foot','Click a date for its outline. Auto tasks are dispatched by the calendar runner every 30 minutes (:14 and :44) while the Claude app is open; each lane runs one task at a time.'));
}
render();
function nextTick(){var d=D.dispatcher||{},mins=d.minutes||[],j=(d.jitterSeconds||0)*1000;if(!mins.length)return null;
  var n=Date.now(),best=null;for(var h=0;h<3;h++){var base=new Date(n);base.setMinutes(0,0,0);base.setHours(base.getHours()+h-1);
    mins.forEach(function(m){var t=base.getTime()+m*60000+j;if(t>n&&(best===null||t<best))best=t})}return best}
setInterval(function(){var e=document.getElementById('tick');if(!e)return;var t=nextTick();
  if(!t){e.textContent='';return}var s=Math.max(0,Math.round((t-Date.now())/1000)),m=Math.floor(s/60);
  e.textContent='Next dispatch in '+m+':'+pad(s%60)+' (about '+hm(new Date(t))+')'},1000);
})();
"""


def main() -> int:
    db = json.loads((HERE / "tasks.json").read_text(encoding="utf-8"))
    now = datetime.now().astimezone()
    keep = ("id", "title", "project", "due", "status", "auto", "repeat", "prompt", "result", "notes", "session", "sessionTitle")
    tasks = []
    for t in db["tasks"]:
        o = {k: t.get(k) for k in keep}
        o["sched"] = t.get("scheduledTaskId")
        tasks.append(o)
    disp = {}
    dj = HERE / "dispatcher.json"
    if dj.exists():
        try:
            disp = json.loads(dj.read_text(encoding="utf-8"))
        except ValueError:
            disp = {}
    pets, pcfg = {}, {}
    try:
        pets = json.loads((HERE / "pets.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    try:
        pcfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    data = json.dumps({"generated": now.isoformat(), "tasks": tasks, "dispatcher": disp, "pets": pets, "pet": {"style": pcfg.get("pet"), "name": pcfg.get("petName"), "enabled": pcfg.get("petEnabled", True) is not False}}, ensure_ascii=False).replace("</", "<\\/")
    page = "\n".join([
        "<title>Claude Calendar</title>", '<meta name="claude:viewport-fit-sides" content="cover">',
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;600&display=swap">',
        f"<style>{CSS}</style>", '<div id="app" class="wrap"></div>',
        f'<script id="data" type="application/json">{data}</script>', f"<script>{JS}</script>"])
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "calendar.html"
    path.write_text(page, encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
