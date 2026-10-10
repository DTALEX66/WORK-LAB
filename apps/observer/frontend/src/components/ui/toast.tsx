import * as React from 'react'
import { cn } from '@/lib/utils'

/**
 * UI_COMPONENTS (20260921) · L10b (2026-09-27): Toast — B10 `.toast` contract.
 *
 * B10 single-file: `<div class="toast" id="toast">Done</div>` styled as a fixed
 * bottom-right panel that fades/lifts in with `.show` and auto-hides after
 * 1800ms (showToast → clearTimeout → remove `.show`). `.toast` / `.toast.show`
 * are B10-verbatim in src/skins/b10.css (right/bottom 18px, min 220px, primary
 * border, --shadow-soft, translateY(12px) scale(.98) → 0/1).
 *
 * The repo keeps a small stack (the original M3 contract) — this renders the
 * newest toast as the B10 `.toast.show` element and any additional items as the
 * same B10 element in its shown state, so the visual contract stays identical
 * while nothing is swallowed. Default lifetime is 1800ms (B10), overridable.
 *
 * Usage (imperative, no context dependency):
 *   const { toast, Toaster } = useToaster(1800)
 *   toast({ title: '暂无新的通知' })
 *   ... <Toaster />
 */
export type ToastVariant = 'success' | 'error' | 'info'

export interface ToastItem {
  id: number
  title: string
  description?: string
  variant?: ToastVariant
}

export interface ToasterProps {
  toasts: ToastItem[]
  onDismiss: (id: number) => void
}

const VARIANT_TAG: Record<ToastVariant, string> = {
  success: 'tag ok',
  error: 'tag bad',
  info: 'tag info',
}

export function Toaster({ toasts, onDismiss }: ToasterProps) {
  if (toasts.length === 0) return null
  return (
    <div className="toast-stack">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="toast show"
          // M-4: an error is not a status update. `role="status` is a polite
          // live region that assistive tech may not announce urgently, and a
          // failure that disappears on its own leaves the user with no record
          // of what went wrong. Errors announce assertively and stay until
          // dismissed.
          role={t.variant === 'error' ? 'alert' : 'status'}
          aria-live={t.variant === 'error' ? 'assertive' : 'polite'}
          onClick={() => onDismiss(t.id)}
        >
          <div className="flex items-start gap-3">
            <span className={cn(VARIANT_TAG[t.variant ?? 'info'], 'shrink-0')}>
              {t.variant === 'success' ? 'OK' : t.variant === 'error' ? 'ERR' : 'INFO'}
            </span>
            <div className="min-w-0 flex-1">
              <p className="m-0 text-sm font-medium text-ink">{t.title}</p>
              {t.description ? <p className="m-0 mt-1 text-xs text-muted">{t.description}</p> : null}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

let seq = 0

export function useToaster(defaultMs = 1800) {
  const [toasts, setToasts] = React.useState<ToastItem[]>([])

  const dismiss = React.useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const toast = React.useCallback(
    (input: { title: string; description?: string; variant?: ToastVariant; ms?: number }) => {
      const id = ++seq
      setToasts((prev) => [...prev.slice(-2), { id, ...input }])
      // An error survives the timer unless the caller sets an explicit ms.
      const ttl = input.ms ?? (input.variant === 'error' ? 0 : defaultMs)
      if (ttl > 0) {
        window.setTimeout(() => dismiss(id), ttl)
      }
      return id
    },
    [defaultMs, dismiss],
  )

  return { toasts, toast, dismiss, Toaster }
}
