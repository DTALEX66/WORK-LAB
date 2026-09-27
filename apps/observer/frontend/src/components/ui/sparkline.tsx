// L10 (2026-09-27): B10 `.spark` sparkline — SVG polyline with the
// primary->secondary gradient stroke. Values are the caller's truth; a
// missing series renders nothing (honest UNKNOWN, no fabricated trend).
import { cn } from '@/lib/utils'

export interface SparklineProps {
  /** 0..100 series; null/undefined/empty -> empty placeholder, no fake data */
  values?: Array<number | null>
  height?: number
  className?: string
}

export function Sparkline({ values, height = 120, className }: SparklineProps) {
  const pts = (values ?? []).filter((v): v is number => v != null)
  return (
    <div className={cn('w-full', className)} style={{ height }} aria-hidden={pts.length === 0}>
      {pts.length > 1 ? (
        <svg className="spark w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
          <defs>
            <linearGradient id="wl-spark-grad" x1="0" x2="1">
              <stop offset="0%" stopColor="rgb(var(--primary-rgb))" />
              <stop offset="100%" stopColor="rgb(var(--secondary-rgb))" />
            </linearGradient>
          </defs>
          <polyline
            points={pts
              .map(
                (v, i) =>
                  `${(i * (100 / (pts.length - 1))).toFixed(1)},${(100 - Math.max(0, Math.min(100, v))).toFixed(1)}`,
              )
              .join(' ')}
            fill="none"
            stroke="url(#wl-spark-grad)"
            strokeWidth="3.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      ) : (
        <div className="h-full w-full grid place-items-center text-[11px] text-muted">
          无趋势数据（UNKNOWN）
        </div>
      )}
    </div>
  )
}
