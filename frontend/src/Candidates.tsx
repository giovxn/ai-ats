// Block 2: the selected role's candidates, with the upload dialog and the profile panel.
// App renders this with key={role.id}, so switching roles starts with fresh state.

import { useEffect, useRef, useState } from 'react'
import { api, type Candidate, type Role } from './api'
import CandidateProfile from './CandidateProfile'
import { formatYears } from './format'
import UploadCVs from './UploadCVs'

const CARD_SKILLS = 4

function CandidateCard({ candidate, onOpen }: { candidate: Candidate; onOpen: () => void }) {
  const years = formatYears(candidate.years_experience)
  const extra = candidate.skills.length - CARD_SKILLS

  return (
    <li className="candidate-card">
      {/* The name is the button; CSS stretches its click area over the whole card. */}
      <button type="button" className="candidate-open" onClick={onOpen}>
        {candidate.name ?? 'Name not found'}
      </button>
      <p className="candidate-meta">
        {[candidate.current_title, years].filter(Boolean).join(' · ') || 'No work history found'}
      </p>
      {candidate.skills.length > 0 && (
        <ul className="chips" aria-label="Top skills">
          {candidate.skills.slice(0, CARD_SKILLS).map((skill, index) => (
            <li key={index} className="chip">{skill}</li>
          ))}
          {extra > 0 && (
            <li className="chip chip-more">
              <span aria-hidden="true">+{extra}</span>
              <span className="visually-hidden">{extra} more skills</span>
            </li>
          )}
        </ul>
      )}
    </li>
  )
}

export default function Candidates({ role }: { role: Role }) {
  const [candidates, setCandidates] = useState<Candidate[] | null>(null) // null while loading
  const [loadError, setLoadError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [openId, setOpenId] = useState<number | null>(null)
  const uploadButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    api.listCandidates(role.id).then(setCandidates).catch((err: Error) => setLoadError(err.message))
  }, [role.id])

  const open = candidates?.find((c) => c.id === openId) ?? null

  // The empty state's button disappears once the first CV arrives, so the dialog can't
  // hand focus back to it. Move focus to the header's button instead (after the
  // dialog has restored focus itself, hence the next frame).
  function closeUpload() {
    setUploading(false)
    requestAnimationFrame(() => uploadButtonRef.current?.focus())
  }

  function handleUploaded(candidate: Candidate) {
    setCandidates((prev) => [candidate, ...(prev ?? [])])
  }

  return (
    <section className="candidates" aria-labelledby="candidates-title">
      <div className="section-header">
        <h2 id="candidates-title" className="section-title">
          Candidates {candidates && <span className="section-count">{candidates.length}</span>}
        </h2>
        {/* In the empty state, the button below is the one primary action. */}
        {candidates && candidates.length > 0 && (
          <button ref={uploadButtonRef} className="button button-secondary" onClick={() => setUploading(true)}>
            Upload CVs
          </button>
        )}
      </div>

      {loadError && <p className="banner-error" role="alert">{loadError}</p>}

      {candidates && candidates.length === 0 && (
        <div className="candidates-empty">
          <p className="empty-text">No candidates yet. Upload CVs and we'll turn each one into a profile.</p>
          <button className="button button-primary" onClick={() => setUploading(true)}>
            Upload CVs
          </button>
        </div>
      )}

      {candidates && candidates.length > 0 && (
        <ul className="candidate-grid">
          {candidates.map((candidate) => (
            <CandidateCard key={candidate.id} candidate={candidate} onOpen={() => setOpenId(candidate.id)} />
          ))}
        </ul>
      )}

      <UploadCVs
        roleId={role.id}
        open={uploading}
        onClose={closeUpload}
        onUploaded={handleUploaded}
      />
      <CandidateProfile candidate={open} onClose={() => setOpenId(null)} />
    </section>
  )
}
