import { useState } from 'react'
import ProjectDetail from './components/ProjectDetail.jsx'
import ProjectList from './components/ProjectList.jsx'

const styles = {
  root: {
    maxWidth: 760,
    margin: '0 auto',
    padding: '24px 16px',
    fontFamily: 'monospace',
  },
  header: {
    borderBottom: '2px solid #1a1a1a',
    paddingBottom: 12,
    marginBottom: 24,
  },
}

export default function App() {
  const [selectedProject, setSelectedProject] = useState(null)

  return (
    <div style={styles.root}>
      <header style={styles.header}>
        <h1 style={{ margin: 0, fontSize: '1.4rem' }}>Task Tracker</h1>
      </header>
      {selectedProject ? (
        <ProjectDetail
          project={selectedProject}
          onBack={() => setSelectedProject(null)}
        />
      ) : (
        <ProjectList onSelect={setSelectedProject} />
      )}
    </div>
  )
}
