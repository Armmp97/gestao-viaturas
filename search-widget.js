/* ============================================================
   DomusCar Intranet · Search Widget
   - Lê window.SEARCH_INDEX (carregado por search-index.js)
   - Pesquisa em título, secção, headings e conteúdo
   - Filtra resultados pelas permissões do utilizador
   - Dropdown de sugestões em tempo real, navegável por teclado
   - Clicar (ou Enter) chama openModule(id) já existente na intranet
   ============================================================ */
(function () {
  'use strict';

  // -------- estilos -------------------------------------------------
  var css = ''
    + '.dc-search-wrap{position:relative;flex:1;max-width:520px;margin:0 24px;}'
    + '.dc-search-box{display:flex;align-items:center;gap:8px;background:#f0f2f5;border:1px solid transparent;border-radius:8px;padding:7px 12px;transition:all .15s;}'
    + '.dc-search-box:focus-within{background:#fff;border-color:#1a73e8;box-shadow:0 0 0 3px rgba(26,115,232,.12);}'
    + '.dc-search-box svg{width:16px;height:16px;color:#5f6368;flex-shrink:0;}'
    + '.dc-search-input{flex:1;border:none;background:transparent;outline:none;font-family:inherit;font-size:13.5px;color:#1a1a2e;min-width:0;}'
    + '.dc-search-input::placeholder{color:#9aa0a6;}'
    + '.dc-search-kbd{font-size:11px;color:#9aa0a6;background:#fff;border:1px solid #e0e3e8;border-radius:4px;padding:1px 6px;font-family:inherit;}'
    + '.dc-search-results{position:absolute;top:calc(100% + 6px);left:0;right:0;background:#fff;border:1px solid #e0e3e8;border-radius:10px;box-shadow:0 8px 28px rgba(10,22,40,.16);max-height:480px;overflow-y:auto;display:none;z-index:200;}'
    + '.dc-search-results.show{display:block;}'
    + '.dc-search-section-label{font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#9aa0a6;padding:10px 14px 4px;}'
    + '.dc-search-item{display:flex;align-items:flex-start;gap:10px;padding:9px 14px;cursor:pointer;border-left:3px solid transparent;}'
    + '.dc-search-item:hover,.dc-search-item.active{background:#e8f0fe;border-left-color:#1a73e8;}'
    + '.dc-search-icon{font-size:18px;line-height:1;margin-top:2px;flex-shrink:0;}'
    + '.dc-search-meta{flex:1;min-width:0;}'
    + '.dc-search-title{font-size:13.5px;font-weight:600;color:#1a1a2e;margin:0 0 2px;}'
    + '.dc-search-sub{font-size:11.5px;color:#5f6368;}'
    + '.dc-search-snippet{font-size:12px;color:#5f6368;margin-top:3px;line-height:1.45;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}'
    + '.dc-search-snippet mark,.dc-search-title mark{background:#fff3a3;color:inherit;padding:0 2px;border-radius:2px;}'
    + '.dc-search-empty{padding:18px 14px;font-size:13px;color:#5f6368;text-align:center;}'
    + '.dc-search-footer{border-top:1px solid #eef0f3;padding:8px 14px;font-size:11.5px;color:#9aa0a6;display:flex;justify-content:space-between;gap:8px;}'
    + '.dc-search-footer span{display:inline-flex;align-items:center;gap:4px;}'
    + '@media (max-width:768px){.dc-search-wrap{margin:0 8px;}.dc-search-kbd{display:none;}}'
    + '@media (max-width:520px){.dc-search-wrap{display:none;}}'
  ;

  // -------- helpers -------------------------------------------------
  function normalize(s){
    return (s||'').toString().toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, ''); // strip combining diacritics
  }

  function escapeHtml(s){
    return String(s||'').replace(/[&<>"']/g, function(c){
      return ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' })[c];
    });
  }

  // Variantes singular/plural simples PT — tolera "picagem"↔"picagens", "margem"↔"margens", "sugestão"↔"sugestões" (após deaccent), "horas"↔"hora", etc.
  function termVariants(t){
    var v = [t];
    if(t.length >= 4){
      v.push(t.slice(0, -1));
      if(t.length >= 5) v.push(t.slice(0, -2));
    }
    if(/m$/.test(t))  v.push(t.replace(/m$/, 'ns'));
    if(/ao$/.test(t)) v.push(t.replace(/ao$/, 'oes'));
    if(!/s$/.test(t)) v.push(t + 's');
    if(t.length >= 3 && !/s$/.test(t)) v.push(t + 'es');
    var seen = {}, out = [];
    v.forEach(function(x){ if(x && !seen[x]){ seen[x]=1; out.push(x); }});
    return out;
  }

  function matchTerm(haystack, term){
    var vars = termVariants(term);
    for(var i=0;i<vars.length;i++) if(haystack.indexOf(vars[i]) !== -1) return true;
    return false;
  }

  function highlight(text, terms){
    var safe = escapeHtml(text);
    if(!terms || !terms.length) return safe;
    var nText = normalize(text);
    var allTerms = [];
    terms.forEach(function(t){
      if(!t) return;
      var nt = normalize(t);
      if(!nt) return;
      termVariants(nt).forEach(function(v){ if(allTerms.indexOf(v) === -1) allTerms.push(v); });
    });
    var ranges = [];
    allTerms.forEach(function(nt){
      var idx = 0;
      while(true){
        var pos = nText.indexOf(nt, idx);
        if(pos === -1) break;
        ranges.push([pos, pos+nt.length]);
        idx = pos + nt.length;
      }
    });
    if(!ranges.length) return safe;
    ranges.sort(function(a,b){return a[0]-b[0];});
    var merged = [ranges[0]];
    for(var i=1;i<ranges.length;i++){
      var last = merged[merged.length-1];
      if(ranges[i][0] <= last[1]) last[1] = Math.max(last[1], ranges[i][1]);
      else merged.push(ranges[i]);
    }
    var out = '';
    var p = 0;
    merged.forEach(function(r){
      out += escapeHtml(text.slice(p, r[0])) + '<mark>' + escapeHtml(text.slice(r[0], r[1])) + '</mark>';
      p = r[1];
    });
    out += escapeHtml(text.slice(p));
    return out;
  }

  function snippetAround(text, terms, max){
    max = max || 160;
    if(!text) return '';
    var nText = normalize(text);
    var firstPos = -1;
    for(var i=0;i<terms.length;i++){
      var vars = termVariants(normalize(terms[i]));
      for(var j=0;j<vars.length;j++){
        var p = nText.indexOf(vars[j]);
        if(p !== -1 && (firstPos === -1 || p < firstPos)) firstPos = p;
      }
    }
    if(firstPos === -1) return text.slice(0, max) + (text.length > max ? '…' : '');
    var start = Math.max(0, firstPos - 50);
    var end = Math.min(text.length, start + max);
    return (start > 0 ? '…' : '') + text.slice(start, end) + (end < text.length ? '…' : '');
  }

  // -------- pesquisa ------------------------------------------------
  function search(query){
    var index = window.SEARCH_INDEX || [];
    if(!index.length) return [];
    var terms = normalize(query).split(/\s+/).filter(function(t){return t.length >= 2;});
    if(!terms.length) return [];

    var perm = window.currentUserPermissions;
    var allowed = perm && Array.isArray(perm.modules) ? perm.modules : null;

    var hits = [];
    index.forEach(function(item){
      if(allowed && allowed.indexOf(item.id) === -1) return;
      var nTitle = normalize(item.title);
      var nSection = normalize(item.section);
      var nHeadings = normalize((item.headings||[]).join(' | '));
      var nContent = normalize(item.content||'');
      var score = 0;
      var allMatched = true;
      terms.forEach(function(t){
        var inT = matchTerm(nTitle, t);
        var inS = matchTerm(nSection, t);
        var inH = matchTerm(nHeadings, t);
        var inC = matchTerm(nContent, t);
        if(!(inT || inS || inH || inC)) allMatched = false;
        if(inT) score += 50;
        if(nTitle.split(/\s+/).indexOf(t) !== -1) score += 30;
        if(inS) score += 8;
        if(inH) score += 15;
        if(inC) score += 3;
      });
      if(!allMatched) return;
      if(nTitle.indexOf(terms.join(' ')) !== -1) score += 25;
      hits.push({ item: item, score: score });
    });
    hits.sort(function(a,b){return b.score - a.score;});
    return hits.slice(0, 12);
  }

  // -------- UI ------------------------------------------------------
  function injectStyles(){
    if(document.querySelector('style[data-dc-search]')) return;
    var s = document.createElement('style');
    s.setAttribute('data-dc-search','1');
    s.textContent = css;
    document.head.appendChild(s);
  }

  function buildWidget(){
    var wrap = document.createElement('div');
    wrap.className = 'dc-search-wrap';
    wrap.setAttribute('role','search');
    wrap.innerHTML = ''
      + '<div class="dc-search-box">'
      +   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
      +   '<input class="dc-search-input" type="search" autocomplete="off" spellcheck="false" placeholder="Pesquisar na intranet…" aria-label="Pesquisar" />'
      +   '<span class="dc-search-kbd" id="dcSearchKbd">Ctrl K</span>'
      + '</div>'
      + '<div class="dc-search-results" role="listbox"></div>';
    return wrap;
  }

  function mountWidget(){
    var header = document.querySelector('header.app-header');
    if(!header) return false;
    if(header.querySelector('.dc-search-wrap')) return true;

    var widget = buildWidget();
    var right = header.querySelector('.header-right');
    if(right) header.insertBefore(widget, right);
    else header.appendChild(widget);

    var input = widget.querySelector('.dc-search-input');
    var results = widget.querySelector('.dc-search-results');
    var activeIdx = -1;
    var lastHits = [];

    function setActive(idx){
      var nodes = results.querySelectorAll('.dc-search-item');
      nodes.forEach(function(n,i){ n.classList.toggle('active', i===idx); });
      activeIdx = idx;
      if(idx >= 0 && nodes[idx]) nodes[idx].scrollIntoView({ block:'nearest' });
    }

    function open(){ results.classList.add('show'); }
    function close(){ results.classList.remove('show'); activeIdx = -1; }

    function pick(idx){
      var hit = lastHits[idx];
      if(!hit) return;
      if(typeof window.openModule === 'function'){
        window.openModule(hit.item.id);
      }
      input.value = '';
      close();
      input.blur();
    }

    function render(query){
      var hits = search(query);
      lastHits = hits;
      if(!query || query.trim().length < 2){
        close();
        results.innerHTML = '';
        return;
      }
      if(!hits.length){
        results.innerHTML = '<div class="dc-search-empty">Sem resultados para <b>' + escapeHtml(query) + '</b></div>';
        open();
        return;
      }
      var terms = normalize(query).split(/\s+/).filter(function(t){return t.length>=2;});
      var html = '<div class="dc-search-section-label">' + hits.length + ' resultado' + (hits.length>1?'s':'') + '</div>';
      hits.forEach(function(h, i){
        var it = h.item;
        var snippet = snippetAround(it.content||'', terms, 160);
        html += ''
          + '<div class="dc-search-item" data-idx="' + i + '" role="option">'
          +   '<div class="dc-search-icon">' + escapeHtml(it.icon||'📄') + '</div>'
          +   '<div class="dc-search-meta">'
          +     '<div class="dc-search-title">' + highlight(it.title, terms) + '</div>'
          +     '<div class="dc-search-sub">' + escapeHtml(it.section||'') + '</div>'
          +     (snippet ? '<div class="dc-search-snippet">' + highlight(snippet, terms) + '</div>' : '')
          +   '</div>'
          + '</div>';
      });
      html += '<div class="dc-search-footer"><span><b>↑↓</b> navegar</span><span><b>Enter</b> abrir</span><span><b>Esc</b> fechar</span></div>';
      results.innerHTML = html;
      open();
      activeIdx = 0;
      setActive(0);
    }

    var t = null;
    input.addEventListener('input', function(){
      clearTimeout(t);
      var q = input.value;
      t = setTimeout(function(){ render(q); }, 110);
    });

    input.addEventListener('focus', function(){
      if(input.value.trim().length >= 2) render(input.value);
    });

    input.addEventListener('keydown', function(e){
      if(e.key === 'ArrowDown'){ e.preventDefault(); if(lastHits.length) setActive(Math.min(activeIdx+1, lastHits.length-1)); }
      else if(e.key === 'ArrowUp'){ e.preventDefault(); if(lastHits.length) setActive(Math.max(activeIdx-1, 0)); }
      else if(e.key === 'Enter'){ e.preventDefault(); if(activeIdx >=0) pick(activeIdx); }
      else if(e.key === 'Escape'){ input.value=''; close(); input.blur(); }
    });

    results.addEventListener('click', function(e){
      var item = e.target.closest('.dc-search-item');
      if(!item) return;
      pick(parseInt(item.getAttribute('data-idx'), 10));
    });

    document.addEventListener('click', function(e){
      if(!widget.contains(e.target)) close();
    });

    document.addEventListener('keydown', function(e){
      var isCmdK = (e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K');
      if(isCmdK){
        e.preventDefault();
        input.focus();
        input.select();
      }
      if(e.key === '/' && document.activeElement && ['INPUT','TEXTAREA'].indexOf(document.activeElement.tagName) === -1){
        e.preventDefault();
        input.focus();
      }
    });

    var kbd = widget.querySelector('#dcSearchKbd');
    if(kbd && /Mac|iPhone|iPad/.test(navigator.platform)) kbd.textContent = '⌘ K';

    return true;
  }

  function init(){
    injectStyles();
    var tries = 0;
    var iv = setInterval(function(){
      tries++;
      if(mountWidget() || tries > 60){
        clearInterval(iv);
      }
    }, 250);
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
        clearInterval(iv);
      }
    }, 250);
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
