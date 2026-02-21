/**
 * Thin HTTP client.
 *
 * All API calls go through `request` so error handling is centralised.
 * Errors from the backend carry `error` (human message) and `code` (machine code).
 */

async function request(method, path, body) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) {
    options.body = JSON.stringify(body)
  }

  const res = await fetch(path, options)

  if (res.status === 204) return null

  const json = await res.json()

  if (!res.ok) {
    const err = new Error(json.error ?? 'Request failed')
    err.code = json.code
    throw err
  }

  return json
}

export const api = {
  getProjects: () =>
    request('GET', '/projects/'),

  createProject: (data) =>
    request('POST', '/projects/', data),

  deleteProject: (id) =>
    request('DELETE', `/projects/${id}`),

  getProjectTasks: (projectId, filters = {}) => {
    const qs = new URLSearchParams(filters).toString()
    return request('GET', `/projects/${projectId}/tasks${qs ? `?${qs}` : ''}`)
  },

  createTask: (projectId, data) =>
    request('POST', `/projects/${projectId}/tasks`, data),

  getTask: (taskId) =>
    request('GET', `/tasks/${taskId}`),

  updateTask: (taskId, data) =>
    request('PUT', `/tasks/${taskId}`, data),
}
