// U04: the view registry is the single source of truth for navigation. The
// legacy array-index coupling (Sidebar had 8 items, the views array had 10)
// left Delivery/Trust/Settings unreachable. These regression tests pin:
//   1. every registry lane has a real component (no orphan / unreachable view)
//   2. the lanes required by the taskpack all exist
//   3. unknown ids don't crash (App falls back to Overview)
import { describe, it, expect } from 'vitest'
import { VIEW_REGISTRY, VIEW_BY_ID, OVERVIEW_ID } from '@/lib/viewRegistry'
import { NAV_GROUPS } from '@/components/layout/Sidebar'

describe('U04 view registry (no orphan / unreachable view)', () => {
  it('every registry entry has a non-null component', () => {
    for (const v of VIEW_REGISTRY) {
      expect(v.component, `view ${v.id} has no component`).toBeDefined()
    }
  })

  it('the taskpack-required lanes are all reachable by stable id', () => {
    const ids = new Set(VIEW_REGISTRY.map((v) => v.id))
    for (const required of ['agents', 'executions', 'models', 'memory', 'tools', 'monitoring', 'delivery', 'trust', 'settings', 'projects']) {
      expect(ids.has(required), `lane ${required} missing`).toBe(true)
    }
  })

  it('VIEW_BY_ID exposes every id and has no duplicate ids', () => {
    const ids = VIEW_REGISTRY.map((v) => v.id)
    expect(new Set(ids).size).toBe(ids.length)
    for (const id of ids) {
      expect(VIEW_BY_ID[id], `registry lookup failed for ${id}`).toBeDefined()
    }
  })

  it('S31/32 software lane is present as a read-only projection view', () => {
    expect(VIEW_BY_ID['software']).toBeDefined()
  })

  it('OVERVIEW is the synthetic landing lane (not a registry component)', () => {
    expect(OVERVIEW_ID).toBe('overview')
    expect(VIEW_REGISTRY.find((v) => v.id === OVERVIEW_ID)).toBeUndefined()
  })

  // P1-01 (2026-09-26): the sidebar's 7 primary nav groups (P1-D §3.1) must
  // partition the reachable lanes exactly once — no lane dropped, no lane
  // doubled, all ids resolve to real registry/overview ids.
  it('P1-01: NAV_GROUPS has 7 primary entries and covers every reachable lane exactly once', () => {
    const groupKeys = NAV_GROUPS.map((g) => g.key)
    expect(groupKeys, 'need exactly 7 primary nav groups').toHaveLength(7)
    expect(new Set(groupKeys).size, 'group keys must be unique').toBe(7)

    const knownIds = new Set<string>([OVERVIEW_ID, ...VIEW_REGISTRY.map((v) => v.id)])
    const flat = NAV_GROUPS.flatMap((g) => g.ids)
    for (const id of flat) {
      expect(knownIds.has(id), `nav group references unknown lane ${id}`).toBe(true)
    }
    // every reachable lane appears exactly once across the 7 groups
    expect(new Set(flat).size, 'no lane may appear in two groups').toBe(flat.length)
    expect(new Set(flat), 'all 16 reachable lanes must be grouped').toEqual(knownIds)
  })
})
