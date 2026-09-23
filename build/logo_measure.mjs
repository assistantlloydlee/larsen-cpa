// Measure the logo against the page ground on the PUBLISHED page.
// Captures a 1:1 viewport screenshot plus the geometry, so the pixels can be sampled.
import fs from "node:fs";

const CDP = process.env.CDP || "http://127.0.0.1:9333";
const URL_ = process.env.PAGE || "https://assistantlloydlee.github.io/larsen-cpa/";
const WIDTH = Number(process.env.W || 1440);
const OUT = process.env.OUT || "/tmp/logo_measure";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const t = await (await fetch(CDP + "/json/new?" + encodeURIComponent("about:blank"), { method: "PUT" })).json();
const ws = new WebSocket(t.webSocketDebuggerUrl);
let id = 0; const pend = new Map();
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { const q = pend.get(d.id); pend.delete(d.id); d.error ? q.rej(new Error(JSON.stringify(d.error))) : q.res(d.result); } };
await new Promise((r) => { ws.onopen = r; });
const send = (method, params = {}) => { const i = ++id; return new Promise((res, rej) => { pend.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); setTimeout(() => { if (pend.has(i)) { pend.delete(i); rej(new Error("t/o " + method)); } }, 40000); }); };
const ev = async (e) => (await send("Runtime.evaluate", { expression: e, returnByValue: true })).result.value;

await send("Page.enable");
await send("Network.enable");
await send("Network.setCacheDisabled", { cacheDisabled: true });
await send("Emulation.setDeviceMetricsOverride", { width: WIDTH, height: 900, deviceScaleFactor: 1, mobile: false });
await send("Page.navigate", { url: URL_ });
await sleep(5000);
await ev("document.fonts.ready");
await sleep(1200);
await ev("window.scrollTo(0,0)");
await sleep(600);

const geo = await ev(`(() => {
  const img = document.querySelector('.masthead .logo img');
  const r = img.getBoundingClientRect();
  const reg = document.querySelector('.masthead');
  const rr = reg.getBoundingClientRect();
  const cs = getComputedStyle(reg);
  return {
    page: location.href,
    width: innerWidth,
    img: { x: r.x, y: r.y, w: r.width, h: r.height, src: img.currentSrc || img.src },
    masthead: { bg: cs.backgroundColor, x: rr.x, y: rr.y, w: rr.width, h: rr.height },
    bodyBg: getComputedStyle(document.body).backgroundColor,
    // a control patch of bare page ground well clear of the logo, same band
    control: { x: Math.round(rr.x + rr.width / 2), y: Math.round(r.y + r.height / 2) }
  };
})()`);

const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
fs.mkdirSync(OUT, { recursive: true });
fs.writeFileSync(OUT + "/shot-" + WIDTH + ".png", Buffer.from(shot.data, "base64"));
fs.writeFileSync(OUT + "/geo-" + WIDTH + ".json", JSON.stringify(geo, null, 1));
console.log(JSON.stringify(geo, null, 1));
ws.close();
await fetch(CDP + "/json/close/" + t.id);
