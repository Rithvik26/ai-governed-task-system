import { useEffect, useState } from 'react'
import { api } from '../api/client.js'
import CreateProjectForm from './CreateProjectForm.jsx'

export default function ProjectList({ onSelect }) {
  const [projects, setProjects] = useState([])
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)

  const load = () => {
    api
      .getProjects()
      .then(setProjects)
      .catch((err) => setError(err.message))
  }

  useEffect(load, [])

  const handleDelete = (e, id) => {
    e.stopPropagation()
    if (!window.confirm('Delete this project and all its tasks?')) return
    api
      .deleteProject(id)
      .then(load)
      .catch((err) => setError(err.message))
  }

  const handleCreated = () => {
    setShowForm(false)
    load()
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h2 style={{ margin: 0 }}>Projects</h2>
        <button onClick={() => setShowForm((v) => !v)} style={{ fontFamily: 'inherit' }}>
          {showForm ? 'Cancel' : '+ New Project'}
        </button>
      </div>

      {error && <p style={{ color: '#c00' }}>Error: {error}</p>}

      {showForm && <CreateProjectForm onCreated={handleCreated} />}

      {projects.length === 0 && !showForm && (
        <p style={{ color: '#666' }}>No projects yet. Create one to get started.</p>
      )}

      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {projects.map((p) => (
          <li
            key={p.id}
            onClick={() => onSelect(p)}
            style={{
              border: '1px solid #ccc',
              padding: '12px 16px',
              marginBottom: 8,
              background: '#fff',
              cursor: 'pointer',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
            }}
          >
            <div>
              <strong>{p.name}</strong>
              {p.description && (
                <p style={{ margin: '4px 0 0', color: '#555', fontSize: '0.9em' }}>
                  {p.description}
                </p>
              )}
            </div>
            <button
              onClick={(e) => handleDelete(e, p.id)}
              style={{ fontFamily: 'inherit', marginLeft: 12, flexShrink: 0 }}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
