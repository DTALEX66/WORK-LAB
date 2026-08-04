import { invoke } from '@tauri-apps/api/core';
import './style.css';

const app = document.querySelector('#app');
const state = { loading: false, timer: null, started: false, baseline: null, current: null, mode: 'live', sourceKey: '' };
const nf = new Intl.NumberFormat('en-US');
const format = (value) => nf.format(value || 0);
const compact = (value) => new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(value || 0);
const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[char]);

app.innerHTML = `
  <main class="shell">
    <header class="topbar">
      <div class="brand"><div class="logo">✦</div><div><h1>Hermes Token Monitor</h1><p class="subtitle">Local-first usage observability · GPT / DeepSeek / Kimi</p></div></div>
      <div class="status"><i class="dot" id="status-dot"></i><span id="status-text">准备就绪</span></div>
    </header>
    <section class="sourcebar"><label for="source">数据源</label><input id="source" spellcheck="false" placeholder="多个目录用分号分隔：Codex;Router logs;session logs" /><button class="secondary" id="view-mode">历史累计</button><button class="secondary" id="refresh">刷新</button><button class="primary" id="scan">开始监控</button></section>
    <section class="grid" id="metrics"></section>
    <section class="provider-grid" id="providers"></section>
    <section class="section"><div class="section-head"><h2>Token 趋势</h2><span class="section-note" id="trend-note">等待监控</span></div><div class="chart" id="chart"></div></section>
    <section class="section"><div class="section-head"><h2>模型用量</h2><span class="section-note">只显示明确 usage</span></div><div id="models"></div></section>
    <div id="notice"></div>
    <footer class="footer"><span id="footer-status">未读取任何文件</span><span>不读取凭据 · 不上传日志 · 不做字符估算 · 3 秒自动刷新</span></footer>
  </main>`;

const source = document.querySelector('#source');
const metrics = document.querySelector('#metrics');
const providers = document.querySelector('#providers');
const chart = document.querySelector('#chart');
const models = document.querySelector('#models');
const notice = document.querySelector('#notice');
const statusText = document.querySelector('#status-text');
const statusDot = document.querySelector('#status-dot');
const footerStatus = document.querySelector('#footer-status');

function metric(title, value, meta, color) {
  return `<article class="card"><div class="card-title">${title}<span class="${color}">●</span></div><div class="card-value ${color}">${value}</div><div class="card-meta">${meta}</div></article>`;
}
function providerCard(item, max) {
  const color = item.provider === 'DeepSeek' ? 'accent-cyan' : item.provider === 'Kimi' ? 'accent-orange' : item.provider === 'GPT / Codex' ? 'accent-purple' : 'accent-green';
  return `<article class="provider-card"><div class="provider-head"><span class="provider-name"><i class="provider-dot ${color}"></i>${escapeHtml(item.provider)}</span><span class="provider-requests">${format(item.requests)} requests</span></div><div class="provider-total ${color}">${compact(item.total_tokens)}</div><div class="provider-breakdown"><span>输入 ${format(item.input_tokens)}</span><span>输出 ${format(item.output_tokens)}</span></div><div class="provider-progress"><i class="${color}" style="width:${Math.max(2, item.total_tokens / max * 100)}%"></i></div></article>`;
}
function subtractList(current, baseline, key) {
  const identity = typeof key === 'function' ? key : (item) => item[key];
  const old = new Map((baseline || []).map((item) => [identity(item), item]));
  return (current || []).map((item) => {
    const previous = old.get(identity(item)) || {};
    return {
      ...item,
      input_tokens: Math.max(0, (item.input_tokens || 0) - (previous.input_tokens || 0)),
      output_tokens: Math.max(0, (item.output_tokens || 0) - (previous.output_tokens || 0)),
      cached_input_tokens: Math.max(0, (item.cached_input_tokens || 0) - (previous.cached_input_tokens || 0)),
      reasoning_tokens: Math.max(0, (item.reasoning_tokens || 0) - (previous.reasoning_tokens || 0)),
      total_tokens: Math.max(0, (item.total_tokens || 0) - (previous.total_tokens || 0)),
      requests: Math.max(0, (item.requests || 0) - (previous.requests || 0)),
    };
  }).filter((item) => item.total_tokens > 0 || item.requests > 0);
}
function liveSnapshot(snapshot) {
  if (!state.baseline || state.baseline === snapshot) return { ...snapshot, providers: [], models: [], days: [], input_tokens: 0, output_tokens: 0, cached_input_tokens: 0, reasoning_tokens: 0, total_tokens: 0, recognized_requests: 0, notice: '监控已启动；当前面板只显示启动后的新增 usage。切换“历史累计”可查看数据源全部历史。' };
  return {
    ...snapshot,
    input_tokens: Math.max(0, snapshot.input_tokens - state.baseline.input_tokens),
    output_tokens: Math.max(0, snapshot.output_tokens - state.baseline.output_tokens),
    cached_input_tokens: Math.max(0, snapshot.cached_input_tokens - state.baseline.cached_input_tokens),
    reasoning_tokens: Math.max(0, snapshot.reasoning_tokens - state.baseline.reasoning_tokens),
    total_tokens: Math.max(0, snapshot.total_tokens - state.baseline.total_tokens),
    recognized_requests: Math.max(0, snapshot.recognized_requests - state.baseline.recognized_requests),
    providers: subtractList(snapshot.providers, state.baseline.providers, 'provider'),
    models: subtractList(snapshot.models, state.baseline.models, (item) => `${item.provider}::${item.model}`),
    days: subtractList(snapshot.days, state.baseline.days, 'day'),
    notice: snapshot.notice,
  };
}
function sourceRotated(snapshot) {
  const previous = state.baseline?.file_sizes || {};
  const current = snapshot.file_sizes || {};
  return Object.entries(previous).some(([path, size]) => current[path] === undefined || current[path] < size);
}
function render(snapshot) {
  const exact = snapshot.confidence === 'exact' && snapshot.recognized_requests > 0;
  statusText.textContent = exact ? 'LIVE · EXACT USAGE' : 'LIVE · NO USAGE FOUND';
  statusDot.classList.toggle('live', exact);
  metrics.innerHTML = [
    metric('总 Tokens', compact(snapshot.total_tokens), `${format(snapshot.recognized_requests)} 个 usage 记录`, 'accent-purple'),
    metric('输入 Tokens', compact(snapshot.input_tokens), `缓存输入 ${compact(snapshot.cached_input_tokens)}`, 'accent-cyan'),
    metric('输出 Tokens', compact(snapshot.output_tokens), `Reasoning ${compact(snapshot.reasoning_tokens)}`, 'accent-green'),
    metric('扫描文件', format(snapshot.scanned_files), `未识别 ${format(snapshot.unknown_records)} 条`, 'accent-orange'),
  ].join('');
  const providerItems = snapshot.providers || [];
  if (!providerItems.length) {
    providers.innerHTML = '<div class="provider-empty"><strong>GPT / DeepSeek / Kimi 尚未发现 usage</strong><span>请把包含明确 usage 字段的 session 或 Router JSONL 目录填入数据源。</span></div>';
  } else {
    const max = Math.max(...providerItems.map((item) => item.total_tokens), 1);
    providers.innerHTML = providerItems.map((item) => providerCard(item, max)).join('');
  }
  const days = snapshot.days || [];
  document.querySelector('#trend-note').textContent = days.length ? `${days.length} 天 · ${exact ? '明确记录' : '未知'}` : '暂无数据';
  if (!days.length || !snapshot.total_tokens) {
    chart.innerHTML = '<div class="empty" style="width:100%"><div><strong>暂无可绘制的 usage 趋势</strong><span>只认 prompt_tokens / input_tokens / completion_tokens / output_tokens / total_tokens。</span></div></div>';
  } else {
    const max = Math.max(...days.map((day) => day.total_tokens), 1);
    chart.innerHTML = days.slice(-14).map((day) => `<div class="bar-wrap"><div class="bar" style="height:${Math.max(4, day.total_tokens / max * 125)}px" title="${format(day.total_tokens)} tokens"></div><div class="bar-label">${escapeHtml(day.day.slice(5))}</div></div>`).join('');
  }
  const modelItems = snapshot.models || [];
  if (!modelItems.length) {
    models.innerHTML = '<div class="empty"><div><strong>没有明确模型 usage</strong><span>当前数据源可能是 workflow 日志，而不是模型 session 日志。</span></div></div>';
  } else {
    const max = Math.max(...modelItems.map((model) => model.total_tokens), 1);
    models.innerHTML = `<table class="table"><thead><tr><th>Provider</th><th>模型</th><th>请求</th><th>输入</th><th>输出</th><th>总量</th><th>占比</th></tr></thead><tbody>${modelItems.map((model) => `<tr><td><span class="provider-tag">${escapeHtml(model.provider)}</span></td><td><div class="model-cell"><span class="model-icon">AI</span>${escapeHtml(model.model)}</div></td><td>${format(model.requests)}</td><td>${format(model.input_tokens)}</td><td>${format(model.output_tokens)}</td><td><b>${format(model.total_tokens)}</b></td><td><div class="progress"><i style="width:${model.total_tokens / max * 100}%"></i></div></td></tr>`).join('')}</tbody></table>`;
  }
  notice.innerHTML = snapshot.notice ? `<div class="notice">${escapeHtml(snapshot.notice)}</div>` : '';
  footerStatus.textContent = `${escapeHtml(snapshot.source)} · ${format(snapshot.scanned_files)} files · ${new Date().toLocaleTimeString()} 刷新完成`;
}
async function scan() {
  if (state.loading || !source.value.trim()) return;
  state.loading = true; statusText.textContent = 'SCANNING'; statusDot.classList.remove('live');
  document.querySelector('#scan').textContent = '扫描中…';
  try {
    if (state.sourceKey !== source.value.trim()) {
      state.sourceKey = source.value.trim();
      state.baseline = null;
      state.current = null;
    }
    const snapshot = await invoke('scan_usage', { source: source.value });
    if (state.baseline && sourceRotated(snapshot)) {
      state.current = snapshot;
      if (state.timer) clearInterval(state.timer);
      state.timer = null;
      state.started = false;
      render(snapshot);
      statusText.textContent = 'SOURCE ROTATED · RESTART MONITOR';
      statusDot.classList.remove('live');
      notice.innerHTML = '<div class="notice">检测到数据源截断、轮转或文件替换。为避免把历史数据误报为实时 usage，监控已暂停；请重新点击“开始监控”建立新基线。</div>';
      return;
    }
    if (!state.baseline) state.baseline = snapshot;
    state.current = snapshot;
    render(state.mode === 'history' ? snapshot : liveSnapshot(snapshot));
    state.started = true;
    if (!state.timer) state.timer = setInterval(scan, 3000);
  } catch (error) {
    notice.innerHTML = `<div class="notice">${escapeHtml(error)}</div>`;
    statusText.textContent = 'SOURCE ERROR'; footerStatus.textContent = '数据源不可用';
  } finally { state.loading = false; document.querySelector('#scan').textContent = state.started ? '停止监控' : '开始监控'; }
}
function stopMonitoring() {
  if (state.timer) clearInterval(state.timer);
  state.timer = null;
  state.started = false;
  statusText.textContent = '已暂停';
  statusDot.classList.remove('live');
  document.querySelector('#scan').textContent = '开始监控';
}
async function toggleMonitoring() {
  if (state.started) { stopMonitoring(); return; }
  state.baseline = null;
  state.current = null;
  await scan();
}
document.querySelector('#scan').addEventListener('click', toggleMonitoring);
document.querySelector('#refresh').addEventListener('click', async () => {
  if (!state.started) {
    notice.innerHTML = '<div class="notice">请先点击“开始监控”；刷新不会在后台静默读取数据源。</div>';
    return;
  }
  await scan();
});
document.querySelector('#view-mode').addEventListener('click', () => {
  state.mode = state.mode === 'live' ? 'history' : 'live';
  document.querySelector('#view-mode').textContent = state.mode === 'live' ? '历史累计' : '本次新增';
  if (state.current) render(state.mode === 'history' ? state.current : liveSnapshot(state.current));
});
try { source.value = await invoke('default_source'); } catch { source.value = '%USERPROFILE%\\.codex\\sessions'; }
metrics.innerHTML = metric('总 Tokens', '—', '点击开始监控读取本地 session', 'accent-purple') + metric('输入 Tokens', '—', '明确 usage 才会显示', 'accent-cyan') + metric('输出 Tokens', '—', '未知不会被估算', 'accent-green') + metric('扫描文件', '—', '默认不自动读取', 'accent-orange');
providers.innerHTML = '<div class="provider-empty"><strong>当前监控等待新的 usage</strong><span>启动后只显示新增调用；点击“历史累计”查看数据源中已有的 GPT / DeepSeek / Kimi 记录。</span></div>';
