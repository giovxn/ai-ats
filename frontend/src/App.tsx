// The one page of the ATS: header with role picker, the selected role and its candidates.

import { useEffect, useRef, useState } from 'react'
import { api, type Role } from './api'
import Candidates from './Candidates'
import RoleHeader from './RoleHeader'
import RoleSetup from './RoleSetup'

// The selected role lives in the URL (?role=3), so a reload keeps your place.
function roleIdFromUrl(): number | null {
  const value = new URLSearchParams(window.location.search).get('role')
  return value ? Number(value) : null
}

export default function App() {
  const [roles, setRoles] = useState<Role[] | null>(null) // null while loading
  const [loadError, setLoadError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(roleIdFromUrl)
  const [creating, setCreating] = useState(false)
  const newRoleButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    api.listRoles().then(setRoles).catch((err: Error) => setLoadError(err.message))
  }, [])

  const role = roles?.find((r) => r.id === selectedId) ?? roles?.[0] ?? null

  function selectRole(id: number) {
    setSelectedId(id)
    window.history.replaceState(null, '', `?role=${id}`)
  }

  function handleCreated(newRole: Role) {
    setRoles((prev) => [newRole, ...(prev ?? [])])
    selectRole(newRole.id)
    closeRoleSetup()
  }

  // The empty state's button disappears after the first role is created, so move
  // focus to the header's button once the dialog has closed.
  function closeRoleSetup() {
    setCreating(false)
    requestAnimationFrame(() => newRoleButtonRef.current?.focus())
  }

  return (
    <>
      <header className="topbar">
        {/* The OVI mark plus a light lowercase "× gio", sized and weighted to sit with "ovi". */}
        <div className="logo-lockup" role="img" aria-label="OVI x Gio">
          <img src="/ovi-logo.svg" alt="" className="logo" width={57} height={28} />
          <span className="logo-collab" aria-hidden="true">
            <span className="logo-times">×</span>gio
          </span>
        </div>

        <div className="topbar-actions">
          {role && roles && (
            <div className="role-picker">
              <label htmlFor="role-picker" className="role-picker-label">Role</label>
              <select
                id="role-picker"
                className="select"
                value={role.id}
                onChange={(e) => selectRole(Number(e.target.value))}
              >
                {roles.map((r) => (
                  <option key={r.id} value={r.id}>{r.title}</option>
                ))}
              </select>
            </div>
          )}
          {/* In the empty state, the page's own button is the one primary action. */}
          {role && (
            <button ref={newRoleButtonRef} className="button button-primary" onClick={() => setCreating(true)}>
              New role
            </button>
          )}
        </div>
      </header>

      <main className="page">
        {loadError && <p className="banner-error" role="alert">{loadError}</p>}

        {roles && roles.length === 0 && (
          <div className="empty">
            <h1 className="empty-title">No roles yet</h1>
            <p className="empty-text">
              Create a role from a job description, then upload CVs to it.
            </p>
            <button className="button button-primary" onClick={() => setCreating(true)}>
              New role
            </button>
          </div>
        )}

        {role && <RoleHeader role={role} />}
        {role && <Candidates key={role.id} role={role} />}
      </main>

      <RoleSetup
        open={creating}
        onClose={closeRoleSetup}
        onCreated={handleCreated}
      />
    </>
  )
}
