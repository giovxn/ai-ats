// Blocks 2 and 3: the selected role's candidates as a pipeline board (New, Shortlisted,
// Interview, Rejected), with the upload dialog and the profile panel.
// App renders this with key={role.id}, so switching roles starts with fresh state.
//
// Three ways to move a candidate, all ending in moveCandidate():
// the stage menu on each card, the stage buttons in the profile, and drag and drop.
// The menu and buttons work with a keyboard, a screen reader and a phone; dragging doesn't.

import { useEffect, useRef, useState } from 'react'
import { api, STAGES, type Candidate, type Role, type Stage } from './api'
import CandidateProfile from './CandidateProfile'
import { formatYears } from './format'
import ScanMode from './ScanMode'
import UploadCVs from './UploadCVs'

// Each column shows this many cards, then a "Show more" button adds the next batch.
// Long columns stay short on a phone, and only visible cards are drawn.
const PAGE_SIZE = 20

// A moved card is a new element in its new column, so focus on the old one is lost.
// After React has re-rendered (next frame), put focus back on the card's new copy.
function focusSoon(elementId: string) {
  requestAnimationFrame(() => document.getElementById(elementId)?.focus())
}

type CardProps = {
  candidate: Candidate
  dragging: boolean
  onOpen: () => void
  onMove: (stage: Stage) => void
  onDragStart: () => void
  onDragEnd: () => void
}

function CandidateCard({ candidate, dragging, onOpen, onMove, onDragStart, onDragEnd }: CardProps) {
  const name = candidate.name ?? 'Name not found'
  const years = formatYears(candidate.years_experience)

  return (
    <li
      className={`candidate-card${dragging ? ' is-dragging' : ''}`}
      draggable
      onDragStart={(e) => {
        e.dataTransfer.effectAllowed = 'move'
        e.dataTransfer.setData('text/plain', name) // some browsers only start a drag with data set
        onDragStart()
      }}
      onDragEnd={onDragEnd}
    >
      {/* Compact on purpose: name, title, years and stage. The profile has the rest.
          The name gets the full width: it's what people look for. */}
      {/* The name is the button; CSS stretches its click area over the whole card. */}
      <button type="button" id={`candidate-${candidate.id}`} className="candidate-open" onClick={onOpen}>
        {name}
      </button>
      {candidate.current_title && <p className="candidate-meta">{candidate.current_title}</p>}
      <div className="card-bottom">
        <p className="candidate-meta">
          {years ?? (candidate.current_title ? '' : 'No work history found')}
        </p>
        <select
          id={`stage-${candidate.id}`}
          className="select stage-select"
          aria-label={`Stage for ${name}`}
          value={candidate.stage}
          onChange={(e) => onMove(e.target.value as Stage)}
        >
          {STAGES.map((stage) => (
            <option key={stage.id} value={stage.id}>{stage.label}</option>
          ))}
        </select>
      </div>
    </li>
  )
}

export default function Candidates({ role }: { role: Role }) {
  const [candidates, setCandidates] = useState<Candidate[] | null>(null) // null while loading
  const [loadError, setLoadError] = useState<string | null>(null)
  const [moveError, setMoveError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [openId, setOpenId] = useState<number | null>(null)
  const [draggedId, setDraggedId] = useState<number | null>(null)
  const [dropStage, setDropStage] = useState<Stage | null>(null)
  const [shownPerStage, setShownPerStage] = useState<Partial<Record<Stage, number>>>({})
  const [scanning, setScanning] = useState(false)
  const uploadButtonRef = useRef<HTMLButtonElement>(null)
  // Where focus goes when the profile closes: its card on the board, or the button in Scan mode.
  const profileReturnFocus = useRef<string | null>(null)

  useEffect(() => {
    api.listCandidates(role.id).then(setCandidates).catch((err: Error) => setLoadError(err.message))
  }, [role.id])

  const open = candidates?.find((c) => c.id === openId) ?? null

  function setStage(id: number, stage: Stage, onlyIf?: Stage) {
    setCandidates((prev) =>
      (prev ?? []).map((c) => (c.id === id && (!onlyIf || c.stage === onlyIf) ? { ...c, stage } : c)),
    )
  }

  // The card moves at once, then the change is saved. If saving fails, the card goes
  // back and a message says why. It only goes back if nobody has moved it again since.
  function moveCandidate(id: number, stage: Stage) {
    const candidate = candidates?.find((c) => c.id === id)
    if (!candidate || candidate.stage === stage) return
    const previous = candidate.stage
    setMoveError(null)
    // The moved card goes to the top of its new column, so it's never hidden behind "Show more".
    setCandidates((prev) => [{ ...candidate, stage }, ...(prev ?? []).filter((c) => c.id !== id)])
    api.moveCandidate(id, stage).catch((err: Error) => {
      setStage(id, previous, stage)
      setMoveError(`Couldn't move ${candidate.name ?? 'this candidate'}. ${err.message}`)
    })
  }

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

  // Scan mode saves its own changes (decisions, evidence checks) and hands back the result.
  // A candidate that changed stage goes to the top of its new column, as with moveCandidate.
  function handleScanUpdate(updated: Candidate) {
    setCandidates((prev) => {
      const list = prev ?? []
      const before = list.find((c) => c.id === updated.id)
      if (before && before.stage !== updated.stage) return [updated, ...list.filter((c) => c.id !== updated.id)]
      return list.map((c) => (c.id === updated.id ? updated : c))
    })
  }

  function openProfile(id: number, returnFocusTo: string) {
    profileReturnFocus.current = returnFocusTo
    setOpenId(id)
  }

  function endDrag() {
    setDraggedId(null)
    setDropStage(null)
  }

  return (
    <section className="candidates" aria-labelledby="candidates-title">
      <div className="section-header">
        <h2 id="candidates-title" className="section-title">
          Candidates {candidates && <span className="section-count">{candidates.length}</span>}
        </h2>
        {/* In the empty state, the button below is the one primary action. */}
        {candidates && candidates.length > 0 && (
          <div className="section-actions">
            <button id="scan-open" className="button button-secondary" onClick={() => setScanning(true)}>
              Scan mode
            </button>
            <button ref={uploadButtonRef} className="button button-secondary" onClick={() => setUploading(true)}>
              Upload CVs
            </button>
          </div>
        )}
      </div>

      {loadError && <p className="banner-error" role="alert">{loadError}</p>}
      {moveError && <p className="banner-error" role="alert">{moveError}</p>}

      {candidates && candidates.length === 0 && (
        <div className="candidates-empty">
          <p className="empty-text">No candidates yet. Upload CVs and we'll turn each one into a profile.</p>
          <button className="button button-primary" onClick={() => setUploading(true)}>
            Upload CVs
          </button>
        </div>
      )}

      {candidates && candidates.length > 0 && (
        <div className="board">
          {STAGES.map((stage) => {
            const inStage = candidates.filter((c) => c.stage === stage.id)
            const shown = shownPerStage[stage.id] ?? PAGE_SIZE
            const hidden = inStage.length - shown
            return (
              <section
                key={stage.id}
                className={`column${dropStage === stage.id ? ' is-drop-target' : ''}`}
                data-stage={stage.id}
                aria-labelledby={`column-${stage.id}`}
                // Only cards from this board are accepted. A file dragged in from outside is
                // left alone (draggedId is null), so it never counts as a move.
                onDragOver={(e) => {
                  if (draggedId === null) return
                  e.preventDefault()
                  setDropStage(stage.id)
                }}
                onDragLeave={(e) => {
                  if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setDropStage(null)
                }}
                onDrop={(e) => {
                  e.preventDefault()
                  if (draggedId !== null) moveCandidate(draggedId, stage.id)
                  endDrag()
                }}
              >
                <h3 id={`column-${stage.id}`} className="column-title">
                  <span className="stage-dot" aria-hidden="true" />
                  {stage.label} <span className="req-count">{inStage.length}</span>
                </h3>
                {inStage.length > 0 ? (
                  <ul className="column-cards">
                    {inStage.slice(0, shown).map((candidate) => (
                      <CandidateCard
                        key={candidate.id}
                        candidate={candidate}
                        dragging={draggedId === candidate.id}
                        onOpen={() => openProfile(candidate.id, `candidate-${candidate.id}`)}
                        onMove={(next) => {
                          moveCandidate(candidate.id, next)
                          focusSoon(`stage-${candidate.id}`)
                        }}
                        onDragStart={() => setDraggedId(candidate.id)}
                        onDragEnd={endDrag}
                      />
                    ))}
                  </ul>
                ) : (
                  <p className="column-empty">No candidates</p>
                )}
                {hidden > 0 && (
                  <button
                    type="button"
                    className="button button-secondary show-more"
                    onClick={() => {
                      setShownPerStage((prev) => ({ ...prev, [stage.id]: shown + PAGE_SIZE }))
                      // Keyboard users carry on from the first card that just appeared.
                      focusSoon(`candidate-${inStage[shown].id}`)
                    }}
                  >
                    Show {Math.min(PAGE_SIZE, hidden)} more ({hidden} left)
                  </button>
                )}
              </section>
            )
          })}
        </div>
      )}

      {scanning && candidates && (
        <ScanMode
          candidates={candidates}
          onClose={() => {
            setScanning(false)
            focusSoon('scan-open')
          }}
          onUpdate={handleScanUpdate}
          onOpenProfile={(id) => openProfile(id, 'scan-profile')}
        />
      )}

      <UploadCVs
        roleId={role.id}
        open={uploading}
        onClose={closeUpload}
        onUploaded={handleUploaded}
      />
      <CandidateProfile
        candidate={open}
        moveError={moveError}
        onClose={() => {
          if (profileReturnFocus.current) focusSoon(profileReturnFocus.current)
          setOpenId(null)
        }}
        onMove={(stage) => open && moveCandidate(open.id, stage)}
      />
    </section>
  )
}
