// Block 1: the "New role" dialog. Paste a job description, the backend's LLM
// extracts title, location and requirements, and the new role is returned.

import { useEffect, useId, useRef, useState } from 'react'
import { api, type Role } from './api'

const MIN_LENGTH = 50

type Props = {
  open: boolean
  onClose: () => void
  onCreated: (role: Role) => void
}

export default function RoleSetup({ open, onClose, onCreated }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const errorId = useId()
  const hintId = useId()

  // Native <dialog>: showModal() traps focus, dims the page and closes on Escape.
  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (open && !dialog.open) {
      setDescription('')
      setError(null)
      dialog.showModal()
    } else if (!open && dialog.open) {
      dialog.close()
    }
  }, [open])

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (submitting) return

    if (description.trim().length < MIN_LENGTH) {
      setError('Paste the full job description. It needs at least 50 characters.')
      textareaRef.current?.focus()
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      const role = await api.createRole(description.trim())
      onCreated(role)
    } catch (err) {
      setError((err as Error).message)
      textareaRef.current?.focus()
    } finally {
      setSubmitting(false)
    }
  }

  // While the request runs it can't be cancelled: the backend still finishes the
  // OpenAI call and saves the role. So the dialog stays open until it's done,
  // instead of a Cancel that hides the dialog and the role appears anyway.
  function blockCloseWhileSubmitting(event: React.SyntheticEvent) {
    if (submitting) event.preventDefault()
  }

  return (
    <dialog
      ref={dialogRef}
      className="dialog"
      aria-labelledby="new-role-title"
      onClose={onClose}
      onCancel={blockCloseWhileSubmitting}
      onKeyDown={(e) => e.key === 'Escape' && blockCloseWhileSubmitting(e)}
    >
      <form onSubmit={handleSubmit} noValidate>
        <h2 id="new-role-title" className="dialog-title">New role</h2>

        <label htmlFor="jd" className="field-label">Job description</label>
        <p id={hintId} className="field-hint">
          Paste the full posting. We'll pull out the title, location and requirements.
        </p>
        <textarea
          id="jd"
          ref={textareaRef}
          className="textarea"
          rows={14}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="We're hiring a Senior Accountant in Abu Dhabi to lead the month-end close…"
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${hintId} ${errorId}` : hintId}
          autoFocus
        />
        {error && (
          <p id={errorId} className="field-error">{error}</p>
        )}

        <div className="dialog-actions">
          <button
            type="button"
            className="button button-secondary"
            onClick={onClose}
            disabled={submitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="button button-primary"
            aria-disabled={submitting || undefined}
          >
            {submitting ? 'Reading job description…' : 'Create role'}
          </button>
        </div>
        <p className="visually-hidden" role="status">
          {submitting ? 'Reading the job description. This takes a few seconds.' : ''}
        </p>
      </form>
    </dialog>
  )
}
