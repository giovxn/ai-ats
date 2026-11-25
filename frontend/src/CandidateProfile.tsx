// Block 2: a candidate's profile in a side panel: summary, skills, an expandable
// work-history timeline, education and the original CV text.
// Block 3 adds the stage picker here.

import { useEffect, useRef } from 'react'
import type { Candidate, Job } from './api'
import { formatDuration, formatPeriod, formatYears } from './format'

type Props = {
  candidate: Candidate | null // null = closed
  onClose: () => void
}

function Chevron() {
  return (
    <svg className="chevron" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
      <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function TimelineItem({ job, expanded }: { job: Job; expanded: boolean }) {
  const duration = formatDuration(job.start, job.end, job.is_current)
  const heading = (
    <span className="job-heading">
      <span className="job-title">{job.title}</span>
      {job.company && <span className="job-company">{job.company}</span>}
      <span className="job-meta">
        {formatPeriod(job.start, job.end, job.is_current)}
        {duration && ` · ${duration}`}
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

export default function CandidateProfile({ candidate, onClose }: Props) {
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
              <h2 id="profile-name" className="profile-name">{candidate.name ?? 'Name not found'}</h2>
              <p className="profile-meta">
                {[candidate.current_title, years && `${years} experience`].filter(Boolean).join(' · ') ||
                  'No work history found'}
              </p>
            </div>
            <button type="button" className="button button-secondary" onClick={onClose}>
              Close
            </button>
          </div>

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
                      {[item.institution, item.year].filter(Boolean).join(' · ')}
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
