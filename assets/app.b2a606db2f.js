
(function(){
/* search removed 2026-10-02 (Billy): q is a stub so filter logic keeps working
   with an always-empty term; no search box is rendered. */
var q={value:'',addEventListener:function(){},focus:function(){}},gs=document.getElementById('fgenre'),
    bs=document.getElementById('fbook'),
    tboxes=document.querySelectorAll('input[name=ftype]'),
    count=document.getElementById('count'),nores=document.getElementById('noresults'),
    toastEl=document.getElementById('toast'),
    total=document.querySelectorAll('.card:not([data-fb])').length,
    manual={},toastT=null,RM=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
function toast(msg,ms){
  /* #toast is rendered after this script: look it up lazily (was null -> Save/Copy threw) */
  toastEl=toastEl||document.getElementById('toast');if(!toastEl)return;
  toastEl.textContent=msg;toastEl.classList.add('show');
  clearTimeout(toastT);toastT=setTimeout(function(){toastEl.classList.remove('show');},ms||1500);
}
function jesc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
var crumbs=document.getElementById('crumbs');
function updateCrumbs(){
  var open=document.querySelectorAll('.book:not(.collapsed):not(.hidden)'),b=open.length?open[open.length-1]:null;
  var h='<a href="#" data-crumb="root">All books</a>';
  if(b){
    var g=b.getAttribute('data-genre'),gh=document.querySelector('h2.genre[data-genre="'+g+'"]');
    h+='<span class="csep"> \u203a </span>'+(gh?'<a href="#'+gh.id+'">'+jesc(g)+'</a>':jesc(g))+'<span class="csep"> \u203a </span><span class="ccur">'+jesc(b.getAttribute('data-book'))+'</span>';
  }
  crumbs.innerHTML=h;
}
crumbs.addEventListener('click',function(e){
  var r=e.target.closest('[data-crumb="root"]');
  if(r){e.preventDefault();window.scrollTo({top:0,behavior:RM?'auto':'smooth'});}
});
function setBook(book,expand){
  book.classList.toggle('collapsed',!expand);
  manual[book.id]=expand;
  var hd=book.querySelector('.bookhead');
  if(hd)hd.setAttribute('aria-expanded',expand?'true':'false');
  updateCrumbs();
}
/* phase 4: on narrow screens books behave as an accordion - opening one
   closes the others, so the page stays a tidy scan list */
var MOBQ=window.matchMedia?matchMedia('(max-width:700px)'):null;
function accordionize(except){
  if(!(MOBQ&&MOBQ.matches))return;
  document.querySelectorAll('.book:not(.collapsed)').forEach(function(b){
    if(b!==except)setBook(b,false);
  });
}
function checkedTypes(){
  var v=[];
  for(var i=0;i<tboxes.length;i++)if(tboxes[i].checked)v.push(tboxes[i].value);
  return v;
}
function updateTypeUI(){
  var n=checkedTypes().length,tc=document.getElementById('tcount'),cl=document.getElementById('cleartypes');
  if(n){tc.textContent=n;tc.hidden=false;}else{tc.hidden=true;}
  cl.hidden=!n;
}
function setHash(h){
  if(history.replaceState){try{history.replaceState(null,'',location.pathname+location.search+h);}catch(_){}}
}
function syncURL(){
  if(!history.replaceState)return;
  var p,term=q.value.trim(),tvs=checkedTypes();
  try{p=new URLSearchParams(location.search);}catch(_){p=new URLSearchParams();}
  if(term)p.set('q',term);else p.delete('q');
  if(tvs.length)p.set('type',tvs.join(','));else p.delete('type');
  if(gs.value)p.set('g',gs.value);else p.delete('g');
  if(bs.value)p.set('b',bs.value);else p.delete('b');
  var qs=p.toString();
  try{history.replaceState(null,'',location.pathname+(qs?'?'+qs:'')+location.hash);}catch(_){}
}
/* search (2026-09-30): every typed word must match (AND), each word as a
   light-stemmed prefix at a word start (negotiate ~ negotiation, hire ~ hiring).
   If no rip has every word, fall back to rips matching any word, and say so. */
var STOP={a:1,an:1,the:1,and:1,or:1,of:1,to:1,in:1,on:1,for:1,with:1,my:1,i:1,is:1,it:1,how:1,what:1,do:1,me:1,at:1,by:1};
function stem(w){
  if(w.length<=3)return w;
  var s=w.replace(/(ational|ations|ation|ating|ated|ates|ate|ings|ing|ied|ies|ers|er|ed|es|ly|ments|ment|s|e)$/,'');
  return s.length>=3?s:w.slice(0,3);
}
function qStems(term){
  var ws=term.toLowerCase().match(/[\p{L}\p{N}]+/gu)||[],out=[],i;
  var content=ws.filter(function(w){return !STOP[w];});
  if(!content.length)content=ws;
  for(i=0;i<content.length;i++)if(out.indexOf(stem(content[i]))<0)out.push(stem(content[i]));
  return out;
}
function reEsc(x){return x.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');}
function stemRes(st){return st.map(function(x){return new RegExp('(?:^|[^\\p{L}\\p{N}])'+reEsc(x),'u');});}
/* perf (2026-09-30): the search index is built in JS from the card text on
   first use, instead of shipping every card's text twice (data-search was
   ~608 KB, 22% of the page). */
var _stext={};
function cardText(c){
  var id=c.id,t=_stext[id];if(t!==undefined)return t;
  function tx(sel){var el=c.querySelector(sel);return el?el.textContent:'';}
  t=[tx('.ctitle'),tx('.steal'),tx('.why').replace(/^\s*Why it matters:\s*/,''),tx('.uw')].join(' ').toLowerCase();
  _stext[id]=t;return t;
}
var searchMode='all';
function apply(fromInput){
  var term=q.value.trim().toLowerCase(),
      gv=gs.value,bv=bs.value,tvs=checkedTypes(),
      filtering=!!(term||gv||bv||tvs.length),
      res=term?stemRes(qStems(term)):[],
      all=document.querySelectorAll('.card:not([data-fb])'),pass=[],hit=[],i,c,t,k,n;
  for(i=0;i<all.length;i++){
    c=all[i];
    pass[i]=!((gv&&c.dataset.genre!==gv)||(bv&&c.dataset.book!==bv)||(tvs.length&&tvs.indexOf(c.dataset.type)<0));
    hit[i]=0;
    if(pass[i]&&res.length){t=cardText(c);for(k=0,n=0;k<res.length;k++)if(res[k].test(t))n++;hit[i]=n;}
  }
  searchMode='all';
  if(res.length>1){
    var anyAll=false;for(i=0;i<all.length;i++)if(pass[i]&&hit[i]===res.length){anyAll=true;break;}
    if(!anyAll)searchMode='any';
  }
  for(i=0;i<all.length;i++){
    c=all[i];
    var ok=pass[i]&&(!res.length||(searchMode==='all'?hit[i]===res.length:hit[i]>0));
    c.classList.toggle('hidden',!ok);
    if(fromInput)c.classList.toggle('open',!!term&&ok||(!term&&ok&&c.dataset.genre==='Thesis'));
  }
  var sn=document.getElementById('searchnote');
  if(sn){sn.hidden=searchMode!=='any';if(searchMode==='any')sn.innerHTML='No rip matches every word of &ldquo;'+jesc(q.value.trim())+'&rdquo; &mdash; showing rips that match any of them.';}
  document.querySelectorAll('.book').forEach(function(b){
    var vis=!!b.querySelector('.card:not(.hidden)');
    b.classList.toggle('hidden',!vis);
    if(vis){
      if(filtering){b.classList.remove('collapsed');}
      else{b.classList.toggle('collapsed',!manual[b.id]);}
      var hd=b.querySelector('.bookhead');
      if(hd)hd.setAttribute('aria-expanded',b.classList.contains('collapsed')?'false':'true');
      syncXall(b);
    }
  });
  /* full-book deep dives stand alone: the rip hunt box hides the shelf */
  document.querySelectorAll('.fbook').forEach(function(b){
    b.classList.toggle('hidden',filtering);
  });
  document.querySelectorAll('.genre').forEach(function(g){
    if(g.classList.contains('fbshelf')){
      g.classList.toggle('hidden',filtering||!document.querySelector('.fbook:not(.hidden)'));
      return;
    }
    var show=false,next=g.nextElementSibling;
    while(next&&!next.classList.contains('genre')){
      if(next.classList.contains('book')&&!next.classList.contains('hidden')){show=true;break;}
      next=next.nextElementSibling;
    }
    g.classList.toggle('hidden',!show);
  });
  document.querySelectorAll('#jumpchips a').forEach(function(ch){
    ch.classList.toggle('hidden',!!gv&&ch.dataset.genre!==gv);
  });
  var vis=document.querySelectorAll('.card:not([data-fb]):not(.hidden)').length;
  count.textContent='showing '+vis+' of '+total+(searchMode==='any'&&vis?' (any word)':'');
  nores.hidden=vis>0;
  if(!nores.hidden){
    var msg='No rips match',tm=q.value.trim(),tn=checkedTypes();
    if(tm)msg+=' &ldquo;'+jesc(tm)+'&rdquo;';
    if(tn.length)msg+=(tm?' with':'')+' type &ldquo;'+tn.map(jesc).join(', ')+'&rdquo;';
    if(!tm&&!tn.length&&(gv||bv))msg+=' the current filters';
    msg+='.';
    if(tm)msg+=' Try fewer or shorter words, or one of: '+['negotiation','hiring','delay','stuck','habit'].map(function(w){return '<button type="button" class="trysearch" data-try="'+w+'">'+w+'</button>';}).join(' ');
    msg+=' <button type="button" id="clearall">Clear search and filters</button>';
    nores.innerHTML=msg;
    nores.querySelectorAll('.trysearch').forEach(function(b){b.addEventListener('click',function(){
      q.value=b.getAttribute('data-try');gs.value='';bs.value='';
      for(var i=0;i<tboxes.length;i++)tboxes[i].checked=false;
      apply(true);announceLive();q.focus();});});
    var ca=document.getElementById('clearall');
    if(ca)ca.addEventListener('click',function(){
      q.value='';gs.value='';bs.value='';
      for(var i=0;i<tboxes.length;i++)tboxes[i].checked=false;
      apply(true);q.focus();
    });
  }
  updateTypeUI();
  syncURL();
  scheduleHighlight(term);
}
function clearMarks(root){
  var marks=root.querySelectorAll('mark'),i,m,p;
  for(i=0;i<marks.length;i++){
    m=marks[i];p=m.parentNode;
    while(m.firstChild)p.insertBefore(m.firstChild,m);
    p.removeChild(m);
    p.normalize();
  }
}
function markTerm(el,re){
  var walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,null,false),nodes=[],nd,i,t,v,m,st,en,last,frag,mk;
  while(nd=walker.nextNode()){
    if(nd.parentNode&&nd.parentNode.className==='k')continue;
    nodes.push(nd);
  }
  for(i=0;i<nodes.length;i++){
    t=nodes[i];v=t.nodeValue;re.lastIndex=0;frag=null;last=0;
    while((m=re.exec(v))){
      st=m.index+m[1].length;en=st+m[2].length;
      if(en===st){re.lastIndex++;continue;}
      if(!frag)frag=document.createDocumentFragment();
      if(st>last)frag.appendChild(document.createTextNode(v.slice(last,st)));
      mk=document.createElement('mark');mk.textContent=v.slice(st,en);frag.appendChild(mk);
      last=en;
    }
    if(!frag)continue;
    frag.appendChild(document.createTextNode(v.slice(last)));
    t.parentNode.replaceChild(frag,t);
  }
}
var hlT=null;
function scheduleHighlight(term){
  clearTimeout(hlT);
  hlT=setTimeout(function(){
    document.querySelectorAll('.card:not([data-fb])').forEach(function(c){clearMarks(c);});
    var st=term?qStems(term):[];
    if(st.length){
      var re=new RegExp('(^|[^\\p{L}\\p{N}])('+st.map(reEsc).join('|')+')','giu');
      document.querySelectorAll('.card:not([data-fb]):not(.hidden)').forEach(function(c){
        ['.ctitle','.steal','.why','.uw'].forEach(function(sel){
          var el=c.querySelector(sel);if(el)markTerm(el,re);
        });
      });
    }
  },term?150:0);
}
var liveT=null;
function announceLive(){
  var el=document.getElementById('countlive');
  if(el)el.textContent=count.textContent;
}
function scheduleLive(){clearTimeout(liveT);liveT=setTimeout(announceLive,400);}
q.addEventListener('input',function(){apply(true);scheduleLive();});
q.addEventListener('change',function(){apply(false);});
[gs,bs].forEach(function(el){
  el.addEventListener('input',function(){apply(true);announceLive();});
  el.addEventListener('change',function(){apply(false);announceLive();});
});
for(var ti=0;ti<tboxes.length;ti++){
  tboxes[ti].addEventListener('change',function(){apply(true);announceLive();});
}
document.getElementById('cleartypes').addEventListener('click',function(){
  for(var i=0;i<tboxes.length;i++)tboxes[i].checked=false;
  apply(true);announceLive();
});
q.addEventListener('keydown',function(e){
  if(e.key==='Escape'){q.value='';apply(true);}
});
function toggleCard(card,open){
  var will=open===undefined?!card.classList.contains('open'):open;
  card.classList.toggle('open',will);
  var chd=card.querySelector('.cardhead');
  if(chd)chd.setAttribute('aria-expanded',will?'true':'false');
  if(will&&card.dataset.n)setHash('#c'+card.dataset.n);
}
/* delegated (2026-09-30): card heads, Copy and Save buttons are handled at the
   document, so buttons cloned into cards later work without re-binding */
document.addEventListener('click',function(e){
  var h=e.target&&e.target.closest?e.target.closest('.cardhead'):null;
  if(h)toggleCard(h.closest('.card'));
});
document.querySelectorAll('.bookhead').forEach(function(h){
  function t(){var b=h.closest('section'),exp=b.classList.contains('collapsed');setBook(b,exp);if(exp)accordionize(b);}
  h.addEventListener('click',t);
});
function syncXall(b){
  var x=b.querySelector('.xall');if(!x)return;
  var cards=b.querySelectorAll('.card:not(.hidden)'),anyClosed=false,i;
  for(i=0;i<cards.length;i++)if(!cards[i].classList.contains('open')){anyClosed=true;break;}
  x.setAttribute('aria-expanded',anyClosed?'false':'true');
  x.textContent=anyClosed?'Expand all':'Collapse all';
}
document.querySelectorAll('.xall').forEach(function(x){
  x.addEventListener('click',function(e){
    e.stopPropagation();
    var b=x.closest('section.book');if(!b)return;
    if(b.classList.contains('collapsed')){setBook(b,true);accordionize(b);}
    var cards=b.querySelectorAll('.card:not(.hidden)'),anyClosed=false,i;
    for(i=0;i<cards.length;i++)if(!cards[i].classList.contains('open')){anyClosed=true;break;}
    for(i=0;i<cards.length;i++){
      cards[i].classList.toggle('open',anyClosed);
      var h=cards[i].querySelector('.cardhead');
      if(h)h.setAttribute('aria-expanded',anyClosed?'true':'false');
    }
    syncXall(b);
  });
});
/* full-book shelf: own toggle, outside rip expand/collapse-all */
document.querySelectorAll('.fbookhead').forEach(function(h){
  function t(){var b=h.closest('section'),exp=b.classList.contains('collapsed');
    b.classList.toggle('collapsed',!exp);
    h.setAttribute('aria-expanded',exp?'true':'false');}
  h.addEventListener('click',t);
});
document.getElementById('expand').addEventListener('click',function(){
  document.querySelectorAll('.book:not(.hidden)').forEach(function(b){
    setBook(b,true);
    b.querySelectorAll('.card:not(.hidden)').forEach(function(c){c.classList.add('open');});
  });
});
document.getElementById('collapse').addEventListener('click',function(){
  document.querySelectorAll('.book').forEach(function(b){
    setBook(b,false);
    b.querySelectorAll('.card.open').forEach(function(c){c.classList.remove('open');});
  });
});
document.addEventListener('click',function(e){
    var btn=e.target&&e.target.closest?e.target.closest('[data-copy]'):null;if(!btn)return;
    var card=btn.closest('.card'),kind=btn.dataset.copy,txt;if(!card)return;
    if(kind==='steal')txt=card.querySelector('.steal').textContent;
    else if(kind==='uw')txt=card.querySelector('.uw').textContent;
    else txt=location.origin+location.pathname+'#c'+card.dataset.n;
    function done(ok){
      if(ok){toast(kind==='link'?'Link copied':'Copied');return;}
      try{var rng=document.createRange();rng.selectNodeContents(card);
        var sel=getSelection();sel.removeAllRanges();sel.addRange(rng);}catch(_){}
      toast('Copy failed \u2014 press Ctrl+C (Cmd+C on Mac) to copy the selected text',4000);
    }
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(function(){done(true);},function(){done(false);});}
    else{var ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');done(true);}catch(_){done(false);}document.body.removeChild(ta);}
});
document.querySelectorAll('#jumpchips a').forEach(function(ch){
  ch.addEventListener('click',function(e){
    var b=document.getElementById(ch.getAttribute('href').slice(1));
    if(b){e.preventDefault();if(b.classList.contains('book')){setBook(b,true);accordionize(b);}
      b.scrollIntoView({behavior:RM?'auto':'smooth',block:'start'});
      setHash(ch.getAttribute('href'));}
  });
});
/* phase 2: browse-all-books expander */
(function(){
  var bb=document.getElementById('bookbrowser');if(!bb)return;
  var bf=bb.querySelector('.blist-filter');
  bf.addEventListener('input',function(){
    var t=bf.value.toLowerCase();
    bb.querySelectorAll('.blist-item').forEach(function(a){
      a.classList.toggle('hidden',!!t&&a.textContent.toLowerCase().indexOf(t)<0);
    });
  });
  bb.querySelectorAll('.blist-item').forEach(function(a){
    a.addEventListener('click',function(e){
      e.preventDefault();
      bs.value=a.getAttribute('data-book');apply(true);announceLive();
      var sec=document.getElementById(a.getAttribute('href').slice(1));
      if(sec){setBook(sec,true);accordionize(sec);sec.scrollIntoView({behavior:RM?'auto':'smooth',block:'start'});setHash(a.getAttribute('href'));}
      bb.open=false;bf.value='';bf.dispatchEvent(new Event('input'));
    });
  });
})();
function openHash(){
  var m=/^#c(\d+)$/.exec(location.hash),c;
  if(m&&(c=document.getElementById('c'+m[1]))){
    var b=c.closest('.book');setBook(b,true);accordionize(b);c.classList.add('open');c.classList.add('deeplink');
    var oh=c.querySelector('.cardhead');
    if(oh){oh.setAttribute('aria-expanded','true');try{oh.focus({preventScroll:true});}catch(_){}}
    scrollTarget(c,'center');return true;
  }
  m=/^#b-([a-z0-9-]+)$/.exec(location.hash);
  if(m){var bk=document.getElementById('b-'+m[1]);
    if(bk){setBook(bk,true);accordionize(bk);scrollTarget(bk,'start');return true;}}
  m=/^#g-([a-z0-9-]+)$/.exec(location.hash);
  if(m){var gn=document.getElementById('g-'+m[1]);
    if(gn){scrollTarget(gn,'start');return true;}}
  return false;
}
/* deep links (2026-09-30): open the target right away, but scroll exactly once,
   after the load event, with no smooth scrolling and no setInterval re-scrolls
   (those fought layout and made shared links jump: CLS 1.0 on mobile). The
   sticky controls' real height feeds scroll-margin-top so the target isn't
   hidden under them. */
var _dlTakeover=false,_initialScroll=true,_pendingScroll=null;
["touchstart","wheel","keydown"].forEach(function(ev){window.addEventListener(ev,function(){_dlTakeover=true;},{once:true,passive:true});});
function syncScrollMargin(){
  var ctl=document.querySelector('.controls');if(!ctl)return;
  var px=Math.ceil(ctl.getBoundingClientRect().height)+8+'px',st=document.documentElement.style;
  st.setProperty('--scroll-mt',px);st.setProperty('--scroll-mt-mobile',px);
}
syncScrollMargin();
window.addEventListener('resize',syncScrollMargin,{passive:true});
function scrollTarget(el,block){
  if(_initialScroll){_pendingScroll=[el,block];return;}
  setTimeout(function(){el.scrollIntoView({behavior:RM?'auto':'smooth',block:block});},60);
}
function flushInitialScroll(){
  _initialScroll=false;
  var p=_pendingScroll;_pendingScroll=null;
  if(!p||_dlTakeover)return;
  syncScrollMargin();
  p[0].scrollIntoView({behavior:'auto',block:p[1]});
}
if(document.readyState==='complete')setTimeout(flushInitialScroll,0);
else window.addEventListener('load',flushInitialScroll,{once:true});
openHash();
(function restoreURL(){
  var p,qq,tt,gg,bb,want,i;
  try{p=new URLSearchParams(location.search);}catch(_){return;}
  qq=p.get('q');if(qq)q.value=qq;
  tt=p.get('type');
  if(tt){want={};tt.split(',').forEach(function(t){want[t]=1;});
    for(i=0;i<tboxes.length;i++)tboxes[i].checked=!!want[tboxes[i].value];}
  gg=p.get('g');if(gg)gs.value=gg;
  bb=p.get('b');if(bb)bs.value=bb;
  if(tt){var d=document.getElementById('typefilter');if(d)d.open=true;}
})();
var restoredQ=q.value.trim()!=='';
apply(restoredQ);
openHash();
/* 2026-10-02: chips are plain hash anchors; without this, tapping one on an
   already-loaded page jumps but never expands the collapsed book. */
window.addEventListener('hashchange',function(){openHash();});
/* rotw weekly timer (2026-10-02): rotate the Rip of the week every 7 days.
   Pool comes from #rotw-pool JSON; START is the week-index of the deploy week,
   so pool[0] shows first. No rebuild needed. */
(function(){
  var pel=document.getElementById('rotw-pool'),card=document.getElementById('rotw-card');
  if(!pel||!card)return;
  var pool;try{pool=JSON.parse(pel.textContent);}catch(_){return;}
  if(!pool||!pool.length)return;
  var START=parseInt(pel.getAttribute('data-start'),10)||0;
  var wi=Math.floor(Date.now()/604800000);
  var k=((wi-START)%pool.length+pool.length)%pool.length;
  var p=pool[k];
  var fk='<p class="fkicker"><span class="ktext">Rip of the week</span></p>';
  var kr='<div class="kicker"><span class="ktext">Ripped from</span></div>';
  var ku='<div class="kicker"><span class="ktext">Use when</span></div>';
  var s=new Date((START+k)*604800000),e=new Date((START+k)*604800000+6*864e5);
  var mo={month:'short',day:'numeric'};
  var label=s.toLocaleDateString('en-US',mo)+' \u2013 '+e.toLocaleDateString('en-US',mo)+', '+e.getFullYear();
  var meta=label+(p.note?' &mdash; '+p.note:'');
  card.innerHTML=fk+'<h3 class="ftitle">'+p.title+'</h3>'
    +'<p class="fbook">'+p.book+' &middot; <span class="pill '+p.type+'">'+p.type+'</span></p>'
    +kr+'<p class="steal">'+p.steal+'</p>'
    +'<p class="why"><span class="k">Why it matters:</span> '+p.why+'</p>'
    +ku+'<p class="uw">'+p.uw+'</p>'
    +'<p class="rotw-meta">'+meta+'</p>'
    +'<p class="fmore"><a href="#c'+p.id+'">Find it on the shelf \u2193</a></p>';
})();
updateCrumbs();
/* phase 5: saved rips (localStorage), export, random rip, related/saved link opens */
var SVKEY='idearipper.saved.v1';
function getSaved(){try{var v=JSON.parse(localStorage.getItem(SVKEY)||'[]');if(!Array.isArray(v))return[];var out=[],seen={},i,id;for(i=0;i<v.length;i++){id=+v[i];if(id&&!seen[id]){seen[id]=1;out.push(id);}}return out;}catch(_){return[];}}
function setSaved(a){try{localStorage.setItem(SVKEY,JSON.stringify(a));}catch(_){}}
function mainCard(id){return document.querySelector('.card:not([data-fb])#c'+id);}
function cleanTitle(t){return t.replace(/^\d+\s*/,'').trim();}
function stripPrefix(t,lab){return t.indexOf(lab)===0?t.slice(lab.length).trim():t;}
function bookAuthor(bk){var p=(bk||'').split(' \u2014 ');if(p.length<2)return{b:bk,a:''};var a=p.pop();return{b:p.join(' \u2014 '),a:a};}
function openRip(id){
  var c=mainCard(id);if(!c)return false;
  var b=c.closest('.book');if(b&&b.classList.contains('collapsed')){setBook(b,true);accordionize(b);}
  c.classList.add('open');var h=c.querySelector('.cardhead');if(h)h.setAttribute('aria-expanded','true');
  if(b)syncXall(b);
  setTimeout(function(){c.scrollIntoView({behavior:RM?'auto':'smooth',block:'center'});},60);
  if(c.dataset.n)setHash('#c'+c.dataset.n);
  return true;
}
function renderSaved(){
  var s=getSaved(),list=document.getElementById('savedlist'),note=document.getElementById('savenote'),i,id,c,t,bk;
  if(!list)return;
  list.innerHTML='';
  if(note)note.hidden=s.length>0;
  for(i=0;i<s.length;i++){id=s[i];c=mainCard(id);if(!c)continue;
    t=c.querySelector('.ctitle');bk=c.getAttribute('data-book')||'';
    var d=document.createElement('div');d.className='sitem';
    var a=document.createElement('a');a.href='#c'+id;a.textContent=cleanTitle(t?t.textContent:('Rip #'+id));
    var m=document.createElement('span');m.className='smeta';m.textContent=bk+' \u00b7 '+(c.getAttribute('data-type')||'');
    d.appendChild(a);d.appendChild(m);list.appendChild(d);}
  var ex=document.getElementById('exportSaved');if(ex)ex.disabled=!s.length;
  var sc=document.getElementById('savedcount');if(sc)sc.textContent=s.length;
  var chip=document.getElementById('savedchip');if(chip)chip.textContent='\u2605 Saved ('+s.length+')';
}
function syncSaveButtons(){
  var s=getSaved(),has={},i;for(i=0;i<s.length;i++)has[s[i]]=1;
  document.querySelectorAll('[data-save]').forEach(function(b){
    var on=!!has[+b.getAttribute('data-save')];
    b.setAttribute('aria-pressed',on?'true':'false');
    b.textContent=on?'Saved \u2713':'Save';
  });
}
document.addEventListener('click',function(e){
    var b=e.target&&e.target.closest?e.target.closest('[data-save]'):null;if(!b)return;
    var id=+b.getAttribute('data-save'),s=getSaved(),i=s.indexOf(id);
    /* persist first, then update UI, then toast: a toast problem can never lose a save */
    var was=i>=0;if(was)s.splice(i,1);else s.push(id);
    setSaved(s);syncSaveButtons();renderSaved();
    toast(was?'Removed from saved':'Saved');
});
document.querySelectorAll('.rel a').forEach(function(a){
  a.addEventListener('click',function(e){e.preventDefault();openRip(+a.getAttribute('href').slice(2));});
});
/* "Find it on the shelf" links (featured shelves + collide clones): open the
   canonical shelf card instead of a bare hash jump. Delegated so dynamically
   added collide clones are covered too. */
document.addEventListener('click',function(e){
  var a=e.target&&e.target.closest?e.target.closest('.fcard .fmore a[href^="#c"]'):null;
  if(!a)return;e.preventDefault();openRip(+a.getAttribute('href').slice(2));
});
var _slist=document.getElementById('savedlist');
if(_slist)_slist.addEventListener('click',function(e){
  var a=e.target.closest('a');if(!a)return;e.preventDefault();openRip(+a.getAttribute('href').slice(2));
});
var _ex=document.getElementById('exportSaved');
if(_ex)_ex.addEventListener('click',function(){
  var s=getSaved();if(!s.length)return;
  var out=['# Saved rips \u2014 Idea Ripper',''],i,id,c,t,st,wh,uw,ba;
  for(i=0;i<s.length;i++){id=s[i];c=mainCard(id);if(!c)continue;
    t=c.querySelector('.ctitle');st=c.querySelector('.steal');wh=c.querySelector('.why');uw=c.querySelector('.uw');
    ba=bookAuthor(c.getAttribute('data-book'));
    out.push('## '+cleanTitle(t?t.textContent:('Rip #'+id)));
    out.push('_'+ba.b+(ba.a?' \u2014 '+ba.a:'')+'_ \u00b7 #c'+id);
    out.push('');
    if(st){out.push('**Steal:** '+st.textContent.trim());out.push('');}
    if(wh){out.push('**Why it matters:** '+stripPrefix(wh.textContent.trim(),'Why it matters:'));out.push('');}
    if(uw){out.push('**Use when:** '+stripPrefix(uw.textContent.trim(),'Use when:'));out.push('');}
    out.push('---');out.push('');}
  var blob=new Blob([out.join('\n')],{type:'text/markdown'});
  var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='idea-ripper-saved.md';
  document.body.appendChild(a);a.click();
  setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},800);
  toast('Exported '+s.length+' saved rips');
});
var _cs=document.getElementById('clearSaved');
if(_cs)_cs.addEventListener('click',function(){setSaved([]);syncSaveButtons();renderSaved();toast('Saved rips cleared');});
var _rr=document.getElementById('randomrip');
if(_rr)_rr.addEventListener('click',function(){
  var pool=[],i,cs=document.querySelectorAll('.card:not([data-fb]):not(.hidden)');
  for(i=0;i<cs.length;i++)pool.push(cs[i]);
  if(!pool.length){toast('No rips visible \u2014 clear search first');return;}
  openRip(+pool[Math.floor(Math.random()*pool.length)].dataset.n);
});
/* collide (phase 1, 2026-09-27): two rips from different worlds, side by
   side. Deliberately no machine-written synthesis: the collision is the
   product, the user's brain writes the synthesis. */
var _cb=document.getElementById('colliderip'),_csec=document.getElementById('collide'),
    _cpair=document.getElementById('collidepair'),_cagain=document.getElementById('collideagain'),
    _lastPair='';
function collideKicker(label){
  var p=document.createElement('p');p.className='fkicker';
  var s=document.createElement('span');s.className='ktext';s.textContent=label;
  p.appendChild(s);return p;
}
function collideCard(c){
  function tx(sel){var el=c.querySelector(sel);return el?el.textContent.trim():'';}
  var art=document.createElement('article');art.className='fcard';
  art.appendChild(collideKicker('Collision rip'));
  var h=document.createElement('h3');h.className='ftitle';h.textContent=tx('.ctitle');art.appendChild(h);
  var fb=document.createElement('p');fb.className='fbook';
  fb.textContent=(c.getAttribute('data-book')||'')+' \u00b7 ';
  var pill=document.createElement('span');pill.className='pill '+(c.getAttribute('data-type')||'');
  pill.textContent=c.getAttribute('data-type')||'';fb.appendChild(pill);art.appendChild(fb);
  art.appendChild(collideKicker('Ripped from'));
  var st=document.createElement('p');st.className='steal';st.textContent=tx('.steal');art.appendChild(st);
  var wy=document.createElement('p');wy.className='why';
  var k=document.createElement('span');k.className='k';k.textContent='Why it matters:';
  wy.appendChild(k);
  wy.appendChild(document.createTextNode(' '+tx('.why').replace(/^Why it matters:\s*/i,'')));
  art.appendChild(wy);
  art.appendChild(collideKicker('Use when'));
  var u=document.createElement('p');u.className='uw';
  u.textContent=tx('.uw').replace(/^Use when:\s*/i,'');art.appendChild(u);
  var fm=document.createElement('p');fm.className='fmore';
  var a=document.createElement('a');a.href='#c'+c.dataset.n;a.textContent='Find it on the shelf \u2193';
  fm.appendChild(a);art.appendChild(fm);
  return art;
}
function pickTwo(){
  var pool=[],i,cs=document.querySelectorAll('.card:not([data-fb])');
  for(i=0;i<cs.length;i++)pool.push(cs[i]);
  if(pool.length<2)return null;
  var a=null,b=null,tries,cand,key,rkey,att;
  for(att=0;att<3;att++){
    a=pool[(Math.random()*pool.length)|0];b=null;tries=0;
    while(tries<60){
      cand=pool[(Math.random()*pool.length)|0];tries++;
      if(cand===a||cand.getAttribute('data-book')===a.getAttribute('data-book'))continue;
      if(cand.getAttribute('data-genre')!==a.getAttribute('data-genre')||tries>20){b=cand;break;}
    }
    if(!b)continue;
    key=a.dataset.n+'|'+b.dataset.n;rkey=b.dataset.n+'|'+a.dataset.n;
    if(key!==_lastPair&&rkey!==_lastPair){_lastPair=key;return[a,b];}
  }
  return b?[a,b]:null;
}
function doCollide(){
  var pair=pickTwo();
  if(!pair){toast('Not enough rips to collide');return;}
  _cpair.innerHTML='';
  _cpair.appendChild(collideCard(pair[0]));
  _cpair.appendChild(collideCard(pair[1]));
  _csec.hidden=false;
  setTimeout(function(){_csec.scrollIntoView({behavior:RM?'auto':'smooth',block:'start'});},60);
}
if(_cb)_cb.addEventListener('click',doCollide);
if(_cagain)_cagain.addEventListener('click',doCollide);
/* card actions (2026-09-30): one <template id="cardactions">, cloned into a
   library card the first time it is open (any code path: click, expand all,
   search, deep link, random) */
var ACT=document.getElementById('cardactions');
function ensureActions(c){
  if(!ACT||c.hasAttribute('data-fb')||!c.classList.contains('open'))return;
  var body=c.querySelector('.cardbody');if(!body||body.querySelector('.actions'))return;
  var frag=ACT.content.cloneNode(true),sb=frag.querySelector('[data-save]'),id=+c.dataset.n,on=getSaved().indexOf(id)>=0;
  sb.setAttribute('data-save',id);sb.setAttribute('aria-pressed',on?'true':'false');sb.textContent=on?'Saved \u2713':'Save';
  body.appendChild(frag);
}
var _main=document.querySelector('main');
if(_main&&window.MutationObserver)new MutationObserver(function(ms){
  for(var i=0;i<ms.length;i++){var t=ms[i].target;if(t.classList&&t.classList.contains('card')&&t.classList.contains('open'))ensureActions(t);}
}).observe(_main,{subtree:true,attributes:true,attributeFilter:['class']});
document.querySelectorAll('main .card.open').forEach(ensureActions);
syncSaveButtons();renderSaved();
})();

