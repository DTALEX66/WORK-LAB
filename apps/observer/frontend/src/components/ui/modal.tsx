import * as React from 'react'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * UI_COMPONENTS (20260921): Modal — L6 interaction authority: 220ms open/close
 * (motion-modal), backdrop opacity 0.62, Esc closes, focus moves into the
 * dialog on open and returns to the trigger on close, aria-modal +
 * role=dialog. Renders inline (parent positions it). Motion classes
 * (.ui-modal-panel / .ui-backdrop) live in src/index.css.
 */
export interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  footer?: React.ReactNode
  /** extra classes for the panel (width etc.) */
  className?: string
}

export function Modal({ open, onClose, title, children, footer, className }: ModalProps) {
  const panelRef = React.useRef<HTMLDivElement>(null)
  const previouslyFocused = React.useRef<HTMLElement | null>(null)

  React.useEffect(() => {
    if (!open) return
    previouslyFocused.current = document.activeElement as HTMLElement | null
    panelRef.current?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  // restore focus on close
  React.useEffect(() => {
    if (!open) previouslyFocused.current?.focus?.()
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="ui-backdrop absolute inset-0 bg-black/[0.62]"
        aria-hidden="true"
        onClick={onClose}
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        className={cn(
          'ui-modal-panel relative z-10 w-full max-w-lg mx-4 panel card-shadow overflow-hidden',
          'focus:outline-none',
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
        <div className="px-4 py-4 text-sm text-ink">{children}</div>
        {footer ? <div className="px-4 py-3 border-t border-border flex justify-end gap-2">{footer}</div> : null}
      </div>
    </div>
  )
}
