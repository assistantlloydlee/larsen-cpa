// End-to-end contact form test against the published page: fill, submit, capture
// the destination the browser actually reaches.
import fs from "node:fs";
const PORT = process.env.PORT || "9333";
const CDP = "http://127.0.0.1:" + PORT;
const PAGE = process.env.PAGE || "https://assistantlloydlee.github.io/larsen-cpa/contact.html";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const t = await (await fetch(CDP + "/json/new?" + encodeURIComponent("about:blank"), { method: "PUT" })).json();
const ws = new WebSocket(t.webSocketDebuggerUrl);
let id = 0; const pend = new Map(); const nav = [];
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pend.has(d.id)) { const q = pend.get(d.id); pend.delete(d.id); d.error ? q.rej(new Error(JSON.stringify(d.error))) : q.res(d.result); }
  else if (d.method === "Page.frameNavigated") nav.push(d.params.frame.url);
};
await new Promise((r) => { ws.onopen = r; });
const send = (method, params = {}) => { const i = ++id; return new Promise((res, rej) => { pend.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); setTimeout(() => { if (pend.has(i)) { pend.delete(i); rej(new Error("t/o " + method)); } }, 40000); }); };

await send("Page.enable"); await send("Runtime.enable"); await send("Network.enable");
const net = [];
ws.addEventListener("message", (m) => { const d = JSON.parse(m.data); if (d.method === "Network.requestWillBeSent") net.push({ t: "req", url: d.params.request.url }); if (d.method === "Network.responseReceived") net.push({ t: "res", url: d.params.response.url, status: d.params.response.status }); if (d.method === "Network.loadingFailed") net.push({ t: "fail", url: d.params.requestId, err: d.params.errorText }); });
await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
await send("Page.navigate", { url: PAGE });
await sleep(4000);

const fill = `(() => {
  const set = (sel, v) => { const el = document.querySelector(sel); el.focus(); el.value = v;
    el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true})); };
  set('#name', 'End-to-end form test');
  set('#email', 'assistant.lloyd.lee@gmail.com');
  set('#phone', '');
  set('#company', 'Site build verification');
  set('#message', 'Live end-to-end test of the contact form from ${PAGE} submitted on 2026-09-22.');
  const b = document.querySelector('form button[type=submit]');
  b.click();
  return { action: document.querySelector('form').action, clicked: true };
})()`;
const r = await send("Runtime.evaluate", { expression: fill, returnByValue: true });
console.log("form action:", r.result.value.action);

await sleep(9000);
const st = await send("Runtime.evaluate", { expression: `({url: location.href, title: document.title, text: document.body.innerText.replace(/\\s+/g,' ').slice(0,400)})`, returnByValue: true });
console.log("landed:", JSON.stringify(st.result.value, null, 1));
console.log("nav trail:", nav.slice(-3));
console.log("net:", JSON.stringify(net.filter((n) => n.t !== "req" || /formsubmit|github/.test(n.url)).slice(-8), null, 1));
fs.writeFileSync("/tmp/form_test_result.json", JSON.stringify({ action: r.result.value, landed: st.result.value, nav }, null, 1));
ws.close();
await fetch(CDP + "/json/close/" + t.id);
