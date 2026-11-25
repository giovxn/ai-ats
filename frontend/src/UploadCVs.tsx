// Block 2: the "Upload CVs" dialog. Drop or pick several PDF or .txt files. Each file
// is sent on its own request (3 at a time), so each one shows its own progress and
// succeeds or fails on its own.

import { useEffect, useRef, useState } from 'react'
import { api, type Candidate } from './api'

const PARALLEL_UPLOADS = 3

type Status = 'waiting' | 'reading' | 'done' | 'failed'
type Upload = { id: number; file: File; status: Status; message?: string }

type Props = {
  roleId: number
  open: boolean
  onClose: () => void
  onUploaded: (candidate: Candidate) => void
}

const STATUS_TEXT: Record<Status, string> = {
  waiting: 'Waiting',
  reading: 'Reading CV…',
  done: 'Added',
  failed: 'Failed',
}

export default function UploadCVs({ roleId, open, onClose, onUploaded }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const [uploads, setUploads] = useState<Upload[]>([])
  const [dragging, setDragging] = useState(false)
  const queue = useRef<Upload[]>([]) // files not started yet
  const running = useRef(0) // requests in flight
  const nextId = useRef(0)

  const busy = uploads.some((u) => u.status === 'waiting' || u.status === 'reading')
  const done = uploads.filter((u) => u.status === 'done').length
  const failed = uploads.filter((u) => u.status === 'failed').length

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (open && !dialog.open) {
      setUploads([])
      dialog.showModal()
    } else if (!open && dialog.open) {
      dialog.close()
    }
  }, [open])

  function update(id: number, changes: Partial<Upload>) {
    setUploads((prev) => prev.map((u) => (u.id === id ? { ...u, ...changes } : u)))
  }

  // Start queued files until PARALLEL_UPLOADS are running; each finished one starts the next.
  function startNext() {
    while (running.current < PARALLEL_UPLOADS && queue.current.length > 0) {
      const upload = queue.current.shift()!
      running.current += 1
      update(upload.id, { status: 'reading' })
      api
        .uploadCV(roleId, upload.file)
        .then((candidate) => {
          update(upload.id, { status: 'done', message: candidate.name ?? 'Name not found' })
          onUploaded(candidate)
        })
        .catch((err: Error) => update(upload.id, { status: 'failed', message: err.message }))
        .finally(() => {
          running.current -= 1
          startNext()
        })
    }
  }

  function addFiles(files: FileList | null) {
    if (!files || files.length === 0) return
    const added = Array.from(files, (file) => ({ id: nextId.current++, file, status: 'waiting' as const }))
    setUploads((prev) => [...prev, ...added])
    queue.current.push(...added)
    startNext()
  }

  // Same rule as "New role": uploads can't be stopped once sent, so the dialog
  // stays open until they finish instead of hiding work that is still running.
  function blockCloseWhileBusy(event: React.SyntheticEvent) {
    if (busy) event.preventDefault()
  }

  return (
    <dialog
      ref={dialogRef}
      className="dialog"
      aria-labelledby="upload-title"
      onClose={onClose}
      onCancel={blockCloseWhileBusy}
      onKeyDown={(e) => e.key === 'Escape' && blockCloseWhileBusy(e)}
      // A file dropped beside the drop area would otherwise open in the tab and leave the app.
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => e.preventDefault()}
    >
      <h2 id="upload-title" className="dialog-title">Upload CVs</h2>

      <label
        htmlFor="cv-files"
        className={`dropzone${dragging ? ' is-dragging' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
          addFiles(e.dataTransfer.files)
        }}
      >
        <span className="dropzone-title">Drop CVs here or choose files</span>
        <span className="dropzone-hint">PDF or .txt, up to 5 MB each. You can add several at once.</span>
        <input
          id="cv-files"
          type="file"
          className="visually-hidden"
          accept=".pdf,.txt,application/pdf,text/plain"
          multiple
          onChange={(e) => {
            addFiles(e.target.files)
            e.target.value = '' // so the same file can be picked again
          }}
        />
      </label>

      {uploads.length > 0 && (
        <ul className="upload-list" aria-label="Files">
          {uploads.map((u) => (
            <li key={u.id} className="upload-row">
              <span className="upload-file">{u.file.name}</span>
              <span className={`upload-status is-${u.status}`}>
                {STATUS_TEXT[u.status]}
                {u.message && `: ${u.message}`}
              </span>
            </li>
          ))}
        </ul>
      )}

      <div className="dialog-actions upload-actions">
        <p className="upload-summary" role="status">
          {uploads.length === 0
            ? ''
            : busy
              ? `${done + failed} of ${uploads.length} done…`
              : `${done} added${failed ? `, ${failed} failed` : ''}.`}
        </p>
        <button type="button" className="button button-primary" onClick={onClose} disabled={busy}>
          Done
        </button>
      </div>
    </dialog>
  )
}
