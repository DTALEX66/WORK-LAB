// WORK-LAB Observer — Tauri portable shell.
// Portable (no install), double-click to run, copy to update.
// Two surfaces:
//   A) "main"    — full desktop window (Full/Compact x Dark/Light observer UI)
//   B) "panel"   — compact floating panel opened from the system tray
// The UI is the static web/ frontend (Apple Liquid Glass). Read-only by design.

use tauri::{
    AppHandle, Manager, PhysicalPosition, PhysicalSize, State,
};
use tauri::tray::{TrayIconBuilder, TrayIconEvent, MouseButton, MouseButtonState};
use tauri::menu::{Menu, MenuItem, PredefinedMenuItem};

#[cfg(windows)]
use std::os::windows::process::CommandExt;

/// CREATE_NO_WINDOW: spawn console children (python/powershell) without popping a CMD window.
#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;
#[cfg(not(windows))]
const CREATE_NO_WINDOW: u32 = 0;

#[derive(Default)]
struct AppState {
    panel_visible: std::sync::Mutex<bool>,
}

fn validated_observer_api(raw: &str) -> Option<tauri::Url> {
    let url = tauri::Url::parse(raw).ok()?;
    let loopback = match url.host() {
        // url.host() returns the typed host (Host::Ipv4 / Host::Ipv6) without
        // brackets; host_str() keeps "[::1]" brackets for IPv6, which would
        // fail IpAddr::parse and wrongly reject a valid loopback endpoint.
        Some(url::Host::Ipv4(ip)) => ip.is_loopback(),
        Some(url::Host::Ipv6(ip)) => ip.is_loopback(),
        Some(url::Host::Domain(domain)) => domain.eq_ignore_ascii_case("localhost"),
        None => false,
    };
    if url.scheme() == "http"
        && loopback
        && url.username().is_empty()
        && url.password().is_none()
        // R2 third batch: /api/dashboard retired — only the v3 snapshot endpoint.
        && url.path() == "/api/v1/snapshot"
        && url.query().is_none()
        && url.fragment().is_none()
    {
        Some(url)
    } else {
        None
    }
}

fn observer_endpoint() -> Option<tauri::Url> {
    let raw = std::env::var("WORK_LAB_OBSERVER_API_URL").ok()?;
    let endpoint = validated_observer_api(&raw)?;
    Some(endpoint)
}

fn show_main(app: &AppHandle) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.show();
        let _ = w.unminimize();
        let _ = w.set_focus();
    }
}

fn toggle_panel(app: &AppHandle, state: &State<AppState>) {
    let mut vis = state.panel_visible.lock().unwrap();
    if let Some(w) = app.get_webview_window("panel") {
        if *vis {
            let _ = w.hide();
        } else {
            // Place panel at top-right of the primary monitor, like a HUD.
            if let Some(m) = app.primary_monitor().ok().flatten() {
                let size = w.outer_size().unwrap_or(PhysicalSize::new(420, 900));
                let msize = m.size();
                let x = msize.width as i32 - size.width as i32 - 24;
                let _ = w.set_position(PhysicalPosition::new(x, 40));
            }
            let _ = w.show();
            let _ = w.unminimize();
            let _ = w.set_focus();
        }
        *vis = !*vis;
    }
}

fn hide_to_tray(app: &AppHandle, state: &State<AppState>) {
    let mut vis = state.panel_visible.lock().unwrap();
    *vis = false;
    if let Some(w) = app.get_webview_window("panel") {
        let _ = w.hide();
    }
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.hide();
    }
}

/// Spawns the project collector worker (durable_worker.py) bound to this app.
/// The worker feeds git/usage/execution data into canonical.sqlite, which the
/// Observer UI projects. It lives exactly as long as the desktop app.
fn spawn_collector_worker() -> Option<std::process::Child> {
    let python = r"C:\Users\ALEX\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe";
    let script = r"D:\All projects\WORK-LAB\10-workflow\workflow-assistance\scripts\workflow\durable_worker.py";
    let wf = r"D:\All projects\WORK-LAB\10-workflow\workflow-assistance\scripts\workflow";
    std::process::Command::new(python)
        .args([
            "-u", script,
            "--runtime-root", r"D:\All projects\WORK-LAB\.hermes\task-runtime",
            "--project-root", r"D:\All projects\WORK-LAB",
            "--tick", "30",
        ])
        .env("PYTHONPATH", wf)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .creation_flags(CREATE_NO_WINDOW)
        .spawn()
        .ok()
}

/// Kills any stale durable_worker process so this app owns the single worker.
fn kill_stale_worker() {
    let _ = std::process::Command::new("powershell")
        .args([
            "-NoProfile", "-Command",
            "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'durable_worker' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }",
        ])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .creation_flags(CREATE_NO_WINDOW)
        .spawn();
    std::thread::sleep(std::time::Duration::from_millis(1500));
    let _ = std::fs::remove_file(r"D:\All projects\WORK-LAB\.hermes\task-runtime\worker.lock");
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Collector lifecycle: opening the observer frontend starts the collector,
    // closing it (app exit) stops the collector.
    kill_stale_worker();
    let mut worker = spawn_collector_worker();
    let endpoint = observer_endpoint();
    let app = tauri::Builder::default()
        .manage(AppState::default())
        .plugin(tauri_plugin_log::Builder::default().level(log::LevelFilter::Info).build())
        // 注入 Observer 后端地址：必须在页面加载完成后（Finished）做 ——
        // setup 时 window.url() 还是 about:blank，立即 navigate 会把页面
        // 永久带到空白页（透明框/无内容）。用 Builder 全局页面加载 hook，
        // 并跳过 about: 与已注入 api 参数的页面，避免 navigate 循环。
        .on_page_load(move |webview, payload| {
            if payload.event() != tauri::webview::PageLoadEvent::Finished {
                return;
            }
            let Some(endpoint) = endpoint.as_ref() else {
                return;
            };
            if let Ok(mut url) = webview.url() {
                if url.as_str().starts_with("about:") {
                    return;
                }
                if url.query_pairs().any(|(k, _)| k == "api") {
                    return; // 已注入过
                }
                url.query_pairs_mut().append_pair("api", endpoint.as_str());
                if let Err(error) = webview.navigate(url) {
                    log::warn!("failed to inject Observer endpoint: {error}");
                }
            }
        })
        .setup(|app| {
            let handle = app.handle().clone();
            let _state = app.state::<AppState>();

            // --- System tray (B: tray + floating panel) ---
            let show = MenuItem::with_id(app, "show", "打开观测台", true, None::<&str>)?;
            let panel = MenuItem::with_id(app, "panel", "悬浮面板", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;
            let sep = PredefinedMenuItem::separator(app)?;
            let menu = Menu::with_items(app, &[&show, &panel, &sep, &quit])?;

            let _tray = TrayIconBuilder::with_id("wl-observer")
                .icon(app.default_window_icon().unwrap().clone())
                .tooltip("WORK-LAB Observer")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(move |app, event| match event.id().as_ref() {
                    "show" => show_main(app),
                    "panel" => toggle_panel(app, &app.state::<AppState>()),
                    "quit" => app.exit(0),
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        toggle_panel(app, &app.state::<AppState>());
                    }
                })
                .build(app)?;

            // Close button hides to tray instead of quitting (portable, tray-friendly).
            let _ = handle;

            // If opened as the main window only, focus it.
            Ok(())
        })
        .on_window_event(|window, event| {
            // Hiding to tray on close keeps the tray app alive.
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                let label = window.label().to_string();
                if label == "main" || label == "panel" {
                    let app = window.app_handle().clone();
                    api.prevent_close();
                    hide_to_tray(&app, &app.state::<AppState>());
                }
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building WORK-LAB Observer");

    app.run(move |_app, event| {
        // Collector lifecycle: on app exit, stop the collector worker.
        if let tauri::RunEvent::Exit = event {
            if let Some(mut child) = worker.take() {
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    });
}

#[cfg(test)]
mod tests {
    use super::validated_observer_api;

    #[test]
    fn observer_api_is_loopback_get_only() {
        // Canonical v3 snapshot endpoint (WLGM-150/210).
        assert!(validated_observer_api("http://127.0.0.1:43123/api/v1/snapshot").is_some());
        assert!(validated_observer_api("http://[::1]:43123/api/v1/snapshot").is_some());
        // R2 third batch: legacy /api/dashboard is retired and must be rejected.
        assert!(validated_observer_api("http://127.0.0.1:43123/api/dashboard").is_none());
        assert!(validated_observer_api("https://external.invalid/api/v1/snapshot").is_none());
        assert!(validated_observer_api("http://127.0.0.1:43123/api/v1/snapshot?write=1").is_none());
        assert!(validated_observer_api("http://127.0.0.1:43123/api/v1/events").is_none());
    }
}
