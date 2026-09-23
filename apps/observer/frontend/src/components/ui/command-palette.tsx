import * as React from 'react'
import { cn } from '@/lib/utils'

/**
 * UI_COMPONENTS (20260921): CommandPalette — L6 keyboard authority
 * (Ctrl/Cmd+K opens, Esc closes, arrow keys navigate, Enter runs the item,
 * fuzzy filter is a simple case-insensitive `includes`). No dependencies.
 * role=dialog + aria. Controlled: parent owns `open` / `onClose` + items.
 */
export interface PaletteItem {
  id: string
  label: string
  icon?: React.ComponentType<{ className?: string }>
  group?: string
  run: () => void
}

export interface CommandPaletteProps {
  open: boolean
  onClose: () => void
  items: PaletteItem[]
  placeholder?: string
  /** optional heading shown above the list */
  title?: string
}

function filterItems(items: PaletteItem[], query: string): PaletteItem[] {
  const q = query.trim().toLowerCase()
  if (!q) return items
  return items.filter(
    (it) => it.label.toLowerCase().includes(q) || (it.group ?? '').toLowerCase().includes(q),
  )
}

export function CommandPalette({
  open,
  onClose,
  items,
  placeholder = '搜索页面 / 命令 / 资源…',
  title,
}: CommandPaletteProps) {
  const [query, setQuery] = React.useState('')
  const [active, setActive] = React.useState(0)
  const inputRef = React.useRef<HTMLInputElement>(null)

  const visible = React.useMemo(() => filterItems(items, query), [items, query])

  // reset + focus on open
  React.useEffect(() => {
    if (open) {
      setQuery('')
      setActive(0)
      inputRef.current?.focus()
    }
  }, [open])

  const runItem = (idx: number) => {
    const it = visible[idx]
    if (!it) return
    it.run()
    onClose()
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault()
      onClose()
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActive((a) => Math.min(a + 1, visible.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive((a) => Math.max(a - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      runItem(active)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[70] flex items-start justify-center pt-[12vh]">
      <div className="ui-backdrop absolute inset-0 bg-black/[0.62]" aria-hidden="true" onClick={onClose} />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="命令面板"
        className={cn(
          'ui-modal-panel relative z-10 w-full max-w-xl mx-4 panel card-shadow overflow-hidden',
        )}
        onKeyDown={onKeyDown}
      >
        <div className="flex items-center gap-2 border-b border-border px-3 py-2.5">
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setActive(0)
            }}
            placeholder={placeholder}
            aria-label={placeholder}
            className="h-9 w-full rounded-md bg-panel2 px-3 text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <kbd className="hidden shrink-0 rounded border border-border bg-panel2 px-1.5 py-0.5 text-[10px] text-muted sm:inline">
            Esc
          </kbd>
        </div>
        {title ? <div className="px-3 pt-2 text-[11px] font-medium uppercase tracking-wide text-muted">{title}</div> : null}
        <ul className="max-h-80 overflow-y-auto p-2" aria-label="命令列表">
          {visible.length === 0 ? (
            <li className="px-2 py-6 text-center text-xs text-muted">没有匹配结果</li>
          ) : (
            visible.map((it, i) => {
              const Icon = it.icon
              const activeNow = i === active
              return (
                <li key={it.id}>
                  <button
                    type="button"
                    onMouseEnter={() => setActive(i)}
                    onClick={() => runItem(i)}
                    className={cn(
                      'flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left text-sm transition-colors duration-fast',
                      activeNow ? 'bg-primary/15 text-ink' : 'text-ink hover:bg-panel2',
                    )}
                    aria-current={activeNow ? 'true' : undefined}
                  >
                    {Icon ? <Icon className="h-4 w-4 shrink-0 text-secondary" aria-hidden="true" /> : null}
                    <span className="flex-1 truncate">{it.label}</span>
                    {it.group ? <span className="shrink-0 text-[10px] uppercase tracking-wide text-muted">{it.group}</span> : null}
                  </button>
                </li>
              )
            })
          )}
        </ul>
      </div>
    </div>
  )
}
