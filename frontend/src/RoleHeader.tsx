// Shows the selected role: title, location and the requirements the LLM extracted.

import type { Requirement, Role } from './api'

function RequirementGroup({ label, items }: { label: string; items: Requirement[] }) {
  if (items.length === 0) return null
  return (
    <div className="req-group">
      <h3 className="req-label">
        {label} <span className="req-count">{items.length}</span>
      </h3>
      <ul className="chips">
        {items.map((item, index) => (
          <li key={index} className="chip">{item.text}</li>
        ))}
      </ul>
    </div>
  )
}

export default function RoleHeader({ role }: { role: Role }) {
  const mustHave = role.requirements.filter((r) => r.must_have)
  const niceToHave = role.requirements.filter((r) => !r.must_have)

  return (
    <section className="role" aria-labelledby="role-title">
      <h1 id="role-title" className="role-title">{role.title}</h1>
      <p className="role-location">{role.location ?? 'Location not specified'}</p>

      <div className="req-groups">
        <RequirementGroup label="Must-have" items={mustHave} />
        <RequirementGroup label="Nice to have" items={niceToHave} />
        {role.excluded_criteria.length > 0 && (
          <div className="req-group">
            <h3 className="req-label">
              Not used for screening <span className="req-count">{role.excluded_criteria.length}</span>
            </h3>
            <p className="req-hint">
              These are about who someone is, not what they can do, so they weren't added as requirements.
            </p>
            <ul className="chips">
              {role.excluded_criteria.map((text, index) => (
                <li key={index} className="chip chip-excluded">{text}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <details className="jd">
        <summary>Original job description</summary>
        <p className="jd-text">{role.description}</p>
      </details>
    </section>
  )
}
