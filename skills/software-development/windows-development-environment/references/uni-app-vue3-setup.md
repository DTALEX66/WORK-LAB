# uni-app Vue 3 (Alpha) Setup on Windows

## Prerequisites

- Hermes-bundled Node v22 (at `AppData/Local/hermes/node/node.exe`)
- Git Bash terminal

## Known-working version pins (2026-06)

```json
{
  "dependencies": {
    "vue": "^3.4.21",
    "pinia": "^2.1.7"
  },
  "devDependencies": {
    "@dcloudio/uni-app": "3.0.0-alpha-1000920260626810",
    "@dcloudio/uni-mp-weixin": "3.0.0-alpha-1000920260626810",
    "@dcloudio/uni-h5": "3.0.0-alpha-1000920260626810",
    "@dcloudio/vite-plugin-uni": "3.0.0-alpha-5010420260626001",
    "@dcloudio/types": "^3.4.31",
    "typescript": "^5.4.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-vue": "^5.0.0"
  }
}
```

Note: The `@vue3` dist-tag on `@dcloudio/vite-plugin-uni` points to an incompatible old version. Use the explicit alpha version `3.0.0-alpha-5010420260626001` which matches the uni-app 3.0.0-alpha-10009 series.

## Installation

```bash
# MUST use --legacy-peer-deps due to alpha peer dep conflicts
npm install --legacy-peer-deps
```

## Required project files

### `index.html` (H5 build entry)
```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>App</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

### `vite.config.ts`
```ts
import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'
import path from 'path'

export default defineConfig({
  plugins: [uni()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
})
```

## uni-app Vue 3 import rules

| Symbol | Import from | Notes |
|--------|-------------|-------|
| `ref`, `computed`, `reactive` | `'vue'` | Standard Vue 3 |
| `onShow`, `onLoad`, `onHide` | `'@dcloudio/uni-app'` | NOT from vue |
| `getCurrentPages` | **Global** | Do NOT import — it's a global like `wx` |
| `navigateTo`, `showToast` | **Global** via `uni.xxx` | Or import from `@dcloudio/uni-app` |
| `defineStore` | `'pinia'` | Standard Pinia |

## Build commands

```bash
npm run dev:h5          # H5 dev server
npm run build:h5        # H5 production build
npm run dev:mp-weixin   # WeChat mini-program dev
```

## Common build errors & fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Could not resolve entry module "index.html"` | Missing `index.html` at project root | Create `index.html` |
| `"onShow" is not exported by "vue"` | Importing uni-app lifecycle from wrong package | Import from `@dcloudio/uni-app` |
| `"getCurrentPages" is not exported` | Trying to import `getCurrentPages` | Use as global, do not import |
| `Cannot find module 'vite'` | Missing peer dep | `npm install vite@^5.0.0` |
| `Cannot find module '@vitejs/plugin-vue'` | Missing peer dep | `npm install @vitejs/plugin-vue` |
| `No matching version found for @dcloudio/uni-cli-shared@^3.0.0` | Wrong vite-plugin-uni version | Pin to `3.0.0-alpha-5010420260626001` |
| `Error [ERR_MODULE_NOT_FOUND]: entry-server.js` | Mismatched vite-plugin-uni / uni-app versions | Pin both to matching alpha dates |

## Cross-platform API calls (uni.request vs fetch)

In uni-app, always use `uni.request()` instead of `fetch()` for API calls:

```typescript
// ✅ WORKS on H5 + WeChat mini-program
const res = await new Promise<any>((resolve, reject) => {
  uni.request({
    url: 'https://api.example.com/data',
    method: 'GET',
    header: { 'Content-Type': 'application/json' },
    timeout: 15000,
    success: (r) => resolve(r),
    fail: (e) => reject(e),
  })
})

// ❌ fetch() works on H5 but NOT on WeChat mini-program
// const res = await fetch(url)
```

**Key differences from `fetch`:**
| fetch | uni.request |
|-------|-------------|
| `res.ok` | `res.statusCode < 400` |
| `res.json()` | `res.data` (already parsed) |
| `headers` (lowercase) | `header` (older name, kept for compat) |
| `body: JSON.stringify(data)` | `data: obj` (auto-serialized for JSON header) |
| `AbortController` timeout | `timeout` option (milliseconds) |
| `catch(e).message` | `catch(e).errMsg` |
