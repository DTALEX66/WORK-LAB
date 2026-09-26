// Stage-B behavior tests: verify the REAL entry/param/theme/data-source
// contract, not just that a class or a label exists.
//   B2 — the legacy `?view=compact` entry contract actually renders the
//        Compact HUD (data-layout=compact, no sidebar rail); `?view=full`
//        and the canonical `?layout=` param stay full.
//   B3 — theme is projected through the SAME .light + colorScheme contract as
//        the pre-render script in index.html (the CSS has no .dark rule, so a
//        .dark class toggle was a no-op).
//   B4 — the URL write-back preserves the Tauri-injected ?api= data source, so
//        navigation/refresh does not silently fall back to static-preview.
//   B5 — with no snapshot the project KPI is UNKNOWN / "数据源未接入", never a
//        fabricated "0".
// The live-snapshot hook is mocked per-test so none of this depends on a
// running backend (same contract as App.smoke.test.tsx).
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, cleanup, act } from '@testing-library/react'

const mocks = vi.hoisted(() => ({
  live: { snap: null, source: 'stale', live: false, error: null },
}))

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>()
  return {
    ...actual,
    useLiveSnapshot: () => mocks.live,
  }
})

import App from '@/App'

function setUrl(qs: string) {
  window.history.replaceState(null, '', qs || window.location.pathname)
}

beforeEach(() => {
  mocks.live = { snap: null, source: 'stale', live: false, error: null }
})

afterEach(() => {
  cleanup()
  setUrl('')
  document.documentElement.classList.remove('light')
  document.documentElement.style.colorScheme = ''
})

describe('B2 · compact entry contract (?view=full|compact = LAYOUT, not a lane)', () => {
  it('?view=compact renders the Compact HUD, no sidebar rail', async () => {
    setUrl('?view=compact')
    render(<App />)
    await act(async () => {})
    // compact branch sets data-layout=compact and renders the dedicated HUD
    expect(document.querySelector('[data-layout="compact"]')).not.toBeNull()
    // the full-layout sidebar rail must NOT be present in compact
    expect(screen.queryByLabelText('侧边导航')).toBeNull()
  })

  it('the canonical ?layout=compact param also selects Compact', () => {
    setUrl('?layout=compact')
    render(<App />)
    expect(document.querySelector('[data-layout="compact"]')).not.toBeNull()
    expect(screen.queryByLabelText('侧边导航')).toBeNull()
  })

  it('?view=full (main window) keeps the full layout with the rail', () => {
    setUrl('?view=full')
    render(<App />)
    expect(document.querySelector('[data-layout="full"]')).not.toBeNull()
    expect(screen.getByLabelText('侧边导航')).toBeTruthy()
  })

  it('a real lane view under full layout keeps the rail', () => {
    setUrl('?view=monitoring')
    render(<App />)
    expect(document.querySelector('[data-layout="full"]')).not.toBeNull()
    expect(screen.getByLabelText('侧边导航')).toBeTruthy()
  })
})

describe('B3 · theme projected via .light + colorScheme (same as index.html)', () => {
  it('theme=light adds .light and sets colorScheme=light', () => {
    setUrl('?theme=light')
    render(<App />)
    expect(document.documentElement.classList.contains('light')).toBe(true)
    expect(document.documentElement.style.colorScheme).toBe('light')
  })

  it('default dark: no .light class, colorScheme=dark', () => {
    setUrl('')
    render(<App />)
    expect(document.documentElement.classList.contains('light')).toBe(false)
    expect(document.documentElement.style.colorScheme).toBe('dark')
  })
})

describe('B4 · URL write-back preserves the ?api= data source', () => {
  it('navigating does not drop a Tauri-injected ?api= endpoint', async () => {
    const api = 'http://127.0.0.1:61867/api/v1/snapshot'
    setUrl('?api=' + encodeURIComponent(api))
    render(<App />)
    await act(async () => {}) // flush the URL write-back effect
    const kept = new URLSearchParams(window.location.search).get('api')
    expect(kept).toBe(api)
  })

  it('without a ?api= the write-back adds no api param (no fabricated source)', async () => {
    setUrl('')
    render(<App />)
    await act(async () => {})
    expect(new URLSearchParams(window.location.search).get('api')).toBeNull()
  })
})

describe('B5 · no snapshot → UNKNOWN, never a fabricated 0', () => {
  it('every KPI number is UNKNOWN when there is no snapshot', () => {
    mocks.live = { snap: null, source: 'stale', live: false, error: null }
    setUrl('')
    render(<App />)
    // The overview KPI strip: 项目 / 活跃执行 / Token / 数据源. With no snap the
    // three fact KPIs must each read UNKNOWN — the "UNKNOWN ≠ 0" iron law.
    // (项目 used to fabricate "0" via `snap?.projects?.length ?? 0`.)
    const kpis = Array.from(document.querySelectorAll('.kpi-number'))
      .map((el) => el.textContent)
    const factKpis = kpis.slice(0, 3) // 项目 / 活跃执行 / Token
    expect(factKpis).toEqual(['UNKNOWN', 'UNKNOWN', 'UNKNOWN'])
    // and none of the KPIs fabricates a "0"
    expect(kpis).not.toContain('0')
    // multiple honest "no data" indicators (KPI sub + panel empty states)
    expect(screen.getAllByText('数据源未接入').length).toBeGreaterThanOrEqual(1)
  })
})
