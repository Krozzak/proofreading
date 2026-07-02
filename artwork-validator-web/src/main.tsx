import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

declare global {
  interface Window {
    __avwMarkBooted?: () => void
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// Tell the boot-diagnostics harness (index.html) that the app mounted, so it
// doesn't show the troubleshooting panel.
window.__avwMarkBooted?.()
