import { useCallback, useEffect, useState } from 'react'
import { Minus, Square, X, Plus, RotateCcw } from 'lucide-react'

/**
 * Native window chrome for the Tauri shell.
 *
 * Both windows are declared `decorations: false` in tauri.conf.json, so the
 * operating system draws no title bar: without these controls the window can be
 * neither moved nor closed from inside the app. Shell operations only - the
 * Observer stays read-only and this component issues no business write.
 */
const ZOOM_STEP = 0.1
const ZOOM_MIN = 0.6
const ZOOM_MAX = 2.0

function inTauri(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window
}

export function WindowControls() {
  const [tauri, setTauri] = useState(false)
  const [zoom, setZoomState] = useState(1)

  useEffect(() => setTauri(inTauri()), [])

  const win = useCallback(async () => {
    const { getCurrentWindow } = await import('@tauri-apps/api/window')
    return getCurrentWindow()
  }, [])

  const minimize = useCallback(async () => {
    try { (await win()).minimize() } catch { /* not under Tauri */ }
  }, [win])

  const toggleMaximize = useCallback(async () => {
    try { (await win()).toggleMaximize() } catch { /* not under Tauri */ }
  }, [win])

  const close = useCallback(async () => {
    try { (await win()).close() } catch { /* not under Tauri */ }
  }, [win])

  const setZoom = useCallback(async (next: number) => {
    const clamped = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Number(next.toFixed(2))))
    setZoomState(clamped)
    try {
      const { getCurrentWebview } = await import('@tauri-apps/api/webview')
      await getCurrentWebview().setZoom(clamped)
    } catch { /* browser entry has native zoom */ }
  }, [])

  // Ctrl/Cmd + = / - / 0 is the desktop expectation for a webview shell.
  useEffect(() => {
    if (!tauri) return
    const onKey = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey)) return
      if (e.key === '=' || e.key === '+') { e.preventDefault(); void setZoom(zoom + ZOOM_STEP) }
      else if (e.key === '-') { e.preventDefault(); void setZoom(zoom - ZOOM_STEP) }
      else if (e.key === '0') { e.preventDefault(); void setZoom(1) }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [tauri, zoom, setZoom])

  if (!tauri) return null

  return (
    <div className="winctl" role="group" aria-label="窗口控制">
      <div className="winctl-zoomgroup">
      <button
        type="button"
        className="winctl-btn"
        onClick={() => void setZoom(zoom - ZOOM_STEP)}
        aria-label="缩小界面"
        title={`缩小 (Ctrl −)`}
      >
        <Minus size={13} aria-hidden="true" />
      </button>
      <span className="winctl-zoom" aria-live="off">{Math.round(zoom * 100)}%</span>
      <button
        type="button"
        className="winctl-btn"
        onClick={() => void setZoom(zoom + ZOOM_STEP)}
        aria-label="放大界面"
        title="放大 (Ctrl +)"
      >
        <Plus size={13} aria-hidden="true" />
      </button>
      <button
        type="button"
        className="winctl-btn"
        onClick={() => void setZoom(1)}
        aria-label="重置缩放"
        title="重置缩放 (Ctrl 0)"
      >
        <RotateCcw size={12} aria-hidden="true" />
      </button>
      <span className="winctl-sep" aria-hidden="true" />
      </div>
      <button
        type="button"
        className="winctl-btn"
        onClick={() => void minimize()}
        aria-label="最小化窗口"
        title="最小化"
      >
        <Minus size={13} aria-hidden="true" />
      </button>
      <button
        type="button"
        className="winctl-btn"
        onClick={() => void toggleMaximize()}
        aria-label="最大化或还原窗口"
        title="最大化 / 还原"
      >
        <Square size={11} aria-hidden="true" />
      </button>
      <button
        type="button"
        className="winctl-btn winctl-close"
        onClick={() => void close()}
        aria-label="关闭窗口"
        title="关闭"
      >
        <X size={13} aria-hidden="true" />
      </button>
    </div>
  )
}
