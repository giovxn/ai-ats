// Blocks 2 and 3: a candidate's profile in a side panel: stage buttons, summary, skills,
// an expandable work-history timeline, education and the original CV text.

import { useEffect, useRef, useState } from 'react'
import { STAGES, type Candidate, type Job, type Stage } from './api'
import { formatDuration, formatPeriod, formatYears } from './format'

type Props = {
  candidate: Candidate | null // null = closed
  moveError: string | null // shown here too, because the board's banner is behind the panel
  onClose: () => void
  onMove: (stage: Stage) => void
}

function Chevron() {
  return (
    <svg className="chevron" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
      <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function SearchIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
      <circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  )
}

function MailIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
      <rect x="1.5" y="3" width="11" height="8" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.3" />
      <path d="M2 3.8l5 3.7 5-3.7" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
    </svg>
  )
}

function PhoneIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
      <path
        d="M4.2 1.8l1.5 2.6-1.2 1.2a7 7 0 003.9 3.9l1.2-1.2 2.6 1.5-.6 2a1.5 1.5 0 01-1.6 1A10 10 0 011 3.2a1.5 1.5 0 011-1.6z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
      <path d="M2.5 7.5l3 3 6-7" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

// The clipboard API can refuse (an unfocused page, an older browser). Fall back to
// selecting a hidden textarea and copying it. It goes next to the button, because
// everything outside the open profile panel is inert.
async function copyText(text: string, near: HTMLElement): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const area = document.createElement('textarea')
    area.value = text
    area.setAttribute('readonly', '')
    area.className = 'visually-hidden'
    near.after(area)
    area.select()
    const copied = document.execCommand('copy')
    area.remove()
    near.focus()
    return copied
  }
}

// Email and phone copy to the clipboard on click, so a recruiter can paste them into
// whatever they use to reach people. A check mark and a screen-reader message confirm it.
function CopyChip({ kind, value, icon }: { kind: string; value: string; icon: React.ReactNode }) {
  const [status, setStatus] = useState<'idle' | 'copied' | 'failed'>('idle')

  useEffect(() => {
    if (status === 'idle') return
    const timer = setTimeout(() => setStatus('idle'), 2000)
    return () => clearTimeout(timer)
  }, [status])

  async function copy(event: React.MouseEvent<HTMLButtonElement>) {
    setStatus((await copyText(value, event.currentTarget)) ? 'copied' : 'failed')
  }

  return (
    <>
      <button type="button" className={`link-chip${status === 'idle' ? '' : ` is-${status}`}`} onClick={copy}>
        {status === 'copied' ? <CheckIcon /> : icon}
        <span className="visually-hidden">Copy {kind} </span>
        {value}
      </button>
      {/* Always rendered, so screen readers announce changes. A failure is also shown on screen. */}
      <span className={status === 'failed' ? 'copy-error' : 'visually-hidden'} role="status">
        {status === 'copied' ? `${kind[0].toUpperCase()}${kind.slice(1)} copied` : status === 'failed' ? "Couldn't copy. Try again, or copy it from the original CV below." : ''}
      </span>
    </>
  )
}

// LinkedIn and GitHub marks (from SVG Repo), drawn in the text colour like our other icons.
// The viewBox adds a little room around LinkedIn's mark so both icons look the same size.
const SITE_ICONS: Record<string, { path: string; viewBox: string; evenOdd?: boolean }> = {
  'linkedin.com': { viewBox: '-40 -40 592 592', path: 'M116.504,500.219V170.654H6.975v329.564H116.504 L116.504,500.219z M61.751,125.674c38.183,0,61.968-25.328,61.968-56.953c-0.722-32.328-23.785-56.941-61.252-56.941 C24.994,11.781,0.5,36.394,0.5,68.722c0,31.625,23.772,56.953,60.53,56.953H61.751L61.751,125.674z M177.124,500.219 c0,0,1.437-298.643,0-329.564H286.67v47.794h-0.727c14.404-22.49,40.354-55.533,99.44-55.533 c72.085,0,126.116,47.103,126.116,148.333v188.971H401.971V323.912c0-44.301-15.848-74.531-55.497-74.531 c-30.254,0-48.284,20.38-56.202,40.08c-2.897,7.012-3.602,16.861-3.602,26.711v184.047H177.124L177.124,500.219z', evenOdd: true },
  'github.com': { viewBox: '0 0 24 24', path: 'M12 1A10.89 10.89 0 0 0 1 11.77 10.79 10.79 0 0 0 8.52 22c.55.1.75-.23.75-.52v-1.83c-3.06.65-3.71-1.44-3.71-1.44a2.86 2.86 0 0 0-1.22-1.58c-1-.66.08-.65.08-.65a2.31 2.31 0 0 1 1.68 1.11 2.37 2.37 0 0 0 3.2.89 2.33 2.33 0 0 1 .7-1.44c-2.44-.27-5-1.19-5-5.32a4.15 4.15 0 0 1 1.11-2.91 3.78 3.78 0 0 1 .11-2.84s.93-.29 3 1.1a10.68 10.68 0 0 1 5.5 0c2.1-1.39 3-1.1 3-1.1a3.78 3.78 0 0 1 .11 2.84A4.15 4.15 0 0 1 19 11.2c0 4.14-2.58 5.05-5 5.32a2.5 2.5 0 0 1 .75 2v2.95c0 .35.2.63.75.52A10.8 10.8 0 0 0 23 11.77 10.89 10.89 0 0 0 12 1' },
}

const SITE_NAMES: Record<string, string> = {
  'linkedin.com': 'LinkedIn',
  'github.com': 'GitHub',
  'gitlab.com': 'GitLab',
  'behance.net': 'Behance',
  'dribbble.com': 'Dribbble',
  'medium.com': 'Medium',
}

// LinkedIn and GitHub show their icon; any other site shows its name or address
// ("jdoe.dev"): code can't tell a portfolio from a former employer's website.
// A page below the home page adds its last path part, so several project pages on one
// portfolio stay apart: "jdoe.dev", "jdoe.dev/weatherfit", "jdoe.dev/dashboard".
function SiteLink({ url }: { url: string }) {
  const parsed = new URL(url)
  const host = parsed.hostname.replace(/^www\./, '')
  const page = parsed.pathname.split('/').filter(Boolean).at(-1)
  const name = SITE_NAMES[host] ?? (page ? `${host}/${decodeURIComponent(page)}` : host)
  const icon = SITE_ICONS[host]
  return icon ? (
    <a
      className="link-chip link-icon"
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`${name} (opens in a new tab)`}
      title={name}
    >
      <svg width="16" height="16" viewBox={icon.viewBox} aria-hidden="true">
        <path d={icon.path} fill="currentColor" fillRule={icon.evenOdd ? 'evenodd' : undefined} />
      </svg>
    </a>
  ) : (
    <a className="link-chip" href={url} target="_blank" rel="noopener noreferrer" title={url}>
      {name}
      <span className="visually-hidden"> (opens in a new tab)</span>
    </a>
  )
}

// A plain web search for the candidate, opened by the recruiter in a new tab.
function searchUrl(candidate: Candidate): string {
  const query = [`"${candidate.name}"`, candidate.current_title].filter(Boolean).join(' ')
  return `https://www.google.com/search?q=${encodeURIComponent(query)}`
}

function TimelineItem({ job, expanded }: { job: Job; expanded: boolean }) {
  const duration = formatDuration(job.start, job.end, job.is_current)
  const heading = (
    <span className="job-heading">
      <span className="job-title">{job.title}</span>
      {job.company && <span className="job-company">{job.company}</span>}
      <span className="job-meta">
        {formatPeriod(job.start, job.end, job.is_current)}
        {duration && ` (${duration})`}
      </span>
    </span>
  )

  return (
    <li className={`timeline-item${job.is_current ? ' is-current' : ''}`}>
      <span className="timeline-dot" aria-hidden="true" />
      {job.highlights.length > 0 ? (
        <details className="job" open={expanded}>
          <summary>
            {heading}
            <Chevron />
          </summary>
          <ul className="job-highlights">
            {job.highlights.map((text, index) => (
              <li key={index}>{text}</li>
            ))}
          </ul>
        </details>
      ) : (
        <div className="job">{heading}</div>
      )}
    </li>
  )
}

export default function CandidateProfile({ candidate, moveError, onClose, onMove }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (candidate && !dialog.open) dialog.showModal()
    else if (!candidate && dialog.open) dialog.close()
  }, [candidate])

  const years = candidate ? formatYears(candidate.years_experience) : null

  return (
    <dialog
      ref={dialogRef}
      className="drawer"
      aria-labelledby="profile-name"
      onClose={onClose}
      // Nothing to lose here, so a click on the backdrop closes the panel.
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      {candidate && (
        <div className="drawer-body">
          <div className="profile-header">
            <div>
              <div className="profile-title-row">
                <h2 id="profile-name" className="profile-name">{candidate.name ?? 'Name not found'}</h2>
                {candidate.name && (
                  <a
                    className="link-chip link-icon"
                    href={searchUrl(candidate)}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={`Search the web for ${candidate.name} (opens in a new tab)`}
                    title="Search the web"
                  >
                    <SearchIcon />
                  </a>
                )}
              </div>
              <p className="profile-meta">
                {[candidate.current_title, years && `${years} experience`].filter(Boolean).join(', ') ||
                  'No work history found'}
              </p>
              {(candidate.email || candidate.phone || candidate.links.length > 0) && (
                <ul className="profile-links" aria-label="Contact and links">
                  {candidate.email && (
                    <li>
                      <CopyChip kind="email" value={candidate.email} icon={<MailIcon />} />
                    </li>
                  )}
                  {candidate.phone && (
                    <li>
                      <CopyChip kind="phone number" value={candidate.phone} icon={<PhoneIcon />} />
                    </li>
                  )}
                  {candidate.links.map((url) => (
                    <li key={url}>
                      <SiteLink url={url} />
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <button type="button" className="button button-secondary" onClick={onClose}>
              Close
            </button>
          </div>

          <div className="stage-buttons" role="group" aria-label="Stage">
            {STAGES.map((stage) => (
              <button
                key={stage.id}
                type="button"
                className="stage-button"
                data-stage={stage.id}
                aria-pressed={candidate.stage === stage.id}
                onClick={() => onMove(stage.id)}
              >
                <span className="stage-dot" aria-hidden="true" />
                {stage.label}
              </button>
            ))}
          </div>
          {moveError && <p className="field-error" role="alert">{moveError}</p>}

          {/*
            Block 4 plug-in point: an AI feature about this candidate renders here.
            Backend pattern: a prompt in prompts.py, an output schema in schemas.py,
            then llm.extract() called from a new route in main.py.
          */}

          {candidate.summary && <p className="profile-summary">{candidate.summary}</p>}

          {candidate.skills.length > 0 && (
            <section className="profile-section" aria-labelledby="profile-skills">
              <h3 id="profile-skills" className="req-label">
                Skills <span className="req-count">{candidate.skills.length}</span>
              </h3>
              <ul className="chips">
                {candidate.skills.map((skill, index) => (
                  <li key={index} className="chip">{skill}</li>
                ))}
              </ul>
            </section>
          )}

          <section className="profile-section" aria-labelledby="profile-experience">
            <h3 id="profile-experience" className="req-label">Experience</h3>
            {candidate.jobs.length > 0 ? (
              <ol className="timeline">
                {candidate.jobs.map((job, index) => (
                  <TimelineItem key={index} job={job} expanded={index === 0} />
                ))}
              </ol>
            ) : (
              <p className="profile-empty">No work history found in this CV.</p>
            )}
          </section>

          {candidate.education.length > 0 && (
            <section className="profile-section" aria-labelledby="profile-education">
              <h3 id="profile-education" className="req-label">Education</h3>
              <ul className="education">
                {candidate.education.map((item, index) => (
                  <li key={index}>
                    <span className="education-title">{item.qualification}</span>
                    <span className="job-meta">
                      {[item.institution, item.year].filter(Boolean).join(', ')}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <details className="jd">
            <summary>Original CV ({candidate.cv_filename})</summary>
            <p className="jd-text">{candidate.cv_text}</p>
          </details>
        </div>
      )}
    </dialog>
  )
}
