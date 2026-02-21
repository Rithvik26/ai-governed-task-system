import { useState } from 'react'
import { api } from '../api/client.js'

// Mirrors VALID_TRANSITIONS in models.py — kept in sync manually.
// The backend will reject any illegal move; this is UI-only guidance.
const NEXT_STATUSES = {
  todo: ['in_progress'],
  in_progress: ['done'],
  done: [],
}

const STATUS_COLOR = {
  todo: '#888',
  in_progress: '#b07000',
  done: '#2a7a2a',
}

const PRIORITY_LABEL = {
  low: '▽ low',
  medium: '◇ medium',
  high: '▲ high',
}

export default function TaskItem({ task, onUpdated }) {
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleTransition = (newStatus) => {
    setError(null)
    setLoading(true)
    api
      .updateTask(task.id, { status: newStatus })
      .then(onUpdated)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  const next = NEXT_STATUSES[task.status] ?? []

  return (
    <div
      style={{
        border: '1px solid #ccc',
        padding: '12px 16px',
        marginBottom: 8,
        background: '#fff',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong>{task.title}</strong>
        <span style={{ color: STATUS_COLOR[task.status], fontSize: '0.85em', fontWeight: 'bold' }}>
          {task.status}
        </span>
      </div>

      <div style={{ color: '#666', fontSize: '0.8em', marginTop: 4 }}>
        {PRIORITY_LABEL[task.priority]}
      </div>

      {task.description && (
        <p style={{ margin: '6px 0 0', fontSize: '0.9em', color: '#444' }}>
          {task.description}
        </p>
      )}

      {error && (
        <p style={{ color: '#c00', fontSize: '0.85em', margin: '6px 0 0' }}>{error}</p>
      )}

      {next.length > 0 && (
        <div style={{ marginTop: 10 }}>
          {next.map((s) => (
            <button
              key={s}
              disabled={loading}
              onClick={() => handleTransition(s)}
              style={{ fontFamily: 'inherit', marginRight: 8 }}
            >
              → {s}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
