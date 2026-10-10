// Dependency-free Chrome DevTools Protocol layout probe (Node >= 22: global
// WebSocket + fetch). Screenshots show a symptom; this returns the numbers that
// explain it — grid tracks, rects, computed styles — at an emulated viewport.
//
//   node cdp_layout_probe.mjs [url]
//
// Nothing in the repo can measure layout otherwise: jsdom has no layout engine,
// `--dump-dom --virtual-time-budget` hangs on the app's SSE connection, and the
// in-app browser reports a 0x0 surface.
import { spawn } from 'node:child_process'
import { setTimeout as sleep } from 'node:timers/promises'

const CHROME = 'D:\\All projects\\OS External Configuration\\10-toolchains\\playwright\\chromium_headless_shell-1228\\chrome-headless-shell-win64\\chrome-headless-shell.exe'
const PORT = 9333
const PROFILE = 'D:\\All projects\\WORK-LAB\\.project-local\\runs\\cdp-profile'
const TARGET = process.argv[2] || 'http://127.0.0.1:61912/?view=work&theme=dark&layout=full'
const WIDTHS = [320, 560, 840, 1440]

const MEASURE = `(() => {
  const pick = (sel) => {
    const el = document.querySelector(sel)
    if (!el) return null
    const r = el.getBoundingClientRect()
    const cs = getComputedStyle(el)
    return { sel, x: Math.round(r.x), y: Math.round(r.y),
             w: Math.round(r.width), h: Math.round(r.height),
             display: cs.display, grid: cs.gridTemplateColumns,
             padding: cs.paddingLeft + '/' + cs.paddingRight, flex: cs.flexWrap }
  }
  const sels = ['.app', '.main', '.topbar', '.top-actions', '.search', '.content',
                '.winctl', '.sidebar-slot', '.panel']
  const btns = [...document.querySelectorAll('.top-actions button')].map((b) => {
    const r = b.getBoundingClientRect()
    return { text: b.textContent.trim(), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width) }
  })
  return JSON.stringify({
    viewport: [window.innerWidth, window.innerHeight],
    doc: { scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth },
    nodes: sels.map(pick).filter(Boolean),
    buttons: btns,
    media: { le560: matchMedia('(max-width: 560px)').matches,
             le840: matchMedia('(max-width: 840px)').matches,
             ge841: matchMedia('(min-width: 841px)').matches },
  })
})()`

async function main() {
  const child = spawn(CHROME, [
    '--no-sandbox', '--disable-gpu', `--user-data-dir=${PROFILE}`,
    `--remote-debugging-port=${PORT}`, '--headless=new', 'about:blank',
  ], { stdio: 'ignore' })

  let version = null
  for (let i = 0; i < 60 && !version; i++) {
    await sleep(500)
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/version`, { signal: AbortSignal.timeout(1500) })
      version = await res.json()
    } catch { /* not up yet */ }
  }
  if (!version) { console.log('CDP_UNREACHABLE'); child.kill(); return 2 }

  const ws = new WebSocket(version.webSocketDebuggerUrl)
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej })
  let id = 0
  const waiting = new Map()
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data)
    if (msg.id && waiting.has(msg.id)) { waiting.get(msg.id)(msg); waiting.delete(msg.id) }
    if (msg.method === 'Page.loadEventFired') waiting.get('__load')?.()
  }
  const send = (method, params = {}) => new Promise((res) => {
    const n = ++id
    waiting.set(n, (msg) => res(msg.result ?? msg.error))
    ws.send(JSON.stringify({ id: n, method, params }))
  })
  const waitForLoad = (ms) => new Promise((res) => {
    const timer = setTimeout(res, ms)
    waiting.set('__load', () => { clearTimeout(timer); res() })
  })

  await send('Page.enable')
  await send('Target.createTarget', { url: 'about:blank' })
  const targets = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()
  const page = targets.find((t) => t.type === 'page' && t.webSocketDebuggerUrl)
  if (!page) { console.log('NO_PAGE_TARGET'); ws.close(); child.kill(); return 3 }

  const pws = new WebSocket(page.webSocketDebuggerUrl)
  await new Promise((res, rej) => { pws.onopen = res; pws.onerror = rej })
  let pid = 0
  const pwaiting = new Map()
  pws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data)
    if (msg.id && pwaiting.has(msg.id)) { pwaiting.get(msg.id)(msg.result ?? msg.error); pwaiting.delete(msg.id) }
  }
  const psend = (method, params = {}) => new Promise((res) => {
    const n = ++pid
    pwaiting.set(n, res)
    pws.send(JSON.stringify({ id: n, method, params }))
  })

  await psend('Page.enable')
  await psend('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false })
  await psend('Page.navigate', { url: TARGET })
  await sleep(3500)

  const out = []
  for (const w of WIDTHS) {
    await psend('Emulation.setDeviceMetricsOverride', { width: w, height: 900, deviceScaleFactor: 1, mobile: false })
    await sleep(700)
    const r = await psend('Runtime.evaluate', { expression: MEASURE, returnByValue: true })
    try { out.push(JSON.parse(r.result.value)) } catch { out.push({ width: w, error: JSON.stringify(r).slice(0, 200) }) }
  }
  for (const row of out) {
    console.log(JSON.stringify(row.viewport) + ' scrollW=' + row.doc?.scrollW +
      ' media=' + JSON.stringify(row.media) +
      ' app=' + JSON.stringify(row.nodes?.find(n => n.sel === '.app')?.grid) +
      ' main=' + JSON.stringify(row.nodes?.find(n => n.sel === '.main')?.w) +
      ' topbar=' + JSON.stringify(row.nodes?.find(n => n.sel === '.topbar')?.w))
    for (const n of row.nodes ?? []) console.log('    ' + n.sel + ' x=' + n.x + ' w=' + n.w + ' h=' + n.h + ' display=' + n.display + ' grid=' + n.grid + ' pad=' + n.padding)
    for (const b of row.buttons ?? []) console.log('    btn ' + b.text + ' x=' + b.x + ' y=' + b.y + ' w=' + b.w)
  }
  pws.close(); ws.close(); child.kill()
  return 0
}

main().catch((e) => { console.log('ERROR', e?.message ?? String(e)); return 1 })
