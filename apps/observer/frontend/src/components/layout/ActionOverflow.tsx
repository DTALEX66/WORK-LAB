import { useEffect, useLayoutEffect, useRef, useState } from 'react'

/**
 * The action row's overflow收纳 (UI debt #34).
 *
 * `.top-actions` used to be `flex-wrap: wrap`, so on a narrow window the four controls stacked into a
 * vertical column — measured at 430px the row had 76px of usable width and the buttons simply piled up.
 * That satisfies no published pattern: Fluent's CommandBar keeps a "see more" button and moves primary
 * commands into the secondary area when space runs out, and Carbon's OverflowMenu is the named control
 * for "more options exist but space is constrained". A wrapping column is neither, and it also breaks
 * SCREEN_SPEC's one-row band contract.
 *
 * So the row measures its own children and folds the unpinned tail into a real menu: `aria-expanded` on
 * the trigger, `role="menu"`/`role="menuitem"`, Escape dismisses and returns focus to the trigger, and a
 * click outside closes it. Pinned controls stay visible whatever happens — the theme toggle is how a
 * user gets out of a theme that stops making sense, so it must never be the thing that disappears.
 */

export type ActionDef = {
  key: string
  label: string
  title?: string
  ariaLabel?: string
  /** Optional because the caller's own handlers are optional; a missing one renders an inert control
   *  rather than being papered over with a synthetic no-op. */
  run?: () => void
  /** Kept in the row at every width. */
  pinned?: boolean
}

/** The trigger's own footprint plus the gap before it, so folding leaves room for itself. */
const MORE_FOOTPRINT = 64

export function ActionRow({ actions }: { actions: ActionDef[] }) {
  const rowRef = useRef<HTMLDivElement | null>(null)
  const sizerRef = useRef<HTMLDivElement | null>(null)
  const triggerRef = useRef<HTMLButtonElement | null>(null)
  const menuRef = useRef<HTMLDivElement | null>(null)
  const [visibleCount, setVisibleCount] = useState(actions.length)
  const [open, setOpen] = useState(false)

  useLayoutEffect(() => {
    const row = rowRef.current
    const sizer = sizerRef.current
    if (!row || !sizer) return

    const measure = () => {
      const widths = Array.from(sizer.children).map((child) => (child as HTMLElement).offsetWidth)
      const gap = 8
      const pinned = actions.filter((action) => action.pinned)
      const foldable = actions.filter((action) => !action.pinned)
      const usedByPinned = pinned.reduce((sum, action) => sum + widths[actions.indexOf(action)] + gap, 0)
      const available = row.clientWidth - usedByPinned
      // Decide "does everything fit" BEFORE reserving room for the trigger. Measuring against a width
      // the trigger already consumed is circular: the row folds one control, which shrinks the row,
      // which justifies folding another, and a desktop width that visibly held all four controls ends
      // up hiding one behind an ellipsis nobody asked for.
      const allWidth = foldable.reduce((sum, action) => sum + widths[actions.indexOf(action)] + gap, 0)
      if (allWidth <= available) {
        setVisibleCount(actions.length)
        return
      }
      let used = 0
      let fitted = 0
      for (const action of foldable) {
        const width = widths[actions.indexOf(action)] + gap
        const reserve = fitted + 1 < foldable.length ? MORE_FOOTPRINT : 0
        if (used + width + reserve > available) break
        used += width
        fitted += 1
      }
      setVisibleCount(fitted + pinned.length)
    }

    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(row)
    return () => observer.disconnect()
  }, [actions])

  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false)
        triggerRef.current?.focus()
      }
    }
    const onPointerDown = (event: MouseEvent) => {
      const target = event.target as Node | null
      if (target && !menuRef.current?.contains(target) && target !== triggerRef.current) setOpen(false)
    }
    document.addEventListener('keydown', onKey)
    document.addEventListener('mousedown', onPointerDown)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('mousedown', onPointerDown)
    }
  }, [open])

  const shown = actions.slice(0, visibleCount)
  const folded = actions.slice(visibleCount)

  return (
    <div className="top-actions top-actions-fit" ref={rowRef}>
      {shown.map((action) => (
        <ActionButton key={action.key} action={action} />
      ))}
      {folded.length > 0 && (
        <div className="action-overflow" ref={menuRef}>
          <button
            type="button"
            className="ghost-btn action-more"
            ref={triggerRef}
            aria-expanded={open}
            aria-haspopup="menu"
            aria-label="更多操作"
            title="更多操作"
            onClick={() => setOpen((value) => !value)}
          >
            …
          </button>
          {open && (
            <div className="action-overflow-menu" role="menu">
              {folded.map((action) => (
                <button
                  key={action.key}
                  type="button"
                  role="menuitem"
                  className="action-overflow-item"
                  title={action.title ?? action.label}
                  onClick={() => {
                    setOpen(false)
                    action.run?.()
                  }}
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
      {/* Off-screen sizer: real text, real font, real padding, so the widths above are the widths the
          row will actually need rather than a constant someone guessed. */}
      <div className="action-sizer" aria-hidden="true" ref={sizerRef}>
        {actions.map((action) => (
          <button key={action.key} type="button" className="ghost-btn" tabIndex={-1}>
            {action.label}
          </button>
        ))}
        <button type="button" className="ghost-btn" tabIndex={-1}>
          …
        </button>
      </div>
    </div>
  )
}

function ActionButton({ action }: { action: ActionDef }) {
  return (
    <button
      type="button"
      className="ghost-btn"
      onClick={action.run}
      title={action.title ?? action.label}
      aria-label={action.ariaLabel}
    >
      {action.label}
    </button>
  )
}
