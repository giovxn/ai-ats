// Types that mirror backend/schemas.py, plus one small fetch helper per endpoint.

export type Requirement = { text: string; must_have: boolean }

export type Role = {
  id: number
  title: string
  location: string | null
  requirements: Requirement[]
  description: string
  created_at: string
}

// FastAPI errors are { detail: string } for our own errors,
// or { detail: [{ msg }] } for request validation errors.
function errorMessage(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg)
  if (status >= 500) return 'Unable to reach the server. Check that the backend is running.'
  return `Request failed (${status}).`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, init)
  } catch {
    throw new Error('Unable to reach the server. Check that the backend is running.')
  }
  const body = await response.json().catch(() => null)
  if (!response.ok) throw new Error(errorMessage(body, response.status))
  return body as T
}

export const api = {
  listRoles: () => request<Role[]>('/roles'),

  createRole: (description: string) =>
    request<Role>('/roles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    }),
}
