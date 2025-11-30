const API_URL =
    import.meta.env.VITE_API_URL || 'http://localhost:5000';

export const API_ENDPOINTS = {
    jobRoles: `${API_URL}/api/job-roles`,
    process: `${API_URL}/api/process`,
    health: `${API_URL}/api/health`
};

export default API_URL;