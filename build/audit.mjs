// Render + audit the built site at phone / tablet / desktop widths over CDP.
// No third-party deps: raw WebSocket + Runtime.evaluate.
// Reports, per page and width: horizontal overflow, heading-order violations,
// text contrast (composited over real backgrounds), broken images, failed
// requests, console errors, and a full-page screenshot.
import fs from "node:fs";

const CDP = process.env.CDP || "http://127.0.0.1:9333";
const ORIGIN = process.env.ORIGIN || "http://127.0.0.1:8123";
const OUT = process.env.OUT || "/tmp/larsen_audit";
const PAGES = ["index.html", "services.html", "about.html", "contact.html", "privacy.html"];
const WIDTHS = { phone: 390, tablet: 834, desktop: 1440 };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class Conn {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.events = []; }
  connect() {
    return new Promise((res, rej) => {
      this.ws.onopen = () => res();
      this.ws.onerror = (e) => rej(new Error("ws error"));
      this.ws.onmessage = (m) => {
        const d = JSON.parse(m.data);
        if (d.id && this.pending.has(d.id)) {
          const p = this.pending.get(d.id); this.pending.delete(d.id);
          d.error ? p.rej(new Error(JSON.stringify(d.error))) : p.res(d.result);
        } else if (d.method) this.events.push(d);
      };
    });
  }
  send(method, params = {}, timeout = 30000) {
    const id = ++this.id;
    return new Promise((res, rej) => {
      this.pending.set(id, { res, rej });
      this.ws.send(JSON.stringify({ id, method, params }));
      setTimeout(() => { if (this.pending.has(id)) { this.pending.delete(id); rej(new Error("timeout " + method)); } }, timeout);
    });
  }
  close() { try { this.ws.close(); } catch {} }
}

const AUDIT = `(() => {
  const vw = window.innerWidth;
  const res = { overflow: [], headings: [], contrast: [], overImage: [], imgs: [], title: document.title, desc: (document.querySelector('meta[name="description"]')||{}).content || "" };

  const isVisible = (el) => {
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };

  // ---- horizontal overflow
  for (const el of document.querySelectorAll('body *')) {
    if (!isVisible(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.right > vw + 1 || r.left < -1) {
      res.overflow.push({ tag: el.tagName, cls: String(el.className||'').slice(0,48),
        left: Math.round(r.left), right: Math.round(r.right), txt: (el.textContent||'').trim().slice(0,40) });
    }
  }
  res.docScrollW = document.documentElement.scrollWidth;

  // ---- heading order
  const hs = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].filter(isVisible);
  let prev = 0;
  for (const h of hs) {
    const lvl = +h.tagName[1];
    if (prev && lvl > prev + 1) res.headings.push({ tag: h.tagName, prev, txt: h.textContent.trim().slice(0,60) });
    prev = lvl;
  }
  res.h1count = hs.filter(h => h.tagName === 'H1').length;

  // ---- colour maths
  const parse = (c) => {
    const m = c.match(/rgba?\\(([^)]+)\\)/); if (!m) return null;
    const p = m[1].split(',').map(s => parseFloat(s.trim()));
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const over = (fg, bg) => ({ r: fg.r*fg.a + bg.r*(1-fg.a), g: fg.g*fg.a + bg.g*(1-fg.a), b: fg.b*fg.a + bg.b*(1-fg.a), a: 1 });
  const lin = (v) => { v /= 255; return v <= 0.04045 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
  const lum = (c) => 0.2126*lin(c.r) + 0.7152*lin(c.g) + 0.0722*lin(c.b);
  const ratio = (a, b) => { const l1 = lum(a), l2 = lum(b); const hi = Math.max(l1,l2), lo = Math.min(l1,l2); return (hi+0.05)/(lo+0.05); };

  const bgOf = (el) => {
    let layers = [], node = el, img = false;
    while (node && node !== document.documentElement.parentNode) {
      const s = getComputedStyle(node);
      const img2 = s.backgroundImage && s.backgroundImage !== 'none';
      const c = parse(s.backgroundColor);
      if (c && c.a > 0) layers.push(c);
      if (img2) { img = true; break; }
      if (c && c.a >= 1) break;
      if (node.tagName === 'IMG') { img = true; break; }
      node = node.parentElement;
      if (!node) break;
    }
    let base = { r: 251, g: 250, b: 247, a: 1 };
    for (let i = layers.length - 1; i >= 0; i--) base = over(layers[i], base);
    return { c: base, img };
  };

  const check = (el, colorStr, fs, fw, label) => {
    const fg = parse(colorStr); if (!fg) return;
    const { c: bg, img } = bgOf(el);
    if (img) { res.overImage.push(label); return; }
    const eff = fg.a < 1 ? over(fg, bg) : fg;
    const large = fs >= 24 || (fs >= 18.66 && fw >= 700);
    const need = large ? 3.0 : 4.5;
    const r = ratio(eff, bg);
    if (r < need - 0.005) res.contrast.push({ label, ratio: +r.toFixed(2), need, fs: +fs.toFixed(1), fw,
      color: colorStr, bg: 'rgb(' + [bg.r,bg.g,bg.b].map(Math.round).join(',') + ')' });
  };

  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walker.nextNode())) {
    const txt = n.nodeValue.trim(); if (!txt) continue;
    const el = n.parentElement; if (!el || !isVisible(el)) continue;
    const s = getComputedStyle(el);
    check(el, s.color, parseFloat(s.fontSize), parseInt(s.fontWeight) || 400,
      el.tagName.toLowerCase() + '.' + String(el.className||'').split(' ')[0] + ' "' + txt.slice(0,24) + '"');
  }
  // pseudo-element markers that render text (list numerals)
  for (const el of document.querySelectorAll('ol.services > li, .svc-grid li, ul.checks li')) {
    if (!isVisible(el)) continue;
    const s = getComputedStyle(el, '::before');
    const content = s.content;
    if (!content || content === 'none' || content === '""' || content === "''") continue;
    if (s.backgroundColor && s.backgroundColor !== 'rgba(0, 0, 0, 0)' && (!content || content === '""')) continue;
    const fs = parseFloat(s.fontSize), fw = parseInt(s.fontWeight) || 400;
    check(el, s.color, fs, fw, '::before ' + el.tagName + '.' + String(el.className||'').split(' ')[0]);
  }

  // ---- images / lazy state
  for (const im of document.images) {
    res.imgs.push({ src: im.currentSrc || im.src, ok: im.complete && im.naturalWidth > 0,
      w: im.naturalWidth, h: im.naturalHeight, alt: im.alt || '' });
  }
  return res;
})()`;

fs.mkdirSync(OUT, { recursive: true });

async function newTab() {
  let r = await fetch(CDP + "/json/new?about:blank", { method: "PUT" });
  if (!r.ok) r = await fetch(CDP + "/json/new?about:blank");
  return r.json();
}

const tab = await newTab();
const conn = new Conn(new WebSocket(tab.webSocketDebuggerUrl));
await conn.connect();
await conn.send("Page.enable");
await conn.send("Runtime.enable");
await conn.send("Network.enable");
await conn.send("Log.enable");

const report = { pages: {}, problems: [] };

for (const [dev, width] of Object.entries(WIDTHS)) {
  await conn.send("Emulation.setDeviceMetricsOverride", {
    width, height: dev === "phone" ? 844 : 1000, deviceScaleFactor: dev === "desktop" ? 1 : 2,
    mobile: dev === "phone",
  });
  for (const page of PAGES) {
    conn.events.length = 0;
    const url = ORIGIN + "/" + page;
    await conn.send("Page.navigate", { url });
    const deadline = Date.now() + 20000;
    let loaded = false;
    while (Date.now() < deadline) {
      if (conn.events.some((e) => e.method === "Page.loadEventFired")) { loaded = true; break; }
      await sleep(150);
    }
    await conn.send("Runtime.evaluate", { expression: "document.fonts.ready", awaitPromise: true }).catch(() => {});
    // scroll the whole page so lazy-loaded images fetch (as a real visitor would)
    await conn.send("Runtime.evaluate", {
      expression: `(async () => { const h = document.body.scrollHeight;
        for (let y = 0; y < h; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 40)); }
        window.scrollTo(0, 0); await new Promise(r => setTimeout(r, 350)); })()`,
      awaitPromise: true,
    }).catch(() => {});
    await sleep(700);
    const bad = conn.events.filter((e) => e.method === "Network.loadingFailed" ||
      (e.method === "Network.responseReceived" && e.params.response.status >= 400))
      .map((e) => e.params.response ? e.params.response.status + " " + e.params.response.url : e.params.errorText + " " + (e.params.requestId || ""));
    const consoleMsgs = conn.events.filter((e) => e.method === "Runtime.consoleAPICalled" && ["error", "warning"].includes(e.params.type))
      .map((e) => e.params.args.map((a) => a.value || a.description || "").join(" ").slice(0, 200));
    const exceptions = conn.events.filter((e) => e.method === "Runtime.exceptionThrown")
      .map((e) => (e.params.exceptionDetails.exception || {}).description || e.params.exceptionDetails.text);
    let audit = null, err = null;
    try {
      audit = (await conn.send("Runtime.evaluate", { expression: AUDIT, returnByValue: true })).result.value;
    } catch (e) { err = String(e); }

    const lm = await conn.send("Page.getLayoutMetrics");
    const h = Math.ceil(lm.cssContentSize.height);
    const shot = await conn.send("Page.captureScreenshot", {
      format: "png", captureBeyondViewport: true,
      clip: { x: 0, y: 0, width, height: Math.min(h, 12000), scale: 1 },
    });
    const file = `${OUT}/${page.replace(".html", "")}-${dev}.png`;
    fs.writeFileSync(file, Buffer.from(shot.data, "base64"));

    report.pages[`${page}@${dev}`] = {
      loaded, height: h, overflow: audit && audit.overflow.length, headings: audit && audit.headings.length,
      contrast: audit && audit.contrast.length, h1: audit && audit.h1count, imgs: audit && audit.imgs.length,
      badRequests: bad, console: consoleMsgs, exceptions, err,
      audit, screenshot: file,
    };
    console.error(`[${dev} ${width}] ${page}  h=${h} overflow=${audit ? audit.overflow.length : "?"} ` +
      `headings=${audit ? audit.headings.length : "?"} contrast=${audit ? audit.contrast.length : "?"} ` +
      `badReq=${bad.length} console=${consoleMsgs.length} exc=${exceptions.length}`);
  }
}

conn.close();
try { await fetch(CDP + "/json/close/" + tab.id); } catch {}
fs.writeFileSync(`${OUT}/report.json`, JSON.stringify(report, null, 1));
console.log("report: " + OUT + "/report.json");
