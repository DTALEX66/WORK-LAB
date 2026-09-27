// L10 (2026-09-27): B04/L4 DataTable — unified table surface. B10 `.table`
// density: 12px cell padding, 13px text, muted header, hover row tint,
// density toggle (comfortable 56px / compact 44px row heights, L4 density
// tokens). Empty state is honest (the caller's message, no fake rows).
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export interface DataTableColumn<T> {
  key: string
  header: ReactNode
  cell: (row: T) => ReactNode
  className?: string
  /** column alignment (default left) */
  align?: 'left' | 'right'
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  rows: T[]
  /** stable row key */
  rowKey: (row: T, index: number) => string
  /** honest empty-state body (no fabricated rows) */
  empty?: ReactNode
  className?: string
  /** L4 density: comfortable (56px) | compact (44px) */
  density?: 'comfortable' | 'compact'
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  empty,
  className,
  density = 'comfortable',
}: DataTableProps<T>) {
  const cellPad = density === 'compact' ? 'px-3 py-1.5' : 'px-3 py-3'
  return (
    <div className={cn('wl-table-wrap overflow-x-auto', className)}>
      <table className="w-full border-collapse text-[13px] min-w-[720px]">
        <thead>
          <tr className="text-left">
            {columns.map((c) => (
              <th
                key={c.key}
                className={cn('font-semibold text-muted text-[11px] uppercase tracking-wide border-b border-border/60', cellPad, c.align === 'right' && 'text-right', c.className)}
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-3 py-8 text-center text-xs text-muted">
                {empty ?? '暂无数据（UNKNOWN）'}
              </td>
            </tr>
          ) : (
            rows.map((row, i) => (
              <tr key={rowKey(row, i)} className="border-b border-border/40 last:border-0 transition-colors duration-fast hover:bg-panel2/74">
                {columns.map((c) => (
                  <td
                    key={c.key}
                    className={cn(cellPad, 'align-middle', c.align === 'right' ? 'text-right tabular-nums' : 'text-left', c.className)}
                  >
                    {c.cell(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
