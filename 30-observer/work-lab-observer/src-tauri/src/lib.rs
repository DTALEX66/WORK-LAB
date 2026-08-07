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

#[derive(Default)]
struct AppState {
    panel_visible: std::sync::Mutex<bool>,
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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(AppState::default())
        .plugin(tauri_plugin_log::Builder::default().level(log::LevelFilter::Info).build())
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
        .run(tauri::generate_context!())
        .expect("error while running WORK-LAB Observer");
}
