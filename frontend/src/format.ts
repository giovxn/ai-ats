// Display helpers for dates and durations. Intl handles plurals ("1 year", "2 years").

const monthYear = new Intl.DateTimeFormat('en', { month: 'short', year: 'numeric' })
const years = new Intl.NumberFormat('en', { style: 'unit', unit: 'year', unitDisplay: 'long', maximumFractionDigits: 1 })
const wholeYears = new Intl.NumberFormat('en', { style: 'unit', unit: 'year', unitDisplay: 'long' })
const months = new Intl.NumberFormat('en', { style: 'unit', unit: 'month', unitDisplay: 'long' })

// "2019-03" -> { year: 2019, month: 3 }; "2019" -> { year: 2019, month: null }
function parse(value: string | null) {
  const match = /^(\d{4})(?:-(\d{1,2}))?$/.exec(value ?? '')
  if (!match) return null
  return { year: Number(match[1]), month: match[2] ? Number(match[2]) : null }
}

// "2019-03" -> "Mar 2019", "2019" -> "2019"
function formatDate(value: string | null): string | null {
  const date = parse(value)
  if (!date) return null
  return date.month ? monthYear.format(new Date(date.year, date.month - 1)) : String(date.year)
}

export function formatPeriod(start: string | null, end: string | null, isCurrent: boolean): string {
  const from = formatDate(start)
  const to = isCurrent ? 'Present' : formatDate(end)
  if (!from && !to) return 'Dates not given'
  return `${from ?? '?'} – ${to ?? '?'}`
}

// How long one job lasted, for the timeline (months counted like cvs.total_years,
// both ends included). Only shown when both dates have a month: "2016 – 2018" could
// be anything from 1 to 3 years, so a number would be a guess.
export function formatDuration(start: string | null, end: string | null, isCurrent: boolean): string | null {
  const from = parse(start)
  const now = new Date()
  const to = isCurrent ? { year: now.getFullYear(), month: now.getMonth() + 1 } : parse(end)
  if (!from?.month || !to?.month) return null
  const total = to.year * 12 + to.month - (from.year * 12 + from.month) + 1
  if (total <= 0) return null
  const y = Math.floor(total / 12)
  const m = total % 12
  return [y && wholeYears.format(y), m && months.format(m)].filter(Boolean).join(' ')
}

// 11.2 -> "11.2 years"
export function formatYears(value: number | null): string | null {
  return value === null ? null : years.format(value)
}
