# Web Game Dev Patterns (Windows + Node 16 + Git Bash)

## When this reference applies

You're building a **vanilla JS / ES module browser game** (no build tool like Vite/Webpack) on Windows, where `which node` resolves to **WeChat DevTools Node v16** (`/d/Program Files (x86)/Tencent/微信web开发者工具/node`).

The game targets `<script type="module">` in the browser — not Node.js — so Node 16's missing APIs (`structuredClone`, `node --test`) are test-only constraints, not runtime bugs.

## Architecture pattern: 4-layer state-machine game

```
gameConfig.js   — 单一平衡配置源（所有数字参数集中于此）
state.js        — 纯状态机（初始/克隆/快照/Tick/失败检测）
actions.js      — 操作系统（修改状态的纯函数）
events.js       — 事件系统（异常/随机事件）
feedback.js     — 反馈系统（日志/色调/UI提示）
audio.js        — 程序化音效（Web Audio API，0外部文件）
game.js         — 游戏循环 + UI绑定
```

### Why config-driven?

- **一个文件调所有平衡** → `gameConfig.js` 改参数即时生效
- **换皮准备** → 换游戏只需换 events.js 的异常事件 + gameConfig.js 的数值
- **不用重启** → 纯前端，刷新即可

## Workflow: 设计先行，每次一个功能

```
1. 写设计文档 (docs/*.md) — 定义目标、状态变更、交互流程、验收标准
2. 实现核心逻辑 (src/*.js) — 纯函数、无副作用
3. 写测试或手动验证
4. 集成 UI (game.js + index.html + styles.css)
5. git commit（单一功能提交）
```

### Rule: 拒绝无任务重构

- 不同时修改无关文件
- 不同时做多个功能
- 先设计再开发

## Testing under Node 16 for browser-targeted ES modules

`node --test` 和 `structuredClone` 在 Node 16 中不存在。

### Polyfill approach (inline verification):

```js
global.structuredClone = obj => JSON.parse(JSON.stringify(obj));
// 局限: 不支持函数、Symbol、Date、循环引用
```

### Better: Use Hermes Node v22 explicitly

```bash
/c/Users/ALEX/AppData/Local/hermes/node/node.exe -e "import('./src/module.js')..."
```

### Module load test (Node 16 compatible)

```js
cd /d/project && node -e "
global.structuredClone = obj => JSON.parse(JSON.stringify(obj));
Promise.all([
  import('./src/state.js'),
  import('./src/actions.js'),
]).then(([s, a]) => {
  console.log('Modules OK');
  // ... assertions
}).catch(e => console.error(e));
"
```

## Web Audio API — procedural sound effects (0 external files)

**Pattern:** Create an `audio.js` module with lazy `AudioContext` initialization.

```js
let ctx = null;
function getContext() {
  if (!ctx) { ctx = new (window.AudioContext || window.webkitAudioContext)(); }
  if (ctx.state === 'suspended') ctx.resume().catch(() => {});
  return ctx;
}
```

### Sound template — beep:

```js
function beep(freq, duration, type = 'square', volume = 0.08) {
  const ac = getContext();
  const osc = ac.createOscillator();
  const gain = ac.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, ac.currentTime);
  gain.gain.setValueAtTime(volume, ac.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + duration);
  osc.connect(gain).connect(ac.destination);
  osc.start(); osc.stop(ac.currentTime + duration);
}
```

### Sound template — sweep (for alarms):

```js
function sweep(startFreq, endFreq, duration, type = 'sawtooth', volume = 0.06) {
  const ac = getContext();
  const osc = ac.createOscillator();
  const gain = ac.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(startFreq, ac.currentTime);
  osc.frequency.exponentialRampToValueAtTime(endFreq, ac.currentTime + duration);
  gain.gain.setValueAtTime(volume, ac.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + duration);
  osc.connect(gain).connect(ac.destination);
  osc.start(); osc.stop(ac.currentTime + duration);
}
```

### Recommended sound mapping:

| Event | Sound | Parameters |
|---|---|---|
| Button click | beep | 800Hz, 0.06s, square |
| Action success | beep | 1000Hz, 0.1s, sine |
| Action fail | beep | 300Hz, 0.18s, sawtooth |
| Anomaly trigger | sweep | 200→80Hz, 0.45s, sawtooth |
| Warning tone | sweep | 600→200Hz, 0.25s, square |
| System crash | sweep | 150→30Hz, 0.8s, sawtooth |
| Ad revive | sweep | 200→1200Hz, 0.5s, sine |
| Restart | double beep | 600→800Hz, 0.08s+0.1s |

## IAA monetization patterns (ad-gated content)

### Pattern 1: Ad revive (失败→复活)

```js
state.adRevivesUsed  // 追踪复活次数
// 回滚到 N 秒前的快照
reviveFromAd(state)  // 从快照恢复状态
```

### Pattern 2: Hidden logs (广告解锁隐藏剧情)

Each anomaly event auto-adds a locked lore entry to state:

```js
// events.js — applyAnomaly 中自动添加
const hidden = HIDDEN_LOGS[id];
if (hidden && !next.hiddenLogs.some(h => h.id === hidden.id)) {
  next.hiddenLogs.push({ ...hidden, locked: true });
}

// actions.js — 广告解码
unlockHiddenLog(state) {
  const locked = state.hiddenLogs.find(h => h.locked);
  // 找到→解锁→adHintsUsed++
}
```

### Pattern 3: Fake ending (连续失败→假结局→广告揭示真相)

```js
// state
consecutiveFailures     // 每次失败+1
fakeEndingTriggered     // >=阈值 → true
fakeEndingUnlocked      // 广告揭示真相后 → true

// 重置条件: 成功值守到倒计时结束
if (state.gameOver && state.remaining <= 0) {
  state.consecutiveFailures = 0;
}
```

### Config structure for IAA parameters:

```js
// gameConfig.js
{
  adRevive: {
    rollbackWindow: 30,
    snapshotInterval: 10,
    maxSnapshots: 12,
  },
  hiddenLogs: {
    maxUnlockedPerRun: 5,
  },
  fakeEnding: {
    consecutiveFailuresThreshold: 5,
    cooldownFailures: 3,
  },
}
```

## Git workflow for this project

```bash
git commit -m "feat: 一句话说明功能"
git push
```

Commit messages 中文描述，每个功能独立提交，不混入无关修改。
