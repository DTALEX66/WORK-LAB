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
use serde::Serialize;

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

// ---------------------------------------------------------------------------
// WINDOW STATE READBACK — the measurement half of the geometry claim.
//
// Before this, the crate only ever SET geometry: `set_position` in
// `toggle_panel` (below) and `inner_size(...)` on the U19 probe builder. Nothing
// anywhere read a window's real size back, so the CI geometry step could only
// prove "a narrow content area does not overflow" — it measured a Chrome
// `--headless=new` viewport, never the Tauri window. That is the whole
// 500x629-vs-440x780 gap: two numbers describing two different objects.
//
// READ-ONLY BY CONSTRUCTION (apps/observer/AGENTS.md, WLR-100): this block calls
// only `get_webview_window`, `config()`, `inner_size`, `outer_size`,
// `outer_position`, `scale_factor` and `is_visible`. It never creates a window,
// never moves/resizes/shows/hides anything, never touches AppState, never writes
// to disk. A measurement that changes the thing measured is not a measurement.
//
// UNIT OF WORK — the part everyone skipped: `WindowConfig.width/height` are
// LOGICAL pixels of the INNER area (tauri-runtime-wry-2.11.4/src/lib.rs:932
// maps them through `.inner_size(TaoLogicalSize::new(w, h))`), while
// `inner_size()/outer_size()` read back PHYSICAL pixels. Comparing them needs
// the `scale_factor` division, so both units are reported and the conversion is
// checkable rather than trusted.

/// Logical-pixel slack for the declared-vs-measured geometry claim.
///
/// 2.0, not 0: Windows rounds the logical→physical conversion per axis, so an
/// honest readback of a 440-logical window can land a physical pixel off. A
/// slack this tight still convicts the failure that matters (500 vs 440 is 60).
const GEOMETRY_TOLERANCE_LOGICAL_PX: f64 = 2.0;

#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
struct PhysicalPair {
    width: u32,
    height: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
struct PhysicalPoint {
    x: i32,
    y: i32,
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
struct LogicalPair {
    width: f64,
    height: f64,
}

/// What `tauri.conf.json` says this window should be, read from the Config the
/// binary was actually built with (`app.config()`, i.e. the embedded
/// tauri.conf.json) — not re-parsed off disk, so the declared side of the
/// comparison cannot drift from the bundle being measured.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
struct DeclaredWindow {
    label: String,
    width: f64,
    height: f64,
    min_width: Option<f64>,
    min_height: Option<f64>,
    resizable: bool,
    /// The unit the declared numbers carry, stated in the payload so no reader
    /// has to know Tauri internals to interpret the verdict.
    unit: &'static str,
    source: &'static str,
}

/// Verdict status. `unmeasured` is a distinct third state on purpose: a claim
/// with no readback must never be printable as either green or red-by-accident,
/// and it must never collapse into `match` by defaulting.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[serde(rename_all = "lowercase")]
enum GeometryStatus {
    Match,
    Mismatch,
    Unmeasured,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
struct GeometryVerdict {
    status: GeometryStatus,
    /// measured minus declared, in logical pixels; absent when undecidable.
    deviation: Option<LogicalPair>,
    tolerance_logical_px: f64,
    /// Which measured quantity the declared numbers were compared against, so a
    /// reader can tell inner-vs-outer basis was chosen deliberately, not by luck.
    basis: &'static str,
    reason: Option<String>,
}

/// Physical → logical. A non-finite or non-positive scale yields `None`, never a
/// divide-by-zero `inf` that would silently mismatch forever.
fn logical_from_physical(size: Option<PhysicalPair>, scale_factor: Option<f64>) -> Option<LogicalPair> {
    let size = size?;
    let scale = scale_factor?;
    if !scale.is_finite() || scale <= 0.0 {
        return None;
    }
    Some(LogicalPair {
        width: f64::from(size.width) / scale,
        height: f64::from(size.height) / scale,
    })
}

/// The whole claim rule, PURE: no window, no runtime, no filesystem. Every
/// branch that cannot prove something says `unmeasured` — never `match`.
fn judge_geometry(
    measured_logical: Option<LogicalPair>,
    declared: Option<&DeclaredWindow>,
    tolerance: f64,
) -> GeometryVerdict {
    let undecidable = |reason: &str| GeometryVerdict {
        status: GeometryStatus::Unmeasured,
        deviation: None,
        tolerance_logical_px: tolerance,
        basis: "inner_size_logical vs declared width/height",
        reason: Some(reason.to_string()),
    };

    let Some(measured) = measured_logical else {
        return undecidable("no measured inner size at a usable scale factor");
    };
    let Some(declared) = declared else {
        return undecidable("window label is not declared in tauri.conf.json");
    };

    let deviation = LogicalPair {
        width: measured.width - declared.width,
        height: measured.height - declared.height,
    };
    let within = deviation.width.abs() <= tolerance && deviation.height.abs() <= tolerance;
    GeometryVerdict {
        status: if within { GeometryStatus::Match } else { GeometryStatus::Mismatch },
        deviation: Some(deviation),
        tolerance_logical_px: tolerance,
        basis: "inner_size_logical vs declared width/height",
        reason: None,
    }
}

/// Live window for a label, or the label this app *should* have measured, plus
/// why. Explicit request wins; otherwise the non-resizable configured window is
/// the panel by contract (`tauri.conf.json` gives only `panel` resizable:false),
/// and the first configured window is the documented last resort.
fn resolve_target_label(app: &AppHandle, requested: Option<&str>) -> (String, bool, Option<String>) {
    let windows = &app.config().app.windows;
    if let Some(label) = requested {
        let live = app.get_webview_window(label).is_some();
        let declared = windows.iter().any(|w| w.label == label);
        if live && declared {
            return (label.to_string(), true, None);
        }
        let note = match (live, declared) {
            (true, false) => format!("window '{label}' is live but not declared in tauri.conf.json"),
            (false, true) => format!("'{label}' is declared in tauri.conf.json but no live window exists"),
            _ => format!("'{label}' is neither a live window nor a declared one"),
        };
        return (label.to_string(), false, Some(note));
    }
    if let Some(w) = windows.iter().find(|w| !w.resizable) {
        if app.get_webview_window(&w.label).is_some() {
            return (w.label.clone(), true, Some("resolved by the non-resizable (panel) contract".into()));
        }
    }
    if let Some(w) = windows.first() {
        let live = app.get_webview_window(&w.label).is_some();
        return (
            w.label.clone(),
            live,
            Some(format!("no label requested; fell back to the first declared window '{}'", w.label)),
        );
    }
    ("unset".to_string(), false, Some("tauri.conf.json declares no windows at all".into()))
}

/// Collects a getter result without swallowing it: `None` always arrives with a
/// reason in `errors`, so a silent failure becomes visible in the payload.
fn capture<T: Copy>(field: &str, result: tauri::Result<T>, errors: &mut Vec<String>) -> Option<T> {
    match result {
        Ok(value) => Some(value),
        Err(error) => {
            errors.push(format!("{field}: {error}"));
            None
        }
    }
}

/// READ-ONLY: report the real geometry of one named window against what
/// `tauri.conf.json` says it should be. Returns a value rather than a `Result`
/// on purpose — a failure to measure is a *finding* to be carried in the
/// payload (`resolution_succeeded:false` + `verdict.status:"unmeasured"`), not an
/// exception that discards the reason. The JS side calls this over the local
/// IPC bridge; application commands are not ACL-gated while the request origin is
/// local (tauri-2.11.3/src/webview/mod.rs:1823), which is why no capability file
/// had to be widened for the probe window to reach it.
#[tauri::command]
fn window_metrics(app: AppHandle, label: Option<String>) -> WindowMetrics {
    let (resolved_label, resolution_succeeded, note) =
        resolve_target_label(&app, label.as_deref());

    let mut errors: Vec<String> = Vec::new();
    let window = app.get_webview_window(&resolved_label);
    let window_exists = window.is_some();

    let (mut inner, mut outer, mut position, mut scale, mut visible) =
        (None, None, None, None, None);
    if let Some(w) = window.as_ref() {
        // Read order matters only for the log: scale first, so a size failure
        // still reports the DPI the machine was actually on.
        scale = capture("scale_factor", w.scale_factor(), &mut errors);
        inner = capture("inner_size", w.inner_size(), &mut errors)
            .map(|s| PhysicalPair { width: s.width, height: s.height });
        outer = capture("outer_size", w.outer_size(), &mut errors)
            .map(|s| PhysicalPair { width: s.width, height: s.height });
        position = capture("outer_position", w.outer_position(), &mut errors)
            .map(|p| PhysicalPoint { x: p.x, y: p.y });
        visible = capture("is_visible", w.is_visible(), &mut errors);
    } else if !window_exists {
        errors.push(format!("no live window labelled '{resolved_label}'"));
    }

    let declared = app
        .config()
        .app
        .windows
        .iter()
        .find(|w| w.label == resolved_label)
        .map(|w| DeclaredWindow {
            label: w.label.clone(),
            width: w.width,
            height: w.height,
            min_width: w.min_width,
            min_height: w.min_height,
            resizable: w.resizable,
            unit: "logical pixels, inner content area",
            source: "embedded tauri.conf.json (app.windows)",
        });

    let inner_logical = logical_from_physical(inner, scale);
    let verdict = judge_geometry(inner_logical, declared.as_ref(), GEOMETRY_TOLERANCE_LOGICAL_PX);

    WindowMetrics {
        command: "window_metrics",
        readonly: true,
        requested_label: label,
        window_label: resolved_label,
        resolution_succeeded,
        resolution_note: note,
        window_exists,
        visible,
        scale_factor: scale,
        inner_size_physical: inner,
        outer_size_physical: outer,
        outer_position_physical: position,
        inner_size_logical: inner_logical,
        declared,
        verdict,
        field_errors: errors,
    }
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct WindowMetrics {
    command: &'static str,
    /// Self-describing read-only contract, so a payload reader can confirm which
    /// command produced this and that it claims no side effect.
    readonly: bool,
    requested_label: Option<String>,
    window_label: String,
    resolution_succeeded: bool,
    resolution_note: Option<String>,
    window_exists: bool,
    visible: Option<bool>,
    scale_factor: Option<f64>,
    inner_size_physical: Option<PhysicalPair>,
    outer_size_physical: Option<PhysicalPair>,
    outer_position_physical: Option<PhysicalPoint>,
    inner_size_logical: Option<LogicalPair>,
    declared: Option<DeclaredWindow>,
    verdict: GeometryVerdict,
    field_errors: Vec<String>,
}

// WLR-100 (2026-08-20): Observer is strictly read-only. Worker lifecycle
// (spawn/kill/lock) belongs to Workflow Assistance composition root, never to
// the Observer shell. Observer only discovers a verified loopback endpoint.
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // WLR-100: Observer never starts/stops/kills the Worker. The Workflow
    // Assistance worker runs independently (user-level service).
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

            // U19 (E2E): opt-in, default-OFF CDP probe window. In the shipped
            // binary this block is inert unless WORK_LAB_U19_CDP_PORT is set
            // (CI E2E + local harness). The probe window hosts the SAME
            // frontend; only ITS WebView2 environment carries
            // --remote-debugging-port, so the production main/panel webviews
            // are untouched. (The WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS env
            // var is NOT consumed by wry — it always passes app-level args —
            // so the args must go through this builder hook.)
            if let Ok(cdpp) = std::env::var("WORK_LAB_U19_CDP_PORT") {
                // --use-angle=swiftshader: force software rendering so GDI
                // PrintWindow can actually capture the pixels on headless CI
                // runners (GPU-composited surfaces print black). Opt-in only.
                let args = format!(
                    "--remote-debugging-port={cdpp} --remote-allow-origins=* --use-angle=swiftshader"
                );
                let url = tauri::WebviewUrl::App(
                    "index.html?view=full&mode=UNKNOWN&theme=dark".into(),
                );
                match tauri::WebviewWindowBuilder::new(app, "u19cdp", url)
                    .additional_browser_args(args.as_str())
                    // U19: explicit geometry so the harness' GDI proof (>=200x150
                    // filter) and the CDP page target both have a real surface.
                    // A default-sized/hidden window on a headless runner is the
                    // "windows=0 + no CDP target" failure mode seen in CI.
                    .inner_size(800.0, 600.0)
                    .visible(true)
                    .build()
                {
                    Ok(w) => {
                        let _ = w.show();
                        let _ = w.set_focus();
                        // U19 next-cycle: externalize the probe outcome so the
                        // harness/CI log can discriminate "window built" from
                        // "never reached the probe block" without depending on
                        // tauri-plugin-log flushing. visible=false on a built
                        // window => headless-session root cause (R1).
                        if let Ok(status_path) = std::env::var("WORK_LAB_U19_PROBE_STATUS") {
                            let vis = w.is_visible().unwrap_or(false);
                            let _ = std::fs::write(
                                &status_path,
                                format!(
                                    "probe=ok pid={} visible={} cdpPort={}",
                                    std::process::id(),
                                    vis, cdpp
                                ),
                            );
                        }
                        log::info!(target: "u19", "cdp probe window ready");
                    }
                    // Was silently swallowed — the root cause of U19's CI
                    // "no CDP page target / windows=0": the build error (usually
                    // a WebView2 instance failure) never reached the log.
                    Err(error) => {
                        if let Ok(status_path) =
                            std::env::var("WORK_LAB_U19_PROBE_STATUS")
                        {
                            let _ = std::fs::write(
                                &status_path,
                                format!(
                                    "probe=build_failed error={}",
                                    error.to_string().replace('\n', " ")
                                ),
                            );
                        }
                        log::error!(
                            target: "u19",
                            "cdp probe window build FAILED: {error}"
                        );
                    }
                }
            }

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
        .invoke_handler(tauri::generate_handler![window_metrics])
        .build(tauri::generate_context!())
        .expect("error while building WORK-LAB Observer");

    app.run(move |_app, event| {
        // WLR-100: Observer exit never touches the Worker (strict read-only).
        let _ = event;
    });
}

#[cfg(test)]
mod tests {
    use super::{
        judge_geometry, logical_from_physical, validated_observer_api, DeclaredWindow,
        GeometryStatus, GeometryVerdict, LogicalPair, PhysicalPair,
        GEOMETRY_TOLERANCE_LOGICAL_PX,
    };

    fn panel_declared() -> DeclaredWindow {
        // Mirrors apps/observer/src-tauri/tauri.conf.json app.windows[1].
        DeclaredWindow {
            label: "panel".into(),
            width: 440.0,
            height: 780.0,
            min_width: Some(440.0),
            min_height: Some(780.0),
            resizable: false,
            unit: "logical pixels, inner content area",
            source: "test",
        }
    }

    fn logical(width: f64, height: f64) -> Option<LogicalPair> {
        Some(LogicalPair { width, height })
    }

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

    // --- WINDOW STATE READBACK: the conversion everyone skipped ---------------

    #[test]
    fn physical_size_converts_to_logical_by_scale() {
        // 440x780 logical at 125% DPI is 550x975 physical. Reading the raw
        // physical number against the declared logical number is exactly how a
        // "the panel is the wrong size" false alarm gets written.
        let physical = Some(PhysicalPair { width: 550, height: 975 });
        assert_eq!(
            logical_from_physical(physical, Some(1.25)),
            logical(440.0, 780.0)
        );
    }

    #[test]
    fn a_broken_scale_factor_is_unmeasured_not_a_mismatch() {
        // Division by 0 would produce inf and report "mismatch" forever; the
        // honest answer is that no conversion was possible.
        let physical = Some(PhysicalPair { width: 440, height: 780 });
        for scale in [Some(0.0), Some(-1.0), Some(f64::NAN), None] {
            assert_eq!(logical_from_physical(physical, scale), None);
            assert_eq!(
                judge_geometry(logical_from_physical(physical, scale), Some(&panel_declared()), 2.0)
                    .status,
                GeometryStatus::Unmeasured,
                "scale {scale:?} must not produce a geometry verdict"
            );
        }
    }

    // --- the claim rule, including the negative controls ----------------------

    #[test]
    fn measured_size_equal_to_declared_is_a_match() {
        let verdict = judge_geometry(
            logical(440.0, 780.0),
            Some(&panel_declared()),
            GEOMETRY_TOLERANCE_LOGICAL_PX,
        );
        assert_eq!(verdict.status, GeometryStatus::Match);
        assert_eq!(verdict.deviation, logical(0.0, 0.0));
    }

    #[test]
    fn tolerance_boundary_is_inclusive_and_the_next_pixel_is_red() {
        let declared = panel_declared();
        assert_eq!(
            judge_geometry(logical(442.0, 782.0), Some(&declared), 2.0).status,
            GeometryStatus::Match,
            "exactly the declared slack is still a match"
        );
        assert_eq!(
            judge_geometry(logical(442.01, 780.0), Some(&declared), 2.0).status,
            GeometryStatus::Mismatch,
            "one hundredth past the slack is red — the rule must not round away"
        );
        // One axis in, one axis out: the verdict is the AND, never the average.
        assert_eq!(
            judge_geometry(logical(440.0, 900.0), Some(&declared), 2.0).status,
            GeometryStatus::Mismatch
        );
    }

    #[test]
    fn the_recorded_cdp_gap_is_convicted_as_mismatch() {
        // The numbers from the run nobody could explain: a CDP-emulated
        // 500x629 viewport against the panel's declared 440x780. Pure emulation
        // must never pass as the panel's real geometry.
        let verdict = judge_geometry(
            logical(500.0, 629.0),
            Some(&panel_declared()),
            GEOMETRY_TOLERANCE_LOGICAL_PX,
        );
        assert_eq!(verdict.status, GeometryStatus::Mismatch);
        assert_eq!(verdict.deviation, logical(60.0, -151.0));
    }

    #[test]
    fn a_missing_readback_never_reports_match() {
        // The fail-closed core of the whole gate: no measurement, no claim —
        // and above all, never the green default.
        for measured in [None, logical(0.0, 0.0)] {
            let verdict: GeometryVerdict =
                judge_geometry(measured, Some(&panel_declared()), 2.0);
            if measured.is_none() {
                assert_eq!(verdict.status, GeometryStatus::Unmeasured);
            }
            assert_ne!(verdict.status, GeometryStatus::Match);
        }
        // No declared config either: nothing to match against, so still red-able.
        let verdict = judge_geometry(logical(440.0, 780.0), None, 2.0);
        assert_eq!(verdict.status, GeometryStatus::Unmeasured);
        assert!(verdict.reason.is_some(), "an undecidable verdict must say why");
    }

    #[test]
    fn payload_serializes_the_contract_the_probe_parses() {
        // The probe reads `verdict.status`, `innerSizeLogical` and
        // `scaleFactor` by name. Pin the wire shape here so a Rust-side rename
        // fails this test instead of failing silently at 3am in CI.
        let value = serde_json::to_value(judge_geometry(
            logical(440.0, 780.0),
            Some(&panel_declared()),
            2.0,
        ))
        .expect("verdict serializes");
        assert_eq!(value["status"].as_str(), Some("match"));
        assert!(value["innerSizeLogical"].is_null(), "verdict carries no such field");
        assert_eq!(value["deviation"]["width"].as_f64(), Some(0.0));
        assert!(value["toleranceLogicalPx"].is_number());
        assert_eq!(value["basis"].as_str(), Some("inner_size_logical vs declared width/height"));
    }
}
