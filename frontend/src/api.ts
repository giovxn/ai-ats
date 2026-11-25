// Types that mirror backend/schemas.py, plus one small fetch helper per endpoint.

export type Requirement = { text: string; must_have: boolean }

export type Role = {
  id: number
  title: string
  location: string | null
  requirements: Requirement[]
  excluded_criteria: string[] // e.g. "Male candidates only": shown, never used
  description: string
  created_at: string
}

export type Job = {
  title: string
  company: string | null
  start: string | null // "YYYY-MM" or "YYYY"
  end: string | null
  is_current: boolean
  highlights: string[]
}

export type Education = { qualification: string; institution: string | null; year: string | null }

export type Stage = 'new' | 'shortlisted' | 'interview' | 'rejected'

export type Candidate = {
  id: number
  role_id: number
  stage: Stage
  name: string | null
  current_title: string | null
  years_experience: number | null
  skills: string[]
  jobs: Job[]
  education: Education[]
  summary: string
  cv_filename: string
  cv_text: string
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

  listCandidates: (roleId: number) => request<Candidate[]>(`/roles/${roleId}/candidates`),

  // One file per request; the browser sets the multipart Content-Type itself.
  uploadCV: (roleId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<Candidate>(`/roles/${roleId}/candidates`, { method: 'POST', body: form })
  },
}
