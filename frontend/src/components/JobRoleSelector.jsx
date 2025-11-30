export default function JobRoleSelector({ roles, selectedRole, onChange }) {
  return (
    <div className="job-role-selector">
      <label>Select Job Role *</label>
      <select
        value={selectedRole}
        onChange={(e) => onChange(e.target.value)}
        className="role-select"
      >
        {roles.map(role => (
          <option key={role} value={role}>
            {role}
          </option>
        ))}
      </select>
    </div>
  )
}
