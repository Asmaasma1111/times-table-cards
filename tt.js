/* Times Table Cards (بطاقات جدول الضرب): the start-up file.
   The first page asks the child's name and whether the child is a boy or a girl; then maths-boy.js or maths-girl.js
   (the cards) and stickerbook-boy.js or stickerbook-girl.js (the reward) are loaded, so the Arabic speaks to the child.
   Everything stays on this device: 'tt:profile' (name, boy or girl), 'tt:math' (the cards), 'tt:stickers' (the
   sticker book) and 'tt:sfx' (sound effects on or off). */
(() => {
'use strict';

const $ = (s, r = document) => r.querySelector(s);
const DEV = new URLSearchParams(location.search).get('dev') === '1';
const PROFILE_KEY = 'tt:profile', SB_KEY = 'tt:stickers', SFX_KEY = 'tt:sfx', DEV_KEY = 'tt:devOffset';
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function lsSet(k, v) { try { localStorage.setItem(k, v); return true; } catch (e) { return false; } }
const readJSON = k => { try { return JSON.parse(lsGet(k) || 'null'); } catch (e) { return null; } };
const esc = s => String(s).replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));

let devOffset = DEV ? (parseInt(lsGet(DEV_KEY) || '0', 10) || 0) : 0;
const pad = n => String(n).padStart(2, '0');
const fmt = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
function today() { const d = new Date(); d.setDate(d.getDate() + devOffset); return fmt(d); }
function addDays(ds, n) { const [y, m, d] = ds.split('-').map(Number); const x = new Date(y, m - 1, d); x.setDate(x.getDate() + n); return fmt(x); }
const isDay = x => typeof x === 'string' && /^\d{4}-\d\d-\d\d$/.test(x);

// the child: a name, and a boy or a girl
const cleanProfile = p => ({ name: p && typeof p.name === 'string' ? p.name.trim().slice(0, 30) : '', who: p && (p.who === 'boy' || p.who === 'girl') ? p.who : '' });
let profile = cleanProfile(readJSON(PROFILE_KEY));
const saveProfile = () => lsSet(PROFILE_KEY, JSON.stringify(profile));

// the sound effects below ask for these: one look, and the sound effects switch
const isMama = () => false;
const st = { settings: { sfx: lsGet(SFX_KEY) !== '0' } };

/* ---------- sound effects, confetti, press and hold, the practice calendar, screens (as in the original app) ---------- */
const TRACK_FROM = '2026-10-01';                         // the practice calendar starts with this version of the app
const SFX = {
  ctx: null, out: null, noise: null, busyUntil: 0,
  init() {
    try {
      if (!this.ctx) {
        const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
        this.ctx = new AC();
        this.out = this.ctx.createGain();
        this.out.connect(this.ctx.destination);
      }
      this.level();
      if (this.ctx.state !== 'running') this.ctx.resume();
      const b = this.ctx.createBuffer(1, 1, 22050), s = this.ctx.createBufferSource();
      s.buffer = b; s.connect(this.ctx.destination); s.start(0);
    } catch (e) {}
  },
  level() { if (this.out) this.out.gain.value = isMama() ? 0.25 : 0.35; },   // share of the voice's loudness
  ready() {
    if (!st.settings.sfx || !this.ctx) return false;
    if (this.ctx.state !== 'running') { try { this.ctx.resume(); } catch (e) {} }
    return true;
  },
  hold(sec) { this.busyUntil = Math.max(this.busyUntil, performance.now() + sec * 1000); },
  tone(f, at, dur, peak, type = 'sine', attack = 0.012) {
    const c = this.ctx, o = c.createOscillator(), g = c.createGain(), t = c.currentTime + 0.02 + at;
    o.type = type; o.frequency.setValueAtTime(f, t);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(this.out);
    o.start(t); o.stop(t + dur + 0.05);
  },
  bell(f, at, dur, peak) { this.tone(f, at, dur, peak, 'sine'); this.tone(f, at, dur * 0.8, peak * 0.2, 'triangle'); },
  flip() {
    if (!this.ready()) return;
    const c = this.ctx;
    if (!this.noise) {
      const len = Math.floor(c.sampleRate * 0.2), b = c.createBuffer(1, len, c.sampleRate), d = b.getChannelData(0);
      for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
      this.noise = b;
    }
    const s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain(), t = c.currentTime + 0.01;
    s.buffer = this.noise;
    f.type = 'bandpass'; f.Q.value = 0.8;
    f.frequency.setValueAtTime(700, t); f.frequency.exponentialRampToValueAtTime(3200, t + 0.15);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.7, t + 0.03);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.15);
    s.connect(f); f.connect(g); g.connect(this.out);
    s.start(t); s.stop(t + 0.18);
    this.hold(0.18);
  },
  good() { if (!this.ready()) return; this.bell(1318.5, 0, 0.32, 0.5); this.bell(1760, 0.1, 0.65, 0.5); this.hold(0.8); },
  again() { if (!this.ready()) return; this.tone(440, 0, 0.24, 0.3); this.tone(329.6, 0.15, 0.34, 0.3); this.hold(0.52); },
  star(at = 0) { if (!this.ready()) return; this.tone(2093, at, 0.09, 0.3, 'sine', 0.006); this.tone(4186, at, 0.06, 0.05, 'sine', 0.004); this.hold(at + 0.13); },
  unlock() { if (!this.ready()) return; [523.25, 659.25, 783.99, 1046.5].forEach((f, i) => this.bell(f, i * 0.12, i === 3 ? 0.9 : 0.4, 0.42)); this.hold(1.3); }
};
let confettiRun = 0;
function stopConfetti(cv = $('#confetti')) { confettiRun++; cv.getContext('2d').clearRect(0, 0, cv.width, cv.height); }
function confetti(cv = $('#confetti')) {
  if (reduced()) return;
  const run = ++confettiRun;
  const ctx = cv.getContext('2d'), dpr = Math.min(2, window.devicePixelRatio || 1);
  const W = innerWidth, H = innerHeight;
  cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const cols = ['#FFD84D', '#8FE3BF', '#FF6FA8', '#DCD6F7', '#2B2340'];
  const P = Array.from({ length: 150 }, (_, i) => {
    const left = i % 2 === 0;
    return { x: left ? W * 0.1 : W * 0.9, y: H * 0.85, vx: (left ? 1 : -1) * (3 + Math.random() * 9), vy: -(12 + Math.random() * 12),
             r: Math.random() * 6, vr: (Math.random() - 0.5) * 0.35, w: 9 + Math.random() * 8, h: 5 + Math.random() * 6,
             c: cols[i % cols.length], round: Math.random() < 0.3 };
  });
  const t0 = performance.now();
  const frame = now => {
    if (run !== confettiRun) return;
    const t = now - t0;
    ctx.clearRect(0, 0, W, H);
    ctx.globalAlpha = t > 2600 ? Math.max(0, 1 - (t - 2600) / 700) : 1;
    P.forEach(p => {
      p.vy += 0.38; p.vx *= 0.985; p.x += p.vx; p.y += p.vy; p.r += p.vr;
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r); ctx.fillStyle = p.c;
      if (p.round) { ctx.beginPath(); ctx.arc(0, 0, p.h * 0.7, 0, Math.PI * 2); ctx.fill(); }
      else ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h * Math.abs(Math.cos(p.r * 1.7)) + 1);
      ctx.restore();
    });
    if (t < 3300) requestAnimationFrame(frame); else ctx.clearRect(0, 0, W, H);
  };
  requestAnimationFrame(frame);
}
function holdToOpen(el, ms, fn) {
  let timer = null;
  const cancel = () => { if (timer) { clearTimeout(timer); timer = null; } el.classList.remove('holding'); };
  el.addEventListener('pointerdown', e => {
    e.preventDefault(); cancel();
    el.classList.add('holding');
    timer = setTimeout(() => { timer = null; el.classList.remove('holding'); fn(); }, ms);
  });
  ['pointerup', 'pointerleave', 'pointercancel'].forEach(ev => el.addEventListener(ev, cancel));
  el.addEventListener('contextmenu', e => e.preventDefault());
  el.addEventListener('click', e => e.preventDefault());
}
function calendarHTML(active, days, reg, goalMin) {
  const t = today(), [y, m, d] = t.split('-').map(Number);
  const start = addDays(t, -new Date(y, m - 1, d).getDay() - 28);
  const set = new Set(days), regSet = new Set(reg);
  let cells = ['S', 'M', 'T', 'W', 'T', 'F', 'S'].map(x => `<span class="cal-h">${x}</span>`).join('');
  for (let i = 0; i < 35; i++) {
    const day = addDays(start, i), [, , dd] = day.split('-').map(Number), secs = active[day] || 0;
    const future = day > t, measured = secs > 0, goal = goalMin > 0 && secs >= goalMin * 60;
    const cls = ['cal-d', future ? 'future' : '', day === t ? 'today' : '', goal ? 'goal' : set.has(day) ? 'done' : '', regSet.has(day) && !measured ? 'reg' : ''].filter(Boolean).join(' ');
    const mark = measured ? `${Math.max(1, Math.round(secs / 60))}m` : set.has(day) ? '✓' : '';
    const tap = !future && !measured && day >= TRACK_FROM;
    cells += tap ? `<button class="${cls}" data-day="${day}" aria-label="${day}${set.has(day) ? ', practised' : ''}"><b>${dd}</b><i>${mark}</i></button>`
      : `<span class="${cls}"><b>${dd}</b><i>${mark}</i></span>`;
  }
  return `<div class="cal">${cells}</div>`;
}
function show(name) {     // every screen (the times-tables screens too): only the named one is visible
  document.querySelectorAll('body > .screen').forEach(el => { el.hidden = el.id !== name; });
  if (['home', 'done', 'mhome', 'mdone', 'lhome', 'apps', 'rhome'].includes(name) && reloadForUpdate.pending) setTimeout(reloadForUpdate, 300);
}
function toast(msg) {
  const t = $('#toast'); t.textContent = msg; t.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => { t.hidden = true; }, 2600);
}
function isIOS() { return /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1); }

/* ---------- the sticker book: a sticker for every 2 days in a row with the daily goal reached ---------- */
// The goal days are kept here as they happen (the cards keep only the last 120 days of minutes), with any day a parent
// registers on the calendar. A girl's book and a boy's book each have their own stickers.
const cleanSB = s => {
  const o = s && typeof s === 'object' ? s : {};
  const book = b => ({ got: b && Array.isArray(b.got) ? b.got : [] });
  return { days: Array.isArray(o.days) ? o.days.filter(isDay) : [], per: Math.max(1, Math.min(7, Number(o.per) || 2)), girl: book(o.girl), boy: book(o.boy) };
};
let sbState = cleanSB(readJSON(SB_KEY));
const saveSB = () => lsSet(SB_KEY, JSON.stringify(sbState));
let MATHS = null, SB = null;
function goalDays() {
  const m = MATHS.state, goal = m.settings.goalMin * 60, set = new Set(sbState.days);
  Object.keys(m.active || {}).forEach(d => { if (isDay(d) && m.active[d] >= goal) set.add(d); });
  (m.reg || []).forEach(d => { if (isDay(d)) set.add(d); });
  if (set.size !== sbState.days.length) { sbState.days = [...set].sort(); saveSB(); }
  return sbState.days;
}
const sbView = {
  get days() { return goalDays(); },
  get stk() { return sbState[profile.who]; },
  set stk(v) { sbState[profile.who] = v; }
};

/* ---------- backup and restore: one small file with everything ---------- */
function backup() {
  const data = JSON.stringify({ app: 'times-table-cards', v: 1, saved: new Date().toISOString(), profile, math: MATHS.snapshot(), stickers: sbState });
  const name = `times-table-cards-backup-${today()}.json`;
  let file = null;
  try { file = new File([data], name, { type: 'application/json' }); } catch (e) {}
  if (file && isIOS() && navigator.canShare && navigator.canShare({ files: [file] })) {
    navigator.share({ files: [file] }).catch(() => {});
    return;
  }
  const url = URL.createObjectURL(file || new Blob([data], { type: 'application/json' }));
  const a = document.createElement('a'); a.href = url; a.download = name;
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
  toast('Backup saved.');
}
async function restore(file) {
  try {
    const obj = JSON.parse(await file.text());
    if (!obj || obj.app !== 'times-table-cards' || !MATHS.valid(obj.math)) throw new Error('bad');
    if (!confirm('Replace the progress on this device with this backup?')) return;
    MATHS.replace(obj.math);
    lsSet(SB_KEY, JSON.stringify(cleanSB(obj.stickers)));
    const p = cleanProfile(obj.profile);
    if (p.name && p.who) lsSet(PROFILE_KEY, JSON.stringify(p));
    location.reload();                    // a boy's backup on a girl's page (or the other way) needs the other words
  } catch (e) { toast('That file is not a Times Table Cards backup.'); }
}

/* ---------- the parent area: the child, and the sticker book ---------- */
function parentRows() {
  const per = sbState.per, n = SB ? SB.count() : 0, f = SB ? SB.friends() : 0, total = SB ? SB.friendsTotal() : 0, next = SB ? SB.nextIn() : per;
  const seg = v => `<button data-tt-who="${v}" aria-pressed="${profile.who === v}">${v === 'boy' ? 'Boy' : 'Girl'}</button>`;
  return `<h2 class="mx-h2">The child</h2>
    <div class="p-group">
      <div class="p-row"><label for="ttName">Name<span class="sub">Shown on Home and on the sticker book</span></label><input id="ttName" class="p-input" type="text" maxlength="30" value="${esc(profile.name)}"></div>
      <div class="p-row"><span>Boy or girl<span class="sub">The Arabic speaks to a boy (ابدأ، أحسنت) or a girl (ابدئي، أحسنتِ). Each has a sticker book of its own: blue with boys' stickers, or pink with girls' stickers.</span></span><div class="seg">${seg('boy')}${seg('girl')}</div></div>
    </div>
    <h2 class="mx-h2">Sticker book</h2>
    <div class="p-group">
      <div class="p-row"><span>${n} sticker${n === 1 ? '' : 's'} · ${f} of ${total} Star Friends<span class="sub">A day counts when the daily goal is reached (or when you register it on the calendar above). Next sticker after ${next} more day${next === 1 ? '' : 's'} in a row · every 7th reward is a Star Friend</span></span><button class="p-btn" data-tt="stickers">Open the sticker book</button></div>
      <div class="p-row"><span>Days in a row for one sticker<span class="sub">Stickers already earned are kept if you change this</span></span><div class="step"><button class="p-btn" data-tt-per="-1" aria-label="Less">−</button><output>${per}</output><button class="p-btn" data-tt-per="1" aria-label="More">+</button></div></div>
    </div>

    `;
}
function onParent(e) {
  const b = e.target.closest('button'); if (!b) return;
  if (b.dataset.ttWho && b.dataset.ttWho !== profile.who) {
    if (!confirm(b.dataset.ttWho === 'boy' ? 'Change to a boy? The Arabic will speak to a boy, and the blue sticker book with boys\' stickers will open.'
      : 'Change to a girl? The Arabic will speak to a girl, and the pink sticker book with girls\' stickers will open.')) return;
    profile.who = b.dataset.ttWho; saveProfile(); location.reload();
  } else if (b.dataset.ttPer) {
    sbState.per = Math.max(1, Math.min(7, sbState.per + Number(b.dataset.ttPer))); saveSB();
    b.parentElement.querySelector('output').textContent = sbState.per;
  } else if (b.dataset.tt === 'stickers' && SB) SB.open(() => MATHS.renderParent() || show('mparent'));
}

/* ---------- updates: a new version reloads by itself, but never in the middle of a round ---------- */
function reloadForUpdate() {
  if (!reloadForUpdate.pending || (MATHS && MATHS.busy()) || (SB && SB.busy())) return;
  location.reload();
}

/* ---------- developer mode (?dev=1): move the date on to test the schedule ---------- */
function renderDev() {
  const bar = $('#devbar');
  bar.hidden = false;
  bar.innerHTML = `<span>dev · ${today()} (+${devOffset}d)</span><button data-dev="plus">+1 day</button><button data-dev="zero">real date</button>`;
}

/* ---------- the first page: the name, and a boy or a girl ---------- */
function askWho() {
  const name = $('#ttNameIn'), go = $('#ttGo');
  let who = profile.who;
  const ready = () => { go.disabled = !(name.value.trim() && who); };
  name.value = profile.name;
  document.querySelectorAll('[data-pick]').forEach(b => {
    b.setAttribute('aria-pressed', String(b.dataset.pick === who));
    b.addEventListener('click', () => {
      who = b.dataset.pick; document.documentElement.dataset.who = who;
      document.querySelectorAll('[data-pick]').forEach(x => x.setAttribute('aria-pressed', String(x === b)));
      ready();
    });
  });
  name.addEventListener('input', ready);
  name.addEventListener('keydown', e => { if (e.key === 'Enter') name.blur(); });
  go.addEventListener('click', () => {
    if (go.disabled) return;
    profile = cleanProfile({ name: name.value, who }); saveProfile();
    start();
  });
  ready();
  show('ttWho');
}

function load(src) {
  return new Promise((ok, fail) => { const s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = fail; document.body.append(s); });
}
async function start() {
  if (!profile.name || !profile.who) return askWho();
  document.documentElement.dataset.who = profile.who;
  try { await load(`maths-${profile.who}.js`); await load(`stickerbook-${profile.who}.js`); }
  catch (e) { document.body.innerHTML = '<p style="font:24px sans-serif;padding:40px;text-align:center">The app could not load. Please connect to the internet once and try again.</p>'; return; }
  MATHS = window.TimesTables.mount({
    today, lsGet, lsSet, show, toast, SFX, confetti, stopConfetti, holdToOpen, reduced, DEV, backup, restore, calendarHTML,
    sfx: v => { if (v !== undefined) { st.settings.sfx = !!v; lsSet(SFX_KEY, v ? '1' : '0'); } return st.settings.sfx; },
    setDeck: () => {}, stopEnglish: () => {}, english: () => {},
    parentRows,
    onHome() {
      $('#ttHello').textContent = `أهلاً يا ${profile.name}!`;
      if (!SB) return;
      SB.sync(); SB.homeCard();
      if (SB.pending()) setTimeout(() => { if (!$('#mhome').hidden && SB.pending()) SB.celebrate(() => MATHS.home()); }, 700);
    },
    onDone() {
      if (!SB) return;
      SB.sync();
      if (SB.pending()) setTimeout(() => { if (!$('#mdone').hidden && SB.pending()) SB.celebrate(() => MATHS.home()); }, 900);
    }
  });
  SB = window.StickerBook.mount({
    st: () => sbView, save: saveSB, today, addDays, show, SFX, confetti, stopConfetti, reduced, toast,
    perDays: () => sbState.per, name: () => profile.name, stopEnglish: () => {}, home: () => MATHS.home()
  });
  await SB.ready;
  document.addEventListener('click', e => { if (e.target.closest('[data-backup]')) backup(); });   // the line under "Created by" on Home
  document.addEventListener('pointerdown', () => { if (SFX.ctx && SFX.ctx.state !== 'running') { try { SFX.ctx.resume(); } catch (e) {} } }, true);
  $('#mparent').addEventListener('click', onParent);
  $('#mparent').addEventListener('input', e => { if (e.target.id === 'ttName' && e.target.value.trim()) { profile.name = e.target.value.trim().slice(0, 30); saveProfile(); } });
  if (DEV) {
    renderDev();
    $('#devbar').addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      devOffset = b.dataset.dev === 'plus' ? devOffset + 1 : 0;
      lsSet(DEV_KEY, String(devOffset));
      renderDev(); MATHS.home();
    });
    window.TT = { get MATHS() { return MATHS; }, get SB() { return SB; }, get sbState() { return sbState; }, get profile() { return profile; } };
  }
  MATHS.home();
}

start();
if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
  const hadController = !!navigator.serviceWorker.controller;
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!hadController || reloadForUpdate.pending) return;
    reloadForUpdate.pending = true;
    reloadForUpdate();
  });
  navigator.serviceWorker.register('sw.js').then(reg => {
    document.addEventListener('visibilitychange', () => { if (!document.hidden) reg.update().catch(() => {}); });
  }).catch(() => {});
}
})();
