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

// The pipeline's columns, in order. Same four stages as schemas.Stage in the backend.
export const STAGES: { id: Stage; label: string }[] = [
  { id: 'new', label: 'New' },
  { id: 'shortlisted', label: 'Shortlisted' },
  { id: 'interview', label: 'Interview' },
  { id: 'rejected', label: 'Rejected' },
]

// Block 4: where each requirement shows up in the CV. Quotes come from the AI;
// "verified" and "buried" are decided by plain code in the backend (evidence.py).
export type EvidenceTag = 'duty' | 'action' | 'outcome'
// Describes the CV, not the person. "unverified": the AI said the CV shows it, but none of its quotes
// could be matched to the CV text, so it's never shown as found.
export type EvidenceStatus = 'demonstrated' | 'partial' | 'not_found' | 'unverified'

export type Quote = {
  text: string
  job_index: number | null // position in Candidate.jobs, most recent first; null for summary, skills...
  tags: EvidenceTag[]
  verified: boolean // found in the CV text, inside that job's section
}

export type RequirementEvidence = {
  text: string
  must_have: boolean
  status: EvidenceStatus
  quotes: Quote[]
  buried: boolean // must-have with verified evidence only in jobs older than the last 2
}

export type Evidence = {
  requirements: RequirementEvidence[]
  highlight_tags: EvidenceTag[][][] // [job 1, job 2] -> tags per highlight
  sections_found: boolean
}

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
  // Found in the CV text by code, not by the AI.
  email: string | null
  phone: string | null
  links: string[] // LinkedIn, GitHub, a portfolio...
  evidence_status: 'pending' | 'complete' | 'failed'
  evidence: Evidence | null // only when evidence_status is "complete"
  created_at: string
}

export type PromptChoice = 'look_again' | 'reject_anyway'

export type Decision = {
  id: number
  candidate_id: number
  from_stage: Stage
  to_stage: Stage
  prompt_shown: boolean
  prompt_choice: PromptChoice | null
  undo_of: number | null
  created_at: string
}

export type DecisionInput = {
  to_stage: Stage
  prompt_shown?: boolean
  prompt_choice?: PromptChoice
  undo_of?: number
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

  moveCandidate: (id: number, stage: Stage) =>
    request<Candidate>(`/candidates/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage }),
    }),

  // Block 4. Runs the evidence check again (e.g. it failed at upload).
  checkEvidence: (id: number) => request<Candidate>(`/candidates/${id}/evidence`, { method: 'POST' }),

  // Block 4. A Scan mode decision: moves the candidate (unless it's "Look again") and logs it.
  decide: (id: number, input: DecisionInput) =>
    request<{ candidate: Candidate; decision: Decision }>(`/candidates/${id}/decisions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    }),
}
