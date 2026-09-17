import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react'
import { Card } from '@/components/ui/card'

interface KPIProps {
  icon: LucideIcon
  label: string
  value: string
  trend?: number
  spark?: number[]
  color: string
}

export function KPICard({ icon: Icon, label, value, trend, spark, color }: KPIProps) {
  const up = (trend ?? 0) >= 0
  const max = spark && spark.length ? Math.max(...spark, 1) : 1
  return (
    <Card className="p-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="label flex items-center gap-1.5">
            <Icon size={13} style={{ color }} /> {label}
          </div>
          <div className="kpi-number mt-2">{value}</div>
        </div>
        {trend !== undefined && (
          <span className={up ? 'text-success' : 'text-error'} style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 2 }}>
            {up ? <TrendingUp size={12} /> : <TrendingDown size={12} />}{Math.abs(trend)}%
          </span>
        )}
      </div>
      {spark && spark.length > 1 && (
        <div className="mt-3 flex items-end gap-[2px]" style={{ height: 28 }}>
          {spark.map((v, i) => (
            <div key={i} className="flex-1 rounded-sm" style={{ height: ((v / max) * 100) + '%', background: color, opacity: 0.5 + (i / spark.length) * 0.5 }} />
          ))}
        </div>
      )}
    </Card>
  )
}
