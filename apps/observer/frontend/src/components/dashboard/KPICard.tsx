import { Card } from '@/components/ui/card'

// KPI card — value is the caller's truth. The caller is responsible for
// passing 'UNKNOWN' when there is no data (front-truth discipline, U07):
// a KPI must never render a fabricated 0 for a missing fact.
export function KPICard({ title, value, sub }: { title: string; value: string; sub?: string }) {
  return (
    <Card className="p-4">
      <div className="label">{title}</div>
      <div className="kpi-number mt-2">{value}</div>
      {sub && <div className="text-[10px] text-zinc-500 mt-1">{sub}</div>}
    </Card>
  )
}
