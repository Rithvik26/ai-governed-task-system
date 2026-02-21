import { useState } from 'react'
import { api } from '../api/client.js'

export default function CreateTaskForm({ projectId, onCreated }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [priority, setPriority] = useState('medium')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    api
      .createTask(projectId, {
        title,
        description: description || undefined,
        priority,
      })
      .then(onCreated)
      .catch((err) => setError(err.message))
      .finally(() => setSubmitting(false))
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{ border: '1px solid #ccc', padding: 16, marginBottom: 16, background: '#fff' }}
    >
      <h4 style={{ margin: '0 0 12px' }}>New Task</h4>
      {error && <p style={{ color: '#c00', margin: '0 0 8px' }}>{error}</p>}
      <div style={{ marginBottom: 8 }}>
        <label style={{ display: 'block', marginBottom: 4 }}>Title *</label>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          style={{ width: '100%', padding: 6, fontFamily: 'inherit' }}
        />
      </div>
      <div style={{ marginBottom: 8 }}>
        <label style={{ display: 'block', marginBottom: 4 }}>Description</label>
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          style={{ width: '100%', padding: 6, fontFamily: 'inherit' }}
        />
      </div>
      <div style={{ marginBottom: 12 }}>
        <label style={{ display: 'block', marginBottom: 4 }}>Priority</label>
        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          style={{ padding: 6, fontFamily: 'inherit' }}
        >
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
        </select>
      </div>
      <button type="submit" disabled={submitting} style={{ fontFamily: 'inherit' }}>
        {submitting ? 'Creating…' : 'Create Task'}
      </button>
    </form>
  )
}
