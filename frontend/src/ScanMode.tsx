// Block 4, Beyond the Scan: go through the New column one candidate at a time.
//
// The card shows what recruiters actually read in a quick scan: the last 2 jobs. When a
// must-have only appears in an older job, the card says so, and rejecting first shows that
// evidence ("Before you reject"). The recruiter always decides; nothing moves by itself.
// Whether evidence is verified and buried is decided by plain code in the backend (evidence.py).
//
// Colour has one meaning each: sage = found in the CV, amber = outside the 2 jobs on this card.
// Every decision here is logged (decisions table); Undo adds a new entry instead of erasing one.

import { useEffect, useRef, useState } from 'react'
import {
  api,
  type Candidate,
  type Decision,
  type DecisionInput,
  type EvidenceStatus,
  type EvidenceTag,
  type Job,
  type Quote,
  type RequirementEvidence,
  type Stage,
} from './api'
import { formatPeriod, formatYears } from './format'

const RECENT_JOBS = 2 // the review window: the last 2 jobs (SME interview), same as evidence.py

const STATUS_LABELS: Record<EvidenceStatus, string> = {
  demonstrated: 'Found',
  partial: 'Partly',
  not_found: 'Not found',
  unverified: 'Unverified',
}

// Shown on hover and read by screen readers, so each word's meaning is never a guess.
const STATUS_HINTS: Record<EvidenceStatus, string> = {
  demonstrated: 'Found in the CV, with a quote checked against the CV text',
  partial: 'Partly shown in the CV, with a quote checked against the CV text',
  not_found: 'Not found in the CV',
  unverified: "The AI found something, but its quote couldn't be matched to the CV text",
}

const TAG_LABELS: Record<EvidenceTag, string> = {
  duty: 'Duty',
  action: 'Action',
  outcome: 'Outcome',
}

const MOVE_LABELS: Record<Stage, string> = {
  new: 'Moved back to New',
  shortlisted: 'Shortlisted',
  interview: 'Moved to Interview',
  rejected: 'Rejected',
}

type Buried = { requirement: RequirementEvidence; quote: Quote; job: Job; jobIndex: number }

// Must-haves whose verified evidence sits only in jobs older than the last 2 (decided by the backend).
// When two must-haves point at the same sentence, the second one shows another older quote if it has one.
function buriedEvidence(candidate: Candidate): Buried[] {
  const used = new Set<string>()
  return (candidate.evidence?.requirements ?? [])
    .filter((requirement) => requirement.buried)
    .flatMap((requirement) => {
      const older = requirement.quotes.filter((q) => q.verified && q.job_index !== null && q.job_index >= RECENT_JOBS)
      const quote = older.find((q) => !used.has(q.text)) ?? older[0]
      if (!quote || quote.job_index === null) return []
      used.add(quote.text)
      return [{ requirement, quote, job: candidate.jobs[quote.job_index], jobIndex: quote.job_index }]
    })
}

// "job 4 of 5 (Mar 2015 – Aug 2018)". Jobs are named by their place in the CV; dates only when the CV gives them.
function jobPlace(job: Job, index: number, total: number): string {
  const place = `job ${index + 1} of ${total}`
  return job.start || job.end || job.is_current ? `${place} (${formatPeriod(job.start, job.end, job.is_current)})` : place
}

// The one label a bullet gets on the card: a stated result matters most, then what they did.
function mainTag(tags: EvidenceTag[]): EvidenceTag | null {
  return (['outcome', 'action', 'duty'] as const).find((tag) => tags.includes(tag)) ?? null
}

// A quote can stop at a line break mid-sentence ("…REST Framework,"): drop the dangling punctuation.
function quoteText(text: string): string {
  return `“${text.replace(/[\s,;:]+$/, '')}”`
}

function focusSoon(elementId: string) {
  requestAnimationFrame(() => document.getElementById(elementId)?.focus())
}

// Four shapes, so status never depends on colour: filled check, half-filled, dashed ring, ring with "?".
// Only verified evidence gets the sage colour.
function StatusIcon({ status }: { status: EvidenceStatus }) {
  return (
    <svg className="status-icon" data-status={status} width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
      {status === 'demonstrated' && (
        <>
          <circle cx="8" cy="8" r="7" fill="currentColor" />
          <path d="M5 8.2l2 2 4-4.4" fill="none" stroke="var(--color-surface)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </>
      )}
      {status === 'partial' && (
        <>
          <circle cx="8" cy="8" r="6.25" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <path d="M8 1.75a6.25 6.25 0 0 0 0 12.5z" fill="currentColor" />
        </>
      )}
      {status === 'not_found' && (
        <circle cx="8" cy="8" r="6.25" fill="none" stroke="currentColor" strokeWidth="1.5" strokeDasharray="2.6 2.2" />
      )}
      {status === 'unverified' && (
        <>
          <circle cx="8" cy="8" r="6.25" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <path d="M6.3 6.4a1.8 1.8 0 1 1 2.5 1.6c-.5.2-.8.6-.8 1.1v.4" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
          <circle cx="8" cy="11.3" r=".85" fill="currentColor" />
        </>
      )}
    </svg>
  )
}

function Tags({ tags }: { tags: EvidenceTag[] }) {
  if (tags.length === 0) return null
  return (
    <span className="tags">
      {tags.map((tag) => (
        <span key={tag} className="tag" data-tag={tag}>
          {tag === 'outcome' ? 'Outcome, as claimed in CV' : TAG_LABELS[tag]}
        </span>
      ))}
    </span>
  )
}

type CheckProps = { candidate: Candidate; buried: Buried[]; onLookAgain: () => void; onRejectAnyway: () => void }

// "Before you reject": shown only when the backend's buried rule is met. Neutral on purpose: it
// shows information and never questions the reason (presentation, seniority or fit are all valid).
function BeforeYouReject({ candidate, buried, onLookAgain, onRejectAnyway }: CheckProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const lookAgainRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    dialogRef.current?.showModal()
    // showModal focuses the first button (Reject anyway). Start on the safe choice instead.
    lookAgainRef.current?.focus()
  }, [])
  const total = candidate.jobs.length

  return (
    <dialog
      ref={dialogRef}
      className="dialog check-dialog"
      aria-labelledby="check-title"
      aria-describedby="check-intro"
      // Escape is the safe choice: same as Look again, and nothing changes.
      onCancel={(e) => {
        e.preventDefault()
        onLookAgain()
      }}
    >
      <h2 id="check-title" className="dialog-title">Before you reject</h2>
      <p id="check-intro">
        {buried.length === 1 ? (
          <>
            There's relevant evidence for <strong>{buried[0].requirement.text}</strong> in this candidate's job{' '}
            {buried[0].jobIndex + 1} of {total}, not shown in the 2 jobs on this card.
          </>
        ) : (
          <>There's relevant evidence for {buried.length} must-haves in older jobs, not shown in the 2 jobs on this card.</>
        )}
      </p>
      <ul className="check-list">
        {buried.map(({ requirement, quote, job, jobIndex }) => (
          <li key={requirement.text}>
            {buried.length > 1 && <p className="check-requirement">{requirement.text}</p>}
            <blockquote className="quote">{quoteText(quote.text)}</blockquote>
            <p className="job-meta">
              {job.title}
              {job.company && `, ${job.company}`}, {jobPlace(job, jobIndex, total)}
            </p>
          </li>
        ))}
      </ul>
      <p className="field-hint">
        This experience is older and may not reflect current skill. Worth a look before you decide?
      </p>
      <div className="dialog-actions">
        <button type="button" className="button button-secondary" onClick={onRejectAnyway}>
          Reject anyway
        </button>
        <button ref={lookAgainRef} type="button" className="button button-primary" onClick={onLookAgain}>
          Look again
        </button>
      </div>
    </dialog>
  )
}

// Where each requirement shows up: requirements down the side, jobs across, the 2 jobs on the card
// shaded. A dot outside the shaded columns is what a 20-second scan doesn't reach.
function EvidenceMap({ candidate }: { candidate: Candidate }) {
  const evidence = candidate.evidence!
  const jobs = candidate.jobs
  const windowSize = Math.min(RECENT_JOBS, jobs.length)
  const older = jobs.length - windowSize
  const columns: (number | null)[] = [...jobs.map((_, index) => index), null] // null: summary, skills...
  const mustHaves = evidence.requirements.filter((r) => r.must_have)
  const niceToHaves = evidence.requirements.filter((r) => !r.must_have)

  const row = (requirement: RequirementEvidence) => (
    <tr key={requirement.text} className={requirement.buried ? 'is-buried' : undefined}>
      <th scope="row">
        <span className="map-requirement">
          <StatusIcon status={requirement.status} />
          <span>
            {requirement.text}
            <span className="visually-hidden">: {STATUS_HINTS[requirement.status]}</span>
          </span>
        </span>
      </th>
      {columns.map((column) => {
        const found = requirement.quotes.some((q) => q.verified && q.job_index === column)
        const isOlder = column !== null && column >= RECENT_JOBS
        return (
          <td key={column ?? 'other'} className={column !== null && column < RECENT_JOBS ? 'is-window' : undefined}>
            {found && (
              <span className="map-dot" data-older={isOlder || undefined}>
                <span className="visually-hidden">Found</span>
              </span>
            )}
          </td>
        )
      })}
    </tr>
  )

  return (
    <div className="map-scroll">
      <table className="evidence-map">
        <caption className="visually-hidden">
          Where each requirement shows up in the CV, by job. Jobs 1 and 2 are the ones on this card.
        </caption>
        <thead>
          <tr className="map-groups">
            <td />
            <th scope="colgroup" colSpan={windowSize} className="is-window">On card</th>
            {older > 0 && <th scope="colgroup" colSpan={older}>Older</th>}
            <td />
          </tr>
          <tr>
            <th scope="col" className="map-corner">Requirement</th>
            {jobs.map((job, index) => (
              <th
                key={index}
                scope="col"
                className={index < RECENT_JOBS ? 'is-window' : undefined}
                title={`${job.title}, ${jobPlace(job, index, jobs.length)}`}
              >
                <span aria-hidden="true">{index + 1}</span>
                <span className="visually-hidden">Job {index + 1}, {job.title}</span>
              </th>
            ))}
            <th scope="col" title="Summary, skills and other sections">
              <span aria-hidden="true">CV</span>
              <span className="visually-hidden">Elsewhere in the CV</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {mustHaves.map(row)}
          {niceToHaves.length > 0 && (
            <tr className="map-section">
              <th scope="colgroup" colSpan={columns.length + 1}>
                <span>Nice-to-haves</span>
              </th>
            </tr>
          )}
          {niceToHaves.map(row)}
        </tbody>
      </table>
    </div>
  )
}

// The quotes behind the map, grouped by job in CV order (the way a recruiter reads a CV).
// A sentence that supports several requirements is shown once, with all of them.
function QuotesByJob({ candidate, lookAgainJob }: { candidate: Candidate; lookAgainJob: number | null }) {
  const evidence = candidate.evidence!
  const total = candidate.jobs.length
  const groups = new Map<number | null, Map<string, { quote: Quote; requirements: string[] }>>()
  let unverified = 0
  for (const requirement of evidence.requirements) {
    for (const quote of requirement.quotes) {
      if (!quote.verified) {
        unverified += 1
        continue
      }
      const group = groups.get(quote.job_index) ?? new Map<string, { quote: Quote; requirements: string[] }>()
      const entry = group.get(quote.text) ?? { quote, requirements: [] }
      entry.requirements.push(requirement.text)
      group.set(quote.text, entry)
      groups.set(quote.job_index, group)
    }
  }
  const order = [...candidate.jobs.map((_, index): number | null => index), null].filter((key) => groups.has(key))

  return (
    <div className="quote-groups">
      {order.map((jobIndex) => {
        const job = jobIndex === null ? null : candidate.jobs[jobIndex]
        const isOlder = jobIndex !== null && jobIndex >= RECENT_JOBS
        const target = jobIndex !== null && jobIndex === lookAgainJob
        return (
          <section
            key={jobIndex ?? 'other'}
            className="quote-group"
            data-older={isOlder || undefined}
            id={target ? 'scan-older-evidence' : undefined}
            tabIndex={target ? -1 : undefined}
            aria-label={job && jobIndex !== null ? `Job ${jobIndex + 1} of ${total}, ${job.title}` : 'Elsewhere in the CV'}
          >
            <div className="quote-group-head">
              {job && jobIndex !== null ? (
                <>
                  <p className="quote-group-place">
                    Job {jobIndex + 1} of {total}
                    {isOlder && <span className="badge-attention">Not on this card</span>}
                  </p>
                  <p>
                    <span className="job-title">{job.title}</span>
                    {job.company && <span className="job-company">, {job.company}</span>}
                  </p>
                  <p className="job-meta">{formatPeriod(job.start, job.end, job.is_current)}</p>
                </>
              ) : (
                <p className="quote-group-place">Elsewhere in the CV (summary, skills and other sections)</p>
              )}
            </div>
            <ul className="quote-list">
              {[...groups.get(jobIndex)!.values()].map(({ quote, requirements }) => (
                <li key={quote.text}>
                  <p className="quote-for">{requirements.join('; ')}</p>
                  <blockquote className="quote">
                    {isOlder ? <mark>{quoteText(quote.text)}</mark> : quoteText(quote.text)}
                  </blockquote>
                  <Tags tags={quote.tags} />
                </li>
              ))}
            </ul>
          </section>
        )
      })}
      {unverified > 0 && (
        <p className="scan-note">
          {unverified === 1 ? '1 quote' : `${unverified} quotes`} from the AI couldn't be matched to the CV text, so{' '}
          {unverified === 1 ? "it isn't" : "they aren't"} shown.
        </p>
      )}
    </div>
  )
}

type CardProps = {
  candidate: Candidate
  evidenceOpen: boolean
  onEvidenceToggle: (open: boolean) => void
  onShowOlderEvidence: () => void
  onOpenProfile: () => void
  onUpdate: (candidate: Candidate) => void
}

function ScanCard({ candidate, evidenceOpen, onEvidenceToggle, onShowOlderEvidence, onOpenProfile, onUpdate }: CardProps) {
  const [checking, setChecking] = useState(false)
  const [checkError, setCheckError] = useState<string | null>(null)
  const name = candidate.name ?? 'Name not found'
  const years = formatYears(candidate.years_experience)
  const total = candidate.jobs.length
  const recent = candidate.jobs.slice(0, RECENT_JOBS)
  const evidence = candidate.evidence
  const mustHaves = evidence?.requirements.filter((r) => r.must_have) ?? []
  const buried = buriedEvidence(candidate)
  const buriedJobs = [...new Set(buried.map((b) => b.jobIndex))]
  const buriedJobFor = new Map(buried.map((b) => [b.requirement.text, b.jobIndex])) // for "Only in job 4"
  const hasOutcomes = recent.some((_, jobIndex) =>
    evidence?.highlight_tags[jobIndex]?.slice(0, 2).some((tags) => tags.includes('outcome')),
  )
  const footnote = [
    hasOutcomes && 'Outcomes are as claimed in the CV.',
    total > RECENT_JOBS && `${total - RECENT_JOBS} older ${total - RECENT_JOBS === 1 ? 'job' : 'jobs'} not on this card.`,
  ]
    .filter(Boolean)
    .join(' ')

  async function checkEvidence() {
    setChecking(true)
    setCheckError(null)
    try {
      onUpdate(await api.checkEvidence(candidate.id))
    } catch (err) {
      setCheckError((err as Error).message)
    } finally {
      setChecking(false)
    }
  }

  return (
    <article className="scan-card" aria-labelledby="scan-name">
      <div className="scan-card-header">
        <div>
          <h3 id="scan-name" className="scan-name" tabIndex={-1}>{name}</h3>
          <p className="profile-meta">
            {[candidate.current_title, years && `${years} experience`].filter(Boolean).join(', ') ||
              'No work history found'}
          </p>
        </div>
        <button id="scan-profile" type="button" className="button button-secondary" onClick={onOpenProfile}>
          Full profile
        </button>
      </div>

      {/* The one thing a 20-second scan would miss, right under the name so it's seen without scrolling. */}
      {buried.length > 0 && (
        <div className="scan-callout">
          <p>
            <strong className="scan-callout-title">Beyond the last 2 jobs</strong>
            {buried.length === 1 ? (
              <>
                <strong>{buried[0].requirement.text}</strong> only shows up in{' '}
                {jobPlace(buried[0].job, buried[0].jobIndex, total)}.
              </>
            ) : buriedJobs.length === 1 ? (
              <>
                {buried.length} must-haves only show up in {jobPlace(buried[0].job, buried[0].jobIndex, total)}.
              </>
            ) : (
              <>{buried.length} must-haves only show up in older jobs.</>
            )}
          </p>
          <button type="button" className="text-button scan-callout-action" onClick={onShowOlderEvidence}>
            Show the evidence
          </button>
        </div>
      )}

      {recent.length > 0 && (
        <section aria-labelledby="scan-jobs-title" className="scan-section">
          <h4 id="scan-jobs-title" className="req-label">On this card: last {recent.length === 1 ? 'job' : '2 jobs'}</h4>
          <ol className="scan-jobs">
            {recent.map((job, jobIndex) => (
              <li key={jobIndex} className="scan-job">
                <div className="scan-job-head">
                  <p>
                    <span className="job-title">{job.title}</span>
                    {job.company && <span className="job-company">, {job.company}</span>}
                  </p>
                  <p className="job-meta">{formatPeriod(job.start, job.end, job.is_current)}</p>
                </div>
                {job.highlights.length > 0 && (
                  <ul className="scan-bullets">
                    {job.highlights.slice(0, 2).map((text, index) => {
                      const tag = mainTag(evidence?.highlight_tags[jobIndex]?.[index] ?? [])
                      return (
                        <li key={index} data-tag={tag ?? undefined}>
                          <span className="bullet-tag">
                            {tag && TAG_LABELS[tag]}
                            {tag === 'outcome' && <span className="visually-hidden">, as claimed in the CV</span>}
                            {tag && <span className="visually-hidden">: </span>}
                          </span>
                          <span className="bullet-text">{text}</span>
                        </li>
                      )
                    })}
                  </ul>
                )}
              </li>
            ))}
          </ol>
          {footnote && <p className="scan-note">{footnote}</p>}
        </section>
      )}

      {candidate.evidence_status !== 'complete' ? (
        <div className="scan-note">
          <p>
            {candidate.evidence_status === 'failed'
              ? "Evidence couldn't be checked for this CV, so there's no check before rejecting."
              : "Evidence hasn't been checked for this CV yet, so there's no check before rejecting."}
          </p>
          <button
            type="button"
            className="button button-secondary scan-check-button"
            aria-disabled={checking}
            onClick={() => !checking && checkEvidence()}
          >
            {checking ? 'Checking…' : 'Check now'}
          </button>
          {checkError && <p className="field-error" role="alert">{checkError}</p>}
        </div>
      ) : (
        evidence && (
          <>
            {mustHaves.length > 0 && (
              <section aria-labelledby="scan-musts-title" className="scan-section">
                <h4 id="scan-musts-title" className="req-label">Must-haves in the CV</h4>
                <ul className="checklist">
                  {mustHaves.map((requirement) => {
                    const buriedJob = buriedJobFor.get(requirement.text)
                    return (
                      <li
                        key={requirement.text}
                        data-status={requirement.status}
                        title={`${requirement.text}: ${STATUS_HINTS[requirement.status]}`}
                      >
                        <StatusIcon status={requirement.status} />
                        <span className="checklist-text">{requirement.text}</span>
                        {buriedJob !== undefined ? (
                          <span className="badge-attention">Only in job {buriedJob + 1}</span>
                        ) : (
                          <span className="checklist-status">
                            {STATUS_LABELS[requirement.status]}
                            {requirement.status === 'unverified' && (
                              <span className="visually-hidden">: {STATUS_HINTS.unverified}</span>
                            )}
                          </span>
                        )}
                      </li>
                    )
                  })}
                </ul>
              </section>
            )}

            {!evidence.sections_found && (
              <p className="scan-note">
                This CV's jobs couldn't be matched to its text, so quotes can't be checked and there's no check
                before rejecting.
              </p>
            )}

            <details
              className="scan-evidence"
              open={evidenceOpen}
              onToggle={(e) => onEvidenceToggle(e.currentTarget.open)}
            >
              <summary>
                <span>Where the evidence is</span>
                <svg className="chevron" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
                  <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </summary>
              <div className="scan-evidence-body">
                <EvidenceMap candidate={candidate} />
                <QuotesByJob candidate={candidate} lookAgainJob={buried[0]?.jobIndex ?? null} />
              </div>
            </details>
          </>
        )
      )}
    </article>
  )
}

type Move = { candidateId: number; decisionId: number; from: Stage; to: Stage; position: number }

type Props = {
  candidates: Candidate[]
  onClose: () => void
  onUpdate: (candidate: Candidate) => void
  onOpenProfile: (id: number) => void
}

export default function ScanMode({ candidates, onClose, onUpdate, onOpenProfile }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  // The queue is fixed when Scan mode opens: the New column, oldest upload first. No ranking.
  const [queue] = useState(() =>
    candidates.filter((c) => c.stage === 'new').map((c) => c.id).sort((a, b) => a - b),
  )
  const [position, setPosition] = useState(0)
  const [moves, setMoves] = useState<Move[]>([]) // for Undo
  const [log, setLog] = useState<Decision[]>([]) // this session's decisions, for the summary
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [checking, setChecking] = useState(false)
  const [evidenceOpen, setEvidenceOpen] = useState(false)

  useEffect(() => {
    dialogRef.current?.showModal()
    focusSoon(queue.length > 0 ? 'scan-name' : 'scan-done')
  }, [queue.length])

  const current = position < queue.length ? candidates.find((c) => c.id === queue[position]) ?? null : null
  const lastMove = moves.at(-1)
  const lastMoved = lastMove && candidates.find((c) => c.id === lastMove.candidateId)

  function goTo(next: number) {
    setPosition(next)
    setEvidenceOpen(false)
    focusSoon(next < queue.length ? 'scan-name' : 'scan-done')
  }

  // Open the evidence and bring the older job's quotes into view, with focus on them.
  function showOlderEvidence() {
    setEvidenceOpen(true)
    requestAnimationFrame(() => {
      const target = document.getElementById('scan-older-evidence')
      const smooth = window.matchMedia('(prefers-reduced-motion: no-preference)').matches
      target?.scrollIntoView({ block: 'start', behavior: smooth ? 'smooth' : 'auto' })
      target?.focus({ preventScroll: true })
    })
  }

  async function submit(candidate: Candidate, input: DecisionInput): Promise<Decision | null> {
    setBusy(true)
    setError(null)
    try {
      const result = await api.decide(candidate.id, input)
      onUpdate(result.candidate)
      setLog((prev) => [...prev, result.decision])
      return result.decision
    } catch (err) {
      setError(`Couldn't save the decision for ${candidate.name ?? 'this candidate'}. ${(err as Error).message}`)
      return null
    } finally {
      setBusy(false)
    }
  }

  async function move(to: Stage, check?: 'reject_anyway') {
    if (!current || busy) return
    const from = current.stage
    const decision = await submit(current, { to_stage: to, prompt_shown: Boolean(check), prompt_choice: check })
    if (!decision) return
    setMoves((prev) => [...prev, { candidateId: current.id, decisionId: decision.id, from, to, position }])
    goTo(position + 1)
  }

  function reject() {
    if (!current || busy) return
    if (buriedEvidence(current).length > 0) setChecking(true)
    else move('rejected')
  }

  // No stage change: show the older job's evidence and log the choice.
  function lookAgain() {
    if (!current) return
    setChecking(false)
    submit(current, { to_stage: current.stage, prompt_shown: true, prompt_choice: 'look_again' })
    showOlderEvidence()
  }

  async function undo() {
    if (!lastMove || !lastMoved || busy) return
    const decision = await submit(lastMoved, { to_stage: lastMove.from, undo_of: lastMove.decisionId })
    if (!decision) return
    setMoves((prev) => prev.slice(0, -1))
    goTo(lastMove.position)
  }

  // The summary counts this session's decisions only: the last move per candidate still standing
  // (an undone move is gone from `moves`). Look again never moves anyone, so it's not a move.
  const outcomes = new Map(moves.map((m) => [m.candidateId, m.to]))
  const decided = (stage: Stage) => [...outcomes.values()].filter((to) => to === stage).length
  const summary: { stage: Stage; label: string; count: number }[] = [
    { stage: 'rejected', label: 'Rejected', count: decided('rejected') },
    { stage: 'shortlisted', label: 'Shortlisted', count: decided('shortlisted') },
    { stage: 'interview', label: 'Interview', count: decided('interview') },
    { stage: 'new', label: 'Left in New or skipped', count: queue.length - outcomes.size + decided('new') },
  ]
  const promptsShown = log.filter((d) => d.prompt_choice !== null)
  const lookedAgain = promptsShown.filter((d) => d.prompt_choice === 'look_again').length
  const progress = queue.length === 0 ? 1 : Math.min(position, queue.length) / queue.length

  return (
    <dialog
      ref={dialogRef}
      className="scan"
      aria-labelledby="scan-title"
      // Nested dialogs can bubble their close event through React: only react to our own.
      onClose={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="scan-layout">
        <header className="scan-header">
          <div className="scan-heading">
            <h2 id="scan-title" className="scan-title">Scan mode</h2>
            {current && (
              <p className="scan-progress">
                <span>
                  <strong>{position + 1}</strong> of {queue.length} new {queue.length === 1 ? 'candidate' : 'candidates'},
                </span>
                <span className="scan-order">oldest upload first</span>
              </p>
            )}
          </div>
          <button type="button" className="button button-secondary" onClick={() => dialogRef.current?.close()}>
            Close
          </button>
          <div className="scan-progress-bar" aria-hidden="true">
            <span style={{ scale: `${progress} 1` }} />
          </div>
        </header>

        <div className="scan-body">
          {error && <p className="banner-error" role="alert">{error}</p>}
          {current ? (
            <ScanCard
              key={current.id}
              candidate={current}
              evidenceOpen={evidenceOpen}
              onEvidenceToggle={setEvidenceOpen}
              onShowOlderEvidence={showOlderEvidence}
              onOpenProfile={() => onOpenProfile(current.id)}
              onUpdate={onUpdate}
            />
          ) : (
            <div className="scan-done">
              <h3 id="scan-done" className="scan-name" tabIndex={-1}>
                {queue.length === 0 ? 'No candidates in New' : "You've gone through New"}
              </h3>
              {queue.length === 0 ? (
                <p className="empty-text">Scan mode goes through the New column. Upload CVs to add candidates.</p>
              ) : (
                <>
                  <p className="scan-note">This session, {queue.length} new {queue.length === 1 ? 'candidate' : 'candidates'}:</p>
                  <dl className="scan-stats">
                    {summary.map(({ stage, label, count }) => (
                      <div key={stage} data-stage={stage}>
                        <dt>
                          <span className="stage-dot" aria-hidden="true" />
                          {label}
                        </dt>
                        <dd>{count}</dd>
                      </div>
                    ))}
                  </dl>
                  <p className="scan-note">
                    “Before you reject” appeared {promptsShown.length} {promptsShown.length === 1 ? 'time' : 'times'}
                    {promptsShown.length > 0 && `: Look again ${lookedAgain}, Reject anyway ${promptsShown.length - lookedAgain}`}.
                  </p>
                </>
              )}
            </div>
          )}
        </div>

        <footer className="scan-footer">
          {current && (
            <div className="scan-actions" role="group" aria-label={`Decision for ${current.name ?? 'this candidate'}`}>
              {(['rejected', 'shortlisted', 'interview'] as Stage[]).map((stage) => (
                <button
                  key={stage}
                  type="button"
                  className="button button-secondary scan-action"
                  data-stage={stage}
                  aria-disabled={busy}
                  onClick={() => (stage === 'rejected' ? reject() : move(stage))}
                >
                  <span className="stage-dot" aria-hidden="true" />
                  {stage === 'rejected' ? 'Reject' : stage === 'shortlisted' ? 'Shortlist' : 'Interview'}
                </button>
              ))}
            </div>
          )}
          <div className="scan-secondary">
            {current && (
              <button type="button" className="text-button" onClick={() => goTo(position + 1)}>
                Skip for now
              </button>
            )}
            {lastMove && lastMoved && (
              <button type="button" className="text-button" aria-disabled={busy} onClick={undo}>
                Undo: {MOVE_LABELS[lastMove.to]} {lastMoved.name ?? 'candidate'}
              </button>
            )}
          </div>
        </footer>
      </div>

      {checking && current && (
        <BeforeYouReject
          candidate={current}
          buried={buriedEvidence(current)}
          onLookAgain={lookAgain}
          onRejectAnyway={() => {
            setChecking(false)
            move('rejected', 'reject_anyway')
          }}
        />
      )}
    </dialog>
  )
}
