import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
// L10b (2026-09-27): B10 verbatim skin (1:1 style replication). Loaded AFTER
// index.css so the B10 skin classes win; data still comes from the v3
// snapshot projection, styles come 1:1 from the UI-suite B10 source.
import './skins/b10.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
