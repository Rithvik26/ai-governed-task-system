import { useEffect, useState } from 'react'
import { api } from '../api/client.js'
import CreateTaskForm from './CreateTaskForm.jsx'
import TaskItem from './TaskItem.jsx'

export default function ProjectDetail({ project, onBack }) {
  const [tasks, setTasks] = useState([])
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)

  const load = () => {
    api
      .getProjectTasks(project.id)
      .then(setTasks)
      .catch((err) => setError(err.message))
  }

  useEffect(load, [project.id])

  return (
    <div>
      <button onClick={onBack} style={{ fontFamily: 'inherit', marginBottom: 16 }}>
        ← Back to Projects
      </button>

      <h2 style={{ margin: '0 0 4px' }}>{project.name}</h2>
      {project.description && (
        <p style={{ margin: '0 0 16px', color: '#555' }}>{project.description}</p>
      )}

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 12,
        }}
      >
        <h3 style={{ margin: 0 }}>Tasks ({tasks.length})</h3>
        <button
          onClick={() => setShowForm((v) => !v)}
          style={{ fontFamily: 'inherit' }}
        >
          {showForm ? 'Cancel' : '+ New Task'}
        </button>
      </div>

      {error && <p style={{ color: '#c00' }}>Error: {error}</p>}

      {showForm && (
        <CreateTaskForm
          projectId={project.id}
          onCreated={() => {
            setShowForm(false)
            load()
          }}
        />
      )}

      {tasks.length === 0 && !showForm && (
        <p style={{ color: '#666' }}>No tasks yet.</p>
      )}

      {tasks.map((task) => (
        <TaskItem key={task.id} task={task} onUpdated={load} />
      ))}
    </div>
  )
}
