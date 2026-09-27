import * as React from 'react'
import { cn } from '@/lib/utils'

/**
 * UI_COMPONENTS (20260921) · L10b (2026-09-27): Drawer — L6 authority: 280ms
 * cubic-bezier(0.2,0,0,1) slide from the right, Esc closes, aria-modal.
 *
 * L10b: the panel is the verbatim B10 `.drawer` element (fixed to the right,
 * translate via `right:-540px` → `right:0` on `.open`, 24px padding, primary
 * left border, --shadow). B10 has no backdrop for the drawer, so the component
 * adds a transparent click-catcher only (no new visual layer) to keep the
 * existing click-outside-to-close behavior.
 */
export interface DrawerProps {
  open: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  side?: 'right' | 'left'
  className?: string
}

export function Drawer({ open, onClose, title, children, side = 'right', className }: DrawerProps) {
  React.useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  // L10b: B10 slides the `.drawer` in/out with `.open`. The repo contract is
  // "closed drawer renders nothing" (so its content never duplicates page
  // text), so the element is mounted only while open.
  if (!open) return null

  return (
    <>
      <div
        className="fixed inset-0"
        style={{ zIndex: 87, background: 'transparent' }}
        aria-hidden="true"
        onClick={onClose}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cn('drawer', 'open', className)}
        style={side === 'left' ? { right: 'auto', left: 0 } : undefined}
      >
        <h3 className="m-0 mb-2">{title}</h3>
        <div className="text-sm text-ink">{children}</div>
      </aside>
    </>
  )
}
