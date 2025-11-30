export default function JobRoleSelector({ roles, selectedRole, onChange }) {
  return (
    <div className="job-role-selector">
      <label htmlFor="role-select" className="role-label">
        Select Job Role <span className="required">*</span>
      </label>
      <select 
        id="role-select"
        value={selectedRole} 
        onChange={(e) => onChange(e.target.value)} 
        className="role-select"
        required
      >
        <option value="">-- Select a Job Role --</option>
        {roles.map(role => (
          <option key={role} value={role}>{role}</option>
        ))}
      </select>
    </div>
  )
}
