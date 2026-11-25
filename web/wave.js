/* HAMAYUKI waveform player (progressive enhancement).
   Upgrades the plain <audio> mixes (.hy-mix) and track rows (.hy-tr li) into
   one shared player with waveforms drawn from /hamayuki/peaks.json
   (built by scripts/build-hamayuki-peaks.py). Without JS the native players
   still work. Source: https://github.com/yukihamada/hamayuki */
(function () {
  'use strict';
  if (window.__hyWave) return; window.__hyWave = 1;
  var BASE = '/hamayuki/audio/';
  var root = document.documentElement;
  var A = new Audio();
  A.preload = 'none';
  var PEAKS = {};
  var items = [];          // every playable item
  var cur = null;          // active item
  var part = 0;            // active file index of cur
  var pending = null;      // seek target waiting for metadata
  var raf = 0;

  function L(el) {
    var x = el && el.closest && el.closest('[data-l]');
    var l = x ? x.getAttribute('data-l') : (root.lang || 'ja');
    return l.indexOf('ja') === 0 ? 'ja' : 'en';
  }
  var TX = {
    ja: { play: '再生', pause: '一時停止', seek: '再生位置', now: '再生中', close: '閉じる', load: '読み込み中' },
    en: { play: 'Play', pause: 'Pause', seek: 'Position', now: 'Now playing', close: 'Close', load: 'Loading' }
  };
  function fmt(s) {
    s = Math.max(0, Math.floor(s || 0));
    var h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60;
    return (h ? h + ':' + (m < 10 ? '0' : '') : '') + m + ':' + (x < 10 ? '0' : '') + x;
  }
  function key(src) { return (src || '').split('/').pop().replace(/\.mp3.*$/, ''); }
  function cssv(el, n) { return getComputedStyle(el).getPropertyValue(n).trim(); }
  function accent(el) { return cssv(el, '--gold') || cssv(el, '--sun') || '#c9a962'; }

  /* ---------- styles ---------- */
  var st = document.createElement('style');
  st.textContent = [
    '.hy-wv-on>audio,.hy-wv-on .hy-parts{display:none!important}',
    '.wv{display:grid;gap:8px;margin-top:2px}',
    '.wv-row{display:flex;align-items:center;gap:14px}',
    '.wv-play{flex:0 0 52px;width:52px;height:52px;border-radius:50%;border:0;background:var(--gold,var(--sun,#c9a962));color:#0a0a0c;cursor:pointer;display:grid;place-items:center;position:relative}',
    '.wv-play svg,.wv-mp svg,.wv-bar button svg{width:20px;height:20px;fill:currentColor}',
    '.wv-play:focus-visible,.wv-c:focus-visible,.wv-mp:focus-visible,.wv-bar button:focus-visible{outline:2px solid var(--gold,var(--sun,#c9a962));outline-offset:3px}',
    '.wv-busy::after{content:"";position:absolute;inset:-4px;border-radius:50%;border:2px solid transparent;border-top-color:var(--gold,var(--sun,#c9a962));animation:wvspin .8s linear infinite}',
    '@keyframes wvspin{to{transform:rotate(360deg)}}',
    '@media (prefers-reduced-motion:reduce){.wv-busy::after{animation:none;border-color:var(--gold,var(--sun,#c9a962));opacity:.5}}',
    '.wv-meta{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}',
    '.wv-now{font-size:14.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.wv-now small{color:var(--dim,var(--mute,#9a9a9f));font-size:12px;margin-right:6px;letter-spacing:.04em}',
    '.wv-nx{align-self:flex-start;font:inherit;font-size:12.5px;color:var(--dim,var(--mute,#9a9a9f));background:none;border:0;padding:4px 0 10px;margin:0 0 -10px;min-height:34px;cursor:pointer;text-align:left;max-width:100%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.wv-nx:focus-visible{outline:2px solid var(--gold,var(--sun,#c9a962));outline-offset:0;border-radius:4px}',
    '.wv-nx:hover{color:var(--gold,var(--sun,#c9a962))}',
    '.wv-time{font-size:12.5px;color:var(--dim,var(--mute,#9a9a9f));font-variant-numeric:tabular-nums}',
    '.wv-c{position:relative;height:96px;cursor:pointer;touch-action:pan-y;border-radius:8px;-webkit-tap-highlight-color:transparent}',
    '.wv-c canvas{display:block;width:100%;height:100%}',
    '.wv-tip{position:absolute;top:4px;transform:translate(-50%,0);background:var(--bg-2,var(--bg,#111));border:1px solid var(--line,#2a2a2e);border-radius:6px;padding:3px 8px;font-size:12px;white-space:nowrap;pointer-events:none;opacity:0;transition:opacity .12s;font-variant-numeric:tabular-nums;max-width:70vw;overflow:hidden;text-overflow:ellipsis;z-index:2}',
    '.wv-c.hov .wv-tip{opacity:1}',
    '.wv-mc.hov .wv-tip{opacity:1}',
    '.hy-tr li.wv-li button[aria-pressed="true"]{color:#0a0a0c!important}',
    '@media (min-width:561px){.hy-tr li.wv-li{display:grid!important;grid-template-columns:44px minmax(150px,1fr) minmax(0,2fr) 5.2em 5.6em;align-items:center}.hy-tr li.wv-li .wv-mc{min-width:0}.hy-tr li.wv-li .hy-tag{justify-self:end}}',
    '.wv-ax{display:flex;justify-content:space-between;font-size:12px;color:var(--dim,var(--mute,#9a9a9f));font-variant-numeric:tabular-nums;margin-top:-2px}',
    '.hy-chap button[aria-current="true"]{color:var(--gold,var(--sun,#c9a962))}',
    '.hy-chap button[aria-current="true"] .tm{color:var(--gold,var(--sun,#c9a962))}',
    /* track rows */
    '.hy-tr li.wv-li{flex-wrap:wrap;row-gap:6px}',
    '.hy-tr li.wv-li .t{flex:1 1 140px}',
    '.wv-mc{flex:2 1 220px;min-width:160px;height:40px;position:relative;cursor:pointer;touch-action:pan-y;-webkit-tap-highlight-color:transparent}',
    '.wv-mc canvas{display:block;width:100%;height:100%}',
    '.wv-mt{font-size:12.5px;color:var(--dim,var(--mute,#9a9a9f));font-variant-numeric:tabular-nums;min-width:4.6em;text-align:right}',
    '.hy-tr li.wv-act{border-color:var(--gold,var(--sun,#c9a962))!important}',
    '.hy-tr li.wv-li button svg{width:16px;height:16px;fill:currentColor;display:block;margin:auto}',
    '@media (max-width:560px){.hy-tr li.wv-li{column-gap:12px}.hy-tr li.wv-li .t{order:1;flex:1 1 0}.hy-tr li.wv-li .hy-tag{order:2}.hy-tr li.wv-li::after{content:"";order:3;flex-basis:100%;height:0}.wv-mc{order:4;flex:1 1 0;min-width:0;margin-left:56px;height:36px}.wv-mt{order:5;min-width:0}.wv-c{height:80px}}',
    /* sticky bar */
    '.wv-bar{position:fixed;left:50%;bottom:max(12px,env(safe-area-inset-bottom));transform:translate(-50%,140%);width:min(720px,calc(100% - 24px));z-index:60;display:flex;align-items:center;gap:12px;padding:8px 10px 8px 8px;border-radius:14px;background:var(--bg-2,var(--bg,#111));border:1px solid var(--line,#2a2a2e);box-shadow:0 10px 30px rgba(0,0,0,.35);transition:transform .25s ease;color:var(--ink,#f4f1ea)}',
    '.wv-bar.on{transform:translate(-50%,0)}',
    '.wv-bar button{flex:0 0 44px;width:44px;height:44px;border-radius:50%;border:0;cursor:pointer;display:grid;place-items:center}',
    '.wv-bar .wv-mp{background:var(--gold,var(--sun,#c9a962));color:#0a0a0c}',
    '.wv-bar .wv-x{background:none;color:var(--dim,var(--mute,#9a9a9f))}',
    '.wv-bar .wv-bt{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px}',
    '.wv-bar .wv-bn{font-size:13.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.wv-bar .wv-bp{height:3px;border-radius:2px;background:var(--line,#2a2a2e);overflow:hidden}',
    '.wv-bar .wv-bp i{display:block;height:100%;width:0;background:var(--gold,var(--sun,#c9a962))}',
    '.wv-bar .wv-btm{font-size:11.5px;color:var(--dim,var(--mute,#9a9a9f));font-variant-numeric:tabular-nums}',
    '@media (prefers-reduced-motion:reduce){.wv-bar{transition:none}}'
  ].join('\n');
  document.head.appendChild(st);

  var ICON = {
    play: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z"/></svg>',
    pause: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z"/></svg>',
    x: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.4 5 5 6.4 10.6 12 5 17.6 6.4 19l5.6-5.6 5.6 5.6 1.4-1.4-5.6-5.6L19 6.4 17.6 5 12 10.6z"/></svg>'
  };

  /* ---------- drawing ---------- */
  function draw(it) {
    var c = it.canvas; if (!c) return;
    var w = c.clientWidth, h = c.clientHeight; if (!w || !h) return;
    var dpr = Math.min(2, window.devicePixelRatio || 1);
    if (c.width !== Math.round(w * dpr) || c.height !== Math.round(h * dpr)) { c.width = Math.round(w * dpr); c.height = Math.round(h * dpr); }
    var x = c.getContext('2d');
    x.setTransform(dpr, 0, 0, dpr, 0, 0);
    x.clearRect(0, 0, w, h);
    var gold = accent(c), ink = getComputedStyle(c).color;
    var rgb = (ink.match(/\d+(\.\d+)?/g) || [200, 200, 200]).map(Number);
    var light = (rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114) < 128; // dark ink = light theme
    var dimA = light ? 0.5 : 0.42, bandA = light ? 0.06 : 0.045;
    var bw = it.mini ? 2 : 2.5, gap = it.mini ? 1.5 : 1.5, step = bw + gap;
    var n = Math.max(8, Math.floor((w + gap) / step));
    var p = it.peaks, total = it.total || 1;
    var t = (cur === it) ? now() : (it.last || 0);
    var prog = Math.min(1, t / total);
    var hov = it.hover;
    var base = Math.round(h * (it.mini ? 0.72 : 0.7));
    if (it.chapters && it.chapters.length > 1) {
      var ci = chapterAt(it, hov != null ? hov * total : t);
      it.chapters.forEach(function (ch, j) {
        var x0 = ch.t / total * w, x1 = (j + 1 < it.chapters.length ? it.chapters[j + 1].t : total) / total * w;
        var hi = j === ci && (cur === it || hov != null || it.last);
        if (!hi && j % 2) { x.fillStyle = ink; x.globalAlpha = bandA; x.fillRect(x0, 0, x1 - x0, h); }
        if (hi) { x.fillStyle = gold; x.globalAlpha = 0.12; x.fillRect(x0, 0, x1 - x0, h); }
        if (j) { x.fillStyle = ink; x.globalAlpha = 0.18; x.fillRect(Math.round(x0), 0, 1, h); }
      });
      x.globalAlpha = 1;
    }
    for (var i = 0; i < n; i++) {
      var v = 0.18;
      if (p && p.length) {
        var a = Math.floor(i * p.length / n), b = Math.max(a + 1, Math.floor((i + 1) * p.length / n)), m = 0;
        for (var k = a; k < b && k < p.length; k++) if (p[k] > m) m = p[k];
        v = Math.pow(m / 99, it.mini ? 1.2 : 1.6);
      }
      var bh = Math.max(1.5, v * (base - 2));
      var px = i * step, f = (i + 0.5) / n;
      var played = f <= prog;
      x.fillStyle = played ? gold : ink;
      x.globalAlpha = played ? 1 : (hov != null && f <= hov ? Math.min(1, dimA + 0.22) : dimA);
      x.fillRect(px, base - bh, bw, bh);
      x.globalAlpha *= light ? 0.45 : 0.4;
      x.fillRect(px, base + 1.5, bw, bh * (1 - (it.mini ? 0.72 : 0.7)) / (it.mini ? 0.72 : 0.7) );
    }
    x.globalAlpha = 1;
    // playhead
    if (cur === it || it.last) {
      x.fillStyle = gold;
      x.fillRect(Math.min(w - 1.5, prog * w), 0, 1.5, h);
    }
    if (hov != null) {
      x.fillStyle = ink; x.globalAlpha = 0.6;
      x.fillRect(Math.round(hov * w), 0, 1, h);
      x.globalAlpha = 1;
    }
  }
  function drawAll() { items.forEach(draw); }

  /* ---------- engine ---------- */
  function offset(it, k) { var s = 0; for (var i = 0; i < k; i++) s += it.durs[i]; return s; }
  function now() { return cur ? offset(cur, part) + (pending != null ? pending : (A.currentTime || 0)) : 0; }
  function chapterAt(it, t) {
    if (!it.chapters) return -1;
    var r = -1; for (var i = 0; i < it.chapters.length; i++) if (t + 0.25 >= it.chapters[i].t) r = i; return r;
  }
  function load(it, k, t, play) {
    part = k;
    var src = BASE + it.files[k] + '.mp3';
    if (A.src.indexOf(src) < 0) { A.src = src; pending = t; A.load(); }
    else if (A.readyState < 1 || pending != null) pending = t;
    else { try { A.currentTime = t; } catch (e) { pending = t; } }
    if (play) A.play().catch(function () { busy(false); ui(); });
  }
  function seek(it, t, play) {
    t = Math.max(0, Math.min(it.total - 0.25, t));
    if (play === undefined) play = true;
    cur = it; it.last = t;
    var k = 0; while (k < it.files.length - 1 && t >= offset(it, k + 1)) k++;
    load(it, k, t - offset(it, k), play);
    if (!play && !A.paused) A.pause();
    reveal(it);
    ui(); meta();
  }
  function reveal(it) {
    var d = it.li && it.li.closest('details');
    if (d && !d.open && !A.paused) d.open = true;
  }
  function toggle(it) {
    if (cur === it && !A.paused) { A.pause(); return; }
    if (cur === it && A.src && !A.ended) { A.play().catch(function () {}); return; }
    seek(it, it.last && it.last < it.total - 1 ? it.last : 0, true);
  }
  A.addEventListener('loadedmetadata', function () {
    if (pending != null) { try { A.currentTime = pending; } catch (e) {} pending = null; }
    ui();
  });
  A.addEventListener('ended', function () {
    if (!cur) return;
    if (part + 1 < cur.files.length) { load(cur, part + 1, 0, true); return; }
    var it = cur; it.last = 0;
    if (it.next) { seek(it.next, 0, true); return; }
    seek(it, 0, false);
    ui();
  });
  function busy(on) { items.forEach(function (it) { if (it.btn) it.btn.classList.toggle('wv-busy', !!on && it === cur); }); }
  A.addEventListener('waiting', function () { busy(true); });
  A.addEventListener('playing', function () { busy(false); ui(); loop(); });
  A.addEventListener('pause', function () { busy(false); if (cur) cur.last = now(); ui(); });
  A.addEventListener('error', function () { busy(false); ui(); });

  function loop() {
    cancelAnimationFrame(raf);
    var lastSec = -1;
    (function f() {
      if (!cur) return;
      draw(cur);
      var s = Math.floor(now());
      if (s !== lastSec) { lastSec = s; tick(); }
      if (!A.paused) raf = requestAnimationFrame(f);
    })();
  }

  /* ---------- UI state ---------- */
  function setBtn(b, on, label, lang) {
    if (!b) return;
    b.innerHTML = on ? ICON.pause : ICON.play;
    b.setAttribute('aria-label', (on ? TX[lang].pause : TX[lang].play) + (label ? ': ' + label : ''));
    if (b.hasAttribute('aria-pressed')) b.setAttribute('aria-pressed', on ? 'true' : 'false');
  }
  function tick() {
    items.forEach(function (it) {
      var t = cur === it ? now() : (it.last || 0);
      if (it.timeEl) it.timeEl.textContent = fmt(t) + ' / ' + fmt(it.total);
      if (it.slider) {
        it.slider.setAttribute('aria-valuenow', String(Math.round(t)));
        it.slider.setAttribute('aria-valuetext', fmt(t) + ' / ' + fmt(it.total));
      }
      if (it.chapters) {
        var ci = chapterAt(it, t);
        if (ci !== it.ci) {
          it.ci = ci;
          it.chapters.forEach(function (ch, j) { if (ch.btn) ch.btn.setAttribute('aria-current', j === ci && (cur === it || it.last) ? 'true' : 'false'); });
          if (it.nowEl) it.nowEl.innerHTML = '<small>' + (ci >= 0 ? (ci + 1) + '/' + it.chapters.length : '') + '</small>' + esc(ci >= 0 ? it.chapters[ci].name : it.title);
          if (it.nxEl) {
            var nx = it.chapters[ci + 1];
            it.nxEl.hidden = !nx;
            if (nx) {
              it.nxEl.textContent = (it.lang === 'ja' ? '次 → ' : 'Next → ') + nx.name + '  ' + fmt(nx.t);
              it.nxEl.setAttribute('aria-label', (it.lang === 'ja' ? '次の曲から再生: ' : 'Play from next track: ') + nx.name);
            }
          }
        }
      }
    });
    if (cur) {
      var t = now();
      bar.n.textContent = cur.chapters && cur.ci >= 0 ? cur.title + ' — ' + cur.chapters[cur.ci].name : cur.title;
      bar.tm.textContent = fmt(t) + ' / ' + fmt(cur.total);
      bar.p.style.width = (t / cur.total * 100).toFixed(2) + '%';
      if ('mediaSession' in navigator && navigator.mediaSession.setPositionState && isFinite(cur.total)) {
        try { navigator.mediaSession.setPositionState({ duration: cur.total, position: Math.min(cur.total, t), playbackRate: 1 }); } catch (e) {}
      }
    }
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function ui() {
    var playing = !A.paused;
    items.forEach(function (it) {
      var on = it === cur && playing;
      setBtn(it.btn, on, it.title, it.lang);
      if (it.li) it.li.classList.toggle('wv-act', it === cur);
    });
    if (cur) setBtn(bar.b, playing, cur.title, cur.lang);
    if ('mediaSession' in navigator) navigator.mediaSession.playbackState = cur ? (playing ? 'playing' : 'paused') : 'none';
    tick(); drawAll(); showBar();
  }
  function meta() {
    if (!('mediaSession' in navigator) || !cur || !window.MediaMetadata) return;
    try {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: cur.title, artist: 'HAMAYUKI', album: 'HAMAYUKI Sessions',
        artwork: [{ src: '/hamayuki/photo.jpg', sizes: '512x512', type: 'image/jpeg' }]
      });
    } catch (e) {}
  }
  if ('mediaSession' in navigator) {
    var ms = navigator.mediaSession, h = function (n, f) { try { ms.setActionHandler(n, f); } catch (e) {} };
    h('play', function () { if (cur) A.play().catch(function () {}); });
    h('pause', function () { A.pause(); });
    h('seekto', function (d) { if (cur && d.seekTime != null) seek(cur, d.seekTime, !A.paused); });
    h('seekbackward', function (d) { if (cur) seek(cur, now() - (d.seekOffset || 10), !A.paused); });
    h('seekforward', function (d) { if (cur) seek(cur, now() + (d.seekOffset || 10), !A.paused); });
    h('nexttrack', function () {
      if (!cur) return;
      if (cur.chapters && cur.ci + 1 < cur.chapters.length) seek(cur, cur.chapters[cur.ci + 1].t, true);
      else if (cur.next) seek(cur.next, 0, true);
    });
    h('previoustrack', function () {
      if (!cur) return;
      if (cur.chapters && cur.ci > 0) seek(cur, cur.chapters[now() - cur.chapters[cur.ci].t > 3 ? cur.ci : cur.ci - 1].t, true);
      else seek(cur, 0, true);
    });
  }

  /* ---------- sticky bar ---------- */
  var bar = (function () {
    var d = document.createElement('div');
    d.className = 'wv-bar'; d.setAttribute('role', 'region');
    d.innerHTML = '<button type="button" class="wv-mp"></button><div class="wv-bt"><span class="wv-bn"></span><span class="wv-bp"><i></i></span><span class="wv-btm"></span></div><button type="button" class="wv-x">' + ICON.x + '</button>';
    document.body.appendChild(d);
    var o = { el: d, b: d.querySelector('.wv-mp'), n: d.querySelector('.wv-bn'), p: d.querySelector('.wv-bp i'), tm: d.querySelector('.wv-btm'), x: d.querySelector('.wv-x'), hidden: false };
    o.b.addEventListener('click', function () { if (cur) toggle(cur); });
    o.x.addEventListener('click', function () { A.pause(); o.hidden = true; showBar(); });
    return o;
  })();
  var visible = new Set();
  var io = 'IntersectionObserver' in window ? new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) visible.add(e.target); else visible.delete(e.target); });
    showBar();
  }) : null;
  function showBar() {
    var lang = (root.lang || 'ja').indexOf('ja') === 0 ? 'ja' : 'en';
    bar.el.setAttribute('aria-label', TX[lang].now);
    bar.x.setAttribute('aria-label', TX[lang].close);
    if (!A.paused) bar.hidden = false;
    var onScreen = cur && cur.box && visible.has(cur.box);
    var on = !!cur && !bar.hidden && !onScreen && (!A.paused || (cur.last || 0) > 0);
    bar.el.classList.toggle('on', on);
    document.body.style.paddingBottom = on ? '96px' : '';
    bar.el.inert = !on;
    if (!on) bar.el.setAttribute('aria-hidden', 'true'); else bar.el.removeAttribute('aria-hidden');
  }

  /* ---------- pointer / keyboard on a waveform ---------- */
  function bindWave(it, el) {
    function pos(ev) { var r = el.getBoundingClientRect(); return Math.max(0, Math.min(1, (ev.clientX - r.left) / r.width)); }
    var down = false;
    el.addEventListener('pointermove', function (ev) {
      if (ev.pointerType === 'touch' && !down) return;
      var f = pos(ev); it.hover = f; el.classList.add('hov');
      if (it.tip) {
        var t = f * it.total, ci = chapterAt(it, t);
        it.tip.textContent = fmt(t) + (ci >= 0 ? '  ' + it.chapters[ci].name : '');
        it.tip.style.top = it.mini ? '-4px' : '4px'; it.tip.style.transform = it.mini ? 'translate(-50%,-100%)' : 'translate(-50%,0)';
        var r = el.getBoundingClientRect(), tw = it.tip.offsetWidth / 2;
        it.tip.style.left = Math.max(tw, Math.min(r.width - tw, f * r.width)) + 'px';
      }
      draw(it);
    });
    el.addEventListener('pointerleave', function () { it.hover = null; el.classList.remove('hov'); draw(it); });
    el.addEventListener('pointerdown', function (ev) { down = true; if (ev.pointerType !== 'touch') el.setPointerCapture && el.setPointerCapture(ev.pointerId); });
    el.addEventListener('pointerup', function (ev) {
      if (!down) return; down = false;
      var f = pos(ev); seek(it, f * it.total, true);
      if (ev.pointerType === 'touch') { it.hover = null; el.classList.remove('hov'); }
    });
    el.addEventListener('pointercancel', function () { down = false; it.hover = null; el.classList.remove('hov'); draw(it); });
    el.addEventListener('keydown', function (ev) {
      var t = cur === it ? now() : (it.last || 0), d = ev.shiftKey ? 30 : 5, k = ev.key;
      if (k === 'ArrowRight' || k === 'ArrowUp') t += d;
      else if (k === 'ArrowLeft' || k === 'ArrowDown') t -= d;
      else if (k === 'PageUp') t += 60; else if (k === 'PageDown') t -= 60;
      else if (k === 'Home') t = 0; else if (k === 'End') t = it.total - 1;
      else if (k === ' ' || k === 'Enter') { ev.preventDefault(); toggle(it); return; }
      else return;
      ev.preventDefault();
      if (cur !== it) { it.last = Math.max(0, Math.min(it.total - 1, t)); tick(); draw(it); return; }
      seek(it, t, !A.paused);
    });
  }
  function slider(el, it, label) {
    el.tabIndex = 0;
    el.setAttribute('role', 'slider');
    el.setAttribute('aria-label', TX[it.lang].seek + ': ' + label);
    el.setAttribute('aria-valuemin', '0');
    el.setAttribute('aria-valuemax', String(Math.round(it.total)));
    el.setAttribute('aria-valuenow', '0');
    it.slider = el;
  }

  /* ---------- build ---------- */
  function partsOf(k) {
    var m = /^(.*-)(\d+)$/.exec(k);
    if (!m || !PEAKS[m[1] + '2']) return [k];
    var out = [], i = 1;
    while (PEAKS[m[1] + i]) out.push(m[1] + i++);
    return out;
  }
  function buildMix(box) {
    var au = box.querySelector('audio'); if (!au) return;
    var k = key(au.getAttribute('src')); if (!PEAKS[k]) return;
    var files = partsOf(k), lang = L(box);
    var it = { box: box, files: files, lang: lang, title: (box.querySelector('b') || {}).textContent || 'HAMAYUKI', mini: false };
    it.durs = files.map(function (f) { return PEAKS[f].d; });
    it.total = it.durs.reduce(function (a, b) { return a + b; }, 0);
    it.peaks = [].concat.apply([], files.map(function (f) { return PEAKS[f].p; }));
    var chs = box.querySelectorAll('.hy-chap button[data-t]');
    if (chs.length) {
      it.chapters = [].map.call(chs, function (b) {
        var tm = b.querySelector('.tm'), name = b.textContent.replace(tm ? tm.textContent : '', '').trim();
        return { t: +b.dataset.t, name: name, btn: b };
      });
      it.chapters.forEach(function (ch) {
        ch.btn.addEventListener('click', function () { seek(it, ch.t, true); });
      });
    }
    var w = document.createElement('div'); w.className = 'wv';
    w.innerHTML = '<div class="wv-row"><button type="button" class="wv-play"></button><div class="wv-meta"><span class="wv-now"></span><span class="wv-time"></span>' + (chs.length ? '<button type="button" class="wv-nx"></button>' : '') + '</div></div>' +
      '<div class="wv-c"><canvas aria-hidden="true"></canvas><span class="wv-tip" aria-hidden="true"></span></div>' +
      '<div class="wv-ax" aria-hidden="true"><span>0:00</span><span>' + fmt(it.total / 2) + '</span><span>' + fmt(it.total) + '</span></div>';
    au.parentNode.insertBefore(w, au);
    box.classList.add('hy-wv-on');
    it.btn = w.querySelector('.wv-play'); it.canvas = w.querySelector('canvas'); it.tip = w.querySelector('.wv-tip');
    it.nowEl = w.querySelector('.wv-now'); it.timeEl = w.querySelector('.wv-time');
    if (!it.chapters) { it.nowEl.hidden = true; it.timeEl.style.fontSize = '14.5px'; }
    if (it.chapters) it.nowEl.innerHTML = '<small>1/' + it.chapters.length + '</small>' + esc(it.chapters[0].name);
    it.ci = -2;
    it.nxEl = w.querySelector('.wv-nx');
    if (it.nxEl) it.nxEl.addEventListener('click', function () {
      var t = cur === it ? now() : (it.last || 0), ci = chapterAt(it, t);
      if (ci + 1 < it.chapters.length) seek(it, it.chapters[ci + 1].t, true);
    });
    var wc = w.querySelector('.wv-c');
    slider(wc, it, it.title); bindWave(it, wc);
    it.btn.addEventListener('click', function () { toggle(it); });
    if (io) io.observe(box);
    items.push(it);
  }
  function buildTrack(li, prev) {
    var b = li.querySelector('button[data-src]'); if (!b) return prev;
    var k = key(b.dataset.src); if (!PEAKS[k]) return prev;
    var tEl = li.querySelector('.t'), title = tEl ? tEl.firstChild.textContent.trim() : k;
    var it = { li: li, box: li, files: [k], durs: [PEAKS[k].d], total: PEAKS[k].d, peaks: PEAKS[k].p, lang: L(li), title: title, mini: true };
    var nb = b.cloneNode(false); nb.removeAttribute('data-src'); b.parentNode.replaceChild(nb, b); it.btn = nb;
    nb.addEventListener('click', function () { toggle(it); });
    var mc = document.createElement('div'); mc.className = 'wv-mc';
    mc.innerHTML = '<canvas aria-hidden="true"></canvas><span class="wv-tip" aria-hidden="true"></span>';
    var mt = document.createElement('span'); mt.className = 'wv-mt';
    tEl.parentNode.insertBefore(mc, tEl.nextSibling);
    var tag = li.querySelector('.hy-tag');
    if (tag) li.insertBefore(mt, tag); else li.appendChild(mt);
    li.classList.add('wv-li');
    it.canvas = mc.querySelector('canvas'); it.timeEl = mt; it.tip = mc.querySelector('.wv-tip');
    slider(mc, it, title); bindWave(it, mc);
    if (io) io.observe(li);
    if (prev) prev.next = it;
    items.push(it);
    return it;
  }
  function build() {
    document.querySelectorAll('.hy-mix').forEach(buildMix);
    // tracks chain per language block so "next" stays inside the same list
    var groups = new Map();
    document.querySelectorAll('.hy-tr li').forEach(function (li) {
      var g = L(li);
      groups.set(g, buildTrack(li, groups.get(g)));
    });
    items.forEach(function (it) { setBtn(it.btn, false, it.title, it.lang); });
    tick(); drawAll();
    var t; addEventListener('resize', function () { clearTimeout(t); t = setTimeout(drawAll, 60); });
    if ('ResizeObserver' in window) { var ro = new ResizeObserver(function () { drawAll(); }); items.forEach(function (it) { if (it.canvas) ro.observe(it.canvas); }); }
    // repaint when a closed <details> opens, the language or theme flips
    document.querySelectorAll('details').forEach(function (d) { d.addEventListener('toggle', drawAll); });
    new MutationObserver(function () {
      var lang = (root.lang || 'ja').indexOf('ja') === 0 ? 'ja' : 'en';
      if (cur && cur.lang !== lang) {
        var twin = items.filter(function (o) { return o.lang === lang && o.files.join() === cur.files.join(); })[0];
        if (twin) { var t = now(); cur.last = 0; twin.last = t; cur = twin; ui(); meta(); }
      }
      setTimeout(drawAll, 0); showBar();
    }).observe(root, { attributes: true, attributeFilter: ['lang', 'data-theme'] });
    if (window.matchMedia) matchMedia('(prefers-color-scheme: dark)').addEventListener && matchMedia('(prefers-color-scheme: dark)').addEventListener('change', drawAll);
  }
  window.hyStop = function () { A.pause(); };

  fetch('/hamayuki/peaks.json?v=2').then(function (r) { if (!r.ok) throw 0; return r.json(); })
    .then(function (j) { PEAKS = j; build(); })
    .catch(function () { /* keep native players */ });
})();
