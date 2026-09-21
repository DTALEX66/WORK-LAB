import * as React from 'react'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * UI_COMPONENTS (20260921): Drawer — L6 authority: 280ms
 * cubic-bezier(0.2,0,0,1) slide, side=right|left, Esc closes, aria-modal.
 * Motion classes (.ui-drawer-right / .ui-drawer-left) live in src/index.css.
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

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex">
      <div
        className="ui-backdrop absolute inset-0 bg-black/[0.62]"
        aria-hidden="true"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cn(
          'ui-drawer relative z-10 flex h-full w-96 max-w-[90vw] flex-col panel card-shadow',
          side === 'right' ? 'ui-drawer-right ml-auto border-l' : 'ui-drawer-left mr-auto border-r',
          className,
        )}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <h2 className="text-base font-semibold text-ink">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="关闭"
            className="rounded-md p-1.5 text-muted hover:text-ink hover:bg-panel2 transition-colors duration-fast focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-4 py-4 text-sm text-ink">{children}</div>
      </div>
    </div>
  )
}
