import { Link, Outlet } from 'react-router-dom'

export function Layout() {
  return (
    <div style={{ fontFamily: 'system-ui', minHeight: '100vh' }}>
      <header style={{ borderBottom: '1px solid #ddd', padding: '16px 24px', background: '#f8f9fa' }}>
        <nav style={{ maxWidth: 820, margin: '0 auto', display: 'flex', alignItems: 'center', gap: 24 }}>
          <Link to="/" style={{ textDecoration: 'none', color: '#0070f3', fontWeight: 600 }}>
            VibeForge
          </Link>
          <span style={{ fontSize: '0.9em', opacity: 0.6 }}>Local UI MVP</span>
          <Link to="/control" style={{ textDecoration: 'none', color: '#1a237e', fontWeight: 500 }}>
            Control Panel
          </Link>
        </nav>
      </header>

      <main style={{ padding: 24, maxWidth: 820, margin: '0 auto' }}>
        <Outlet />
      </main>

      <footer style={{ borderTop: '1px solid #ddd', padding: '16px 24px', marginTop: 48, textAlign: 'center', opacity: 0.6, fontSize: '0.85em' }}>
        <p>VibeForge MVP - Cloud-first skeleton generator</p>
      </footer>
    </div>
  )
}
