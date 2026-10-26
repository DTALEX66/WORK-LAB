// 2026-10-26 E1 · 主题控件的诚实声明。
// 实测事实（2026-10-25，本轮复验仍然成立）：?theme=light 确实写进 html.class，
// 但 src/daily/DailyApp.tsx / HudDaily.tsx / DailyChrome.tsx 里 `var(--` 出现 0 次、色值写死，
// 所以窄窗截图在两个主题下逐字节相同（md5 3f53ee67…）。owner 本轮决定：如实说明，不假装切换；
// 令牌单源是后续项 WUI-03，浅色配色还没接入本视图。
// 测试两侧都钉：日常/HUD 表面必须带这句话；专业投影壳的主题控件必须不带它
// ——只测一边，就等于允许把免责声明盖满整个产品。
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, cleanup, act, fireEvent } from '@testing-library/react'

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>()
  // 本文件测的是「主题这句话怎么说」，与快照内容无关：给空快照，两侧表面都按无数据处理。
  return { ...actual, useLiveSnapshot: () => ({ snap: null, source: 'stale', live: false, error: null, dataUpdatedAt: 0 }) }
})

vi.mock('@/lib/repairPack', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/repairPack')>()
  return { ...actual, makeHttpRepairPackReader: () => async () => ({ kind: 'UNREACHABLE' as const, detail: '测试环境不读取' }) }
})

vi.mock('@/daily/solutionsClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/daily/solutionsClient')>()
  return { ...actual, fetchSolutions: async () => ({ kind: 'UNREACHABLE' as const, detail: '测试环境不读取' }) }
})

import App from '@/App'
import { HudDaily } from '@/daily/HudDaily'
import { THEME_HONESTY_ID_DAILY, THEME_HONESTY_ID_HUD } from '@/daily/DailyChrome'

const NOTE = '[data-testid="theme-honesty-note"]'

function setUrl(search: string) {
  window.history.replaceState(null, '', `/index.html${search}`)
}
function notes(): Element[] {
  return Array.from(document.querySelectorAll(NOTE))
}

beforeEach(() => { setUrl('?shell=daily&dv=settings') })
afterEach(() => {
  cleanup()
  window.history.replaceState(null, '', window.location.pathname)
})

describe('E1 · 日常壳的主题控件带诚实声明', () => {
  it('声明是画在屏幕上的文字，不是 hover 才出现的信息', async () => {
    const { container } = render(<App />)
    await act(async () => { await Promise.resolve() })
    const daily = notes()
    expect(daily).toHaveLength(1)
    const note = daily[0] as HTMLElement
    expect(note.getAttribute('data-surface')).toBe('daily')
    expect(note.getAttribute('id')).toBe(THEME_HONESTY_ID_DAILY)
    expect(note.getAttribute('data-theme-honesty')).toBe('not-applied')
    // 没有任何 mouseover/focus 被派发过，文字就已经在 DOM 里。
    expect((note.textContent ?? '').trim().length).toBeGreaterThan(0)
    expect(container.querySelector('#daily-content')).toBeTruthy()
  })

  it('键盘可达：声明本身可聚焦，不靠悬停；主题控件用 aria-describedby 指向它', async () => {
    render(<App />)
    await act(async () => { await Promise.resolve() })
    const note = screen.getByTestId('theme-honesty-note') as HTMLElement
    expect(note.getAttribute('tabindex')).toBe('0')
    expect(note.getAttribute('role')).toBe('note')
    note.focus()
    expect(document.activeElement).toBe(note)

    const control = screen.getByTestId('daily-theme-toggle')
    expect(control.getAttribute('aria-describedby')).toBe(THEME_HONESTY_ID_DAILY)
    // 说明目标必须真的存在，否则 aria-describedby 是一句空话。
    expect(document.getElementById(THEME_HONESTY_ID_DAILY)).toBe(note)
    expect((control.getAttribute('title') ?? '')).toContain('这一屏暂时不随之换色')
    // 悬停不是唯一通道：不派发任何鼠标事件也能拿到这句话。
    expect(note.getAttribute('title')).toContain('专业投影壳')
  })

  it('措辞：不承认没发生的切换，也不把整个产品说成只有深色', () => {
    render(<App />)
    const text = (screen.getByTestId('theme-honesty-note').textContent ?? '')
    // 本表面的事实：参数改了，这一屏不换色。
    expect(text).toContain('只改地址参数 ?theme=')
    expect(text).toContain('不会把本视图变成浅色')
    // 不反向说谎：专业壳确实会换。
    expect(text).toContain('专业投影壳')
    expect(text).toContain('实际生效')
    // 也不把范围夸大到整个产品。
    expect(text).not.toContain('只有深色')
    expect(text).not.toContain('不支持浅色')
    expect(text).toContain('WUI-03')
    // 控件自己的标签只能说「地址值」，不能宣称画面已经是那个颜色。
    const label = screen.getByTestId('daily-theme-toggle').textContent ?? ''
    expect(label).toContain('当前地址值')
    expect(label).not.toBe('浅色（当前）')
  })

  it('地板：这句话用日常壳唯一的 12px 文字档（text-xs），不用更小的字号', () => {
    render(<App />)
    const note = screen.getByTestId('theme-honesty-note')
    expect(note.className).toContain('text-xs')
    expect(note.className).not.toMatch(/text-\[1[01]px\]|text-\[9px\]|text-\[10px\]/)
  })

  it('HUD 窄窗的设置面板带同一句诚实声明（surface=hud）', () => {
    setUrl('?surface=hud')
    render(<HudDaily snap={null} nativeStrip />)
    // 默认不展开设置面板时，窄窗里没有主题控件，也就不该有免责声明占位。
    expect(notes()).toHaveLength(0)
    fireEvent.click(screen.getByLabelText('HUD 设置'))
    const note = screen.getByTestId('theme-honesty-note') as HTMLElement
    expect(note.getAttribute('data-surface')).toBe('hud')
    expect(note.getAttribute('id')).toBe(THEME_HONESTY_ID_HUD)
    expect(note.getAttribute('tabindex')).toBe('0')
    expect((note.textContent ?? '')).toContain('这个窄窗按固定的深色值绘制')
    expect((note.textContent ?? '')).not.toContain('整个应用只有深色')
  })
})

describe('E1 · 专业投影壳的主题控件不带这句话', () => {
  it('专业壳（默认入口）的主题控件存在，且没有任何诚实声明', () => {
    setUrl('')
    render(<App />)
    const control = screen.getByRole('button', { name: /切换到浅色主题/ })
    expect(notes()).toHaveLength(0)
    // 专业壳的 html.class 真的跟着 ?theme= 走（App.behavior.test.tsx 钉着），所以这里不加限定语。
    expect(control.getAttribute('aria-describedby')).toBeNull()
    expect((control.getAttribute('title') ?? '')).toBe('浅色主题')
  })

  it('专业隐私与采集页（?view=privacy）的 data-setting=theme 控件同样不带免责声明', () => {
    setUrl('?view=privacy')
    render(<App />)
    const control = document.querySelector('[data-setting="theme"]')
    expect(control).toBeTruthy()
    expect((control as HTMLElement).textContent).toContain('切到浅色')
    expect(control?.getAttribute('aria-describedby')).toBeNull()
    expect(notes()).toHaveLength(0)
  })

  it('命令面板里的主题动作也不带（只在日常壳说这句话，不盖满产品）', () => {
    setUrl('')
    render(<App />)
    expect(notes()).toHaveLength(0)
    expect(document.querySelector('[data-testid="daily-theme-toggle"]')).toBeNull()
  })
})
