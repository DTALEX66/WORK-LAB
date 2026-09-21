import * as React from 'react'
import { CheckCircle2, XCircle, Info, X } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * UI_COMPONENTS (20260921): Toast — L6 authority: 4000ms default lifetime,
 * stack gap 12px (gap-3 = 0.75rem), success/error/info variants, top-right
 * stack. Motion class .ui-toast-item lives in src/index.css.
 *
 * Usage (imperative, no context dependency):
 *   const { toast, Toaster } = useToaster()
 *   toast({ title: '已保存', variant: 'success' })
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

const ICONS: Record<ToastVariant, typeof Info> = {
  success: CheckCircle2,
  error: XCircle,
  info: Info,
}

const ICON_COLOR: Record<ToastVariant, string> = {
  success: 'text-success',
  error: 'text-error',
  info: 'text-info',
}

export function Toaster({ toasts, onDismiss }: ToasterProps) {
  return (
    <div
      className="fixed right-4 top-4 z-[60] flex flex-col gap-3"
      role="region"
      aria-label="通知"
      aria-live="polite"
    >
      {toasts.map((t) => {
        const Icon = ICONS[t.variant ?? 'info']
        return (
          <div
            key={t.id}
            className={cn(
              'ui-toast-item panel card-shadow flex items-start gap-3 px-4 py-3 min-w-[260px] max-w-sm',
            )}
            role="status"
          >
            <Icon className={cn('mt-0.5 h-4 w-4 shrink-0', ICON_COLOR[t.variant ?? 'info'])} aria-hidden="true" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-ink">{t.title}</p>
              {t.description ? <p className="mt-0.5 text-xs text-muted">{t.description}</p> : null}
            </div>
            <button
              type="button"
              onClick={() => onDismiss(t.id)}
              aria-label="关闭通知"
              className="rounded p-0.5 text-muted hover:text-ink transition-colors duration-fast focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <X className="h-3.5 w-3.5" aria-hidden="true" />
            </button>
          </div>
        )
      })}
    </div>
  )
}

let seq = 0

export function useToaster(defaultMs = 4000) {
  const [toasts, setToasts] = React.useState<ToastItem[]>([])

  const dismiss = React.useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const toast = React.useCallback(
    (input: { title: string; description?: string; variant?: ToastVariant; ms?: number }) => {
      const id = ++seq
      setToasts((prev) => [...prev, { id, ...input }])
      const ttl = input.ms ?? defaultMs
      if (ttl > 0) {
        window.setTimeout(() => dismiss(id), ttl)
      }
      return id
    },
    [defaultMs, dismiss],
  )

  return { toasts, toast, dismiss, Toaster }
}
