// The one page of the ATS: header with role picker, the selected role, and (later) its pipeline.

import { useEffect, useState } from 'react'
import { api, type Role } from './api'
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
    setCreating(false)
  }

  return (
    <>
      <header className="topbar">
        <img src="/ovi-logo.svg" alt="OVI" className="logo" width={57} height={28} />

        <div className="topbar-actions">
          {role && roles && (
            <label className="role-picker">
              <span className="role-picker-label">Role</span>
              <select
                className="select"
                value={role.id}
                onChange={(e) => selectRole(Number(e.target.value))}
              >
                {roles.map((r) => (
                  <option key={r.id} value={r.id}>{r.title}</option>
                ))}
              </select>
            </label>
          )}
          {/* In the empty state, the page's own button is the one primary action. */}
          {role && (
            <button className="button button-primary" onClick={() => setCreating(true)}>
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
      </main>

      <RoleSetup
        open={creating}
        onClose={() => setCreating(false)}
        onCreated={handleCreated}
      />
    </>
  )
}
