import { useState } from 'react'
import { api } from '../api/client.js'

export default function CreateProjectForm({ onCreated }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    api
      .createProject({ name, description: description || undefined })
      .then(onCreated)
      .catch((err) => setError(err.message))
      .finally(() => setSubmitting(false))
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{ border: '1px solid #ccc', padding: 16, marginBottom: 16, background: '#fff' }}
    >
      <h3 style={{ margin: '0 0 12px' }}>New Project</h3>
      {error && <p style={{ color: '#c00', margin: '0 0 8px' }}>{error}</p>}
      <div style={{ marginBottom: 8 }}>
        <label style={{ display: 'block', marginBottom: 4 }}>Name *</label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          style={{ width: '100%', padding: 6, fontFamily: 'inherit' }}
        />
      </div>
      <div style={{ marginBottom: 12 }}>
        <label style={{ display: 'block', marginBottom: 4 }}>Description</label>
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          style={{ width: '100%', padding: 6, fontFamily: 'inherit' }}
        />
      </div>
      <button type="submit" disabled={submitting} style={{ fontFamily: 'inherit' }}>
        {submitting ? 'Creating…' : 'Create Project'}
      </button>
    </form>
  )
}
