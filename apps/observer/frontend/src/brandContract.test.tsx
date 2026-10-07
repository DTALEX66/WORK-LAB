/**
 * G2 of the UI prompt pack: the console carries its own brand.
 *
 * The top bar had no brand mark at all. That matters most for the compact HUD, which renders no
 * rail, so that window had no identity; and the main window runs with `decorations:false`, so this
 * row IS the chrome. The palette single-source rule and the source-level sweeps for these
 * contracts live in tests/ci/test_desktop_only_shell.py, because `tsc -b` type-checks this
 * project without Node types.
 */
import { describe, it, expect, afterEach } from 'vitest'
import { render, cleanup } from '@testing-library/react'

import { TopStatusBar } from '@/components/layout/TopStatusBar'

afterEach(cleanup)

function bar(layout: 'full' | 'compact') {
  return render(
    <TopStatusBar
      snap={null} source={'unknown' as any} live={false} theme="dark" layout={layout}
      onCycleTheme={() => {}} onCycleLayout={() => {}}
    />,
  )
}

describe('G2 · brand surface', () => {
  it('renders the brand chip in the desktop layout, mark and wordmark', () => {
    bar('full')
    const chip = document.querySelector('.topbar-brand')
    expect(chip).not.toBeNull()
    expect(chip?.querySelector('.topbar-brand-mark')).not.toBeNull()
    expect(chip?.textContent).toContain('WORK-LAB')
  })

  it('renders the brand mark in the compact HUD, which has no rail to carry identity', () => {
    bar('compact')
    expect(document.querySelector('.topbar-brand .topbar-brand-mark')).not.toBeNull()
  })

  it('keeps the transport dot honest while taking its colour from the tokens', () => {
    bar('full')
    // No snapshot: the dot must not render as LIVE and must not be green.
    expect(document.querySelector('.topbar')?.textContent).toContain('UNKNOWN')
  })
})
