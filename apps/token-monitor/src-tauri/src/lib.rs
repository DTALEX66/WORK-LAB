use serde::Serialize;
use serde_json::Value;
use std::collections::{BTreeMap, HashSet};
use std::fs;
use std::os::windows::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use tauri::menu::{Menu, MenuItem};
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri::{Manager, WindowEvent};

#[derive(Debug, Clone, Serialize, Default)]
pub struct ModelStats {
    pub provider: String,
    pub model: String,
    pub input_tokens: u64,
    pub output_tokens: u64,
    pub cached_input_tokens: u64,
    pub reasoning_tokens: u64,
    pub total_tokens: u64,
    pub requests: u64,
}

#[derive(Debug, Clone, Serialize, Default)]
pub struct ProviderStats {
    pub provider: String,
    pub input_tokens: u64,
    pub output_tokens: u64,
    pub total_tokens: u64,
    pub requests: u64,
}

#[derive(Debug, Clone, Serialize, Default)]
pub struct DayStats {
    pub day: String,
    pub total_tokens: u64,
    pub requests: u64,
}

#[derive(Debug, Clone, Serialize, Default)]
pub struct Snapshot {
    pub source: String,
    pub scanned_files: u64,
    pub recognized_requests: u64,
    pub unknown_records: u64,
    pub input_tokens: u64,
    pub output_tokens: u64,
    pub cached_input_tokens: u64,
    pub reasoning_tokens: u64,
    pub total_tokens: u64,
    pub providers: Vec<ProviderStats>,
    pub models: Vec<ModelStats>,
    pub days: Vec<DayStats>,
    pub updated_at: u64,
    pub confidence: String,
    pub notice: Option<String>,
    pub file_sizes: BTreeMap<String, u64>,
}

#[derive(Debug, Default)]
struct Accumulator {
    snapshot: Snapshot,
    models: BTreeMap<String, ModelStats>,
    providers: BTreeMap<String, ProviderStats>,
    days: BTreeMap<String, DayStats>,
    seen: HashSet<String>,
}

fn token_value(object: &serde_json::Map<String, Value>, names: &[&str]) -> Option<u64> {
    names.iter().find_map(|name| match object.get(*name) {
        Some(Value::Number(value)) => value.as_u64(),
        Some(Value::String(value)) => value.parse::<u64>().ok(),
        _ => None,
    })
}

fn string_value(object: &serde_json::Map<String, Value>, names: &[&str]) -> Option<String> {
    names.iter().find_map(|name| match object.get(*name) {
        Some(Value::String(value)) if !value.trim().is_empty() => Some(value.clone()),
        _ => None,
    })
}

fn contains_usage(object: &serde_json::Map<String, Value>) -> bool {
    [
        "prompt_tokens",
        "input_tokens",
        "completion_tokens",
        "output_tokens",
        "total_tokens",
        "cached_tokens",
        "cache_read_input_tokens",
        "reasoning_tokens",
    ]
    .iter()
    .any(|key| object.contains_key(*key))
}

fn contains_usage_descendant(value: &Value) -> bool {
    match value {
        Value::Object(object) => {
            contains_usage(object) || object.values().any(contains_usage_descendant)
        }
        Value::Array(items) => items.iter().any(contains_usage_descendant),
        _ => false,
    }
}

fn provider_for(model: &str, provider_hint: Option<&str>, file_name: &str) -> String {
    if let Some(hint) = provider_hint.filter(|hint| !hint.trim().is_empty()) {
        return provider_for_text(hint);
    }
    let model_name = model.to_lowercase();
    let haystack = if model_name != "unknown-model" {
        model_name
    } else {
        file_name.to_lowercase()
    };
    provider_for_text(&haystack)
}

fn provider_for_text(haystack: &str) -> String {
    if haystack.contains("deepseek") {
        "DeepSeek".to_string()
    } else if haystack.contains("kimi") || haystack.contains("moonshot") {
        "Kimi".to_string()
    } else if haystack.contains("gpt") || haystack.contains("openai") || haystack.contains("codex")
    {
        "GPT / Codex".to_string()
    } else {
        "Other".to_string()
    }
}

fn visit(
    value: &Value,
    file_name: &str,
    location: &str,
    inherited_model: Option<&str>,
    inherited_provider: Option<&str>,
    acc: &mut Accumulator,
) {
    match value {
        Value::Array(items) => {
            for (index, item) in items.iter().enumerate() {
                visit(
                    item,
                    file_name,
                    &format!("{location}[{index}]"),
                    inherited_model,
                    inherited_provider,
                    acc,
                );
            }
        }
        Value::Object(object) => {
            let model = string_value(object, &["model", "model_name", "engine"])
                .or_else(|| inherited_model.map(str::to_owned));
            let provider_hint = string_value(object, &["provider", "provider_name", "vendor"])
                .or_else(|| inherited_provider.map(str::to_owned));
            let nested_usage = object.values().any(contains_usage_descendant);
            if contains_usage(object) && !nested_usage {
                let input = token_value(object, &["prompt_tokens", "input_tokens"]).unwrap_or(0);
                let output =
                    token_value(object, &["completion_tokens", "output_tokens"]).unwrap_or(0);
                let cached = token_value(
                    object,
                    &[
                        "cached_input_tokens",
                        "cache_read_input_tokens",
                        "cache_read_tokens",
                        "cached_tokens",
                    ],
                )
                .unwrap_or(0);
                let reasoning =
                    token_value(object, &["reasoning_tokens", "reasoning_output_tokens"])
                        .unwrap_or(0);
                let explicit_total = token_value(object, &["total_tokens"]);
                let total = explicit_total.unwrap_or(input + output + reasoning);
                let timestamp = string_value(object, &["timestamp", "created_at", "created"])
                    .unwrap_or_else(|| "unknown".to_string());
                let model = model.clone().unwrap_or_else(|| "unknown-model".to_string());
                let provider = provider_for(&model, provider_hint.as_deref(), file_name);
                let fingerprint = format!(
                    "{file_name}|{location}|{model}|{timestamp}|{input}|{output}|{cached}|{reasoning}|{total}"
                );
                if !acc.seen.insert(fingerprint) {
                    return;
                }
                acc.snapshot.recognized_requests += 1;
                acc.snapshot.input_tokens += input;
                acc.snapshot.output_tokens += output;
                acc.snapshot.cached_input_tokens += cached;
                acc.snapshot.reasoning_tokens += reasoning;
                acc.snapshot.total_tokens += total;
                let entry = acc
                    .models
                    .entry(format!("{provider}::{model}"))
                    .or_insert_with(|| ModelStats {
                        provider: provider.clone(),
                        model: model.clone(),
                        ..Default::default()
                    });
                entry.input_tokens += input;
                entry.output_tokens += output;
                entry.cached_input_tokens += cached;
                entry.reasoning_tokens += reasoning;
                entry.total_tokens += total;
                entry.requests += 1;
                let provider_entry =
                    acc.providers
                        .entry(provider.clone())
                        .or_insert_with(|| ProviderStats {
                            provider,
                            ..Default::default()
                        });
                provider_entry.input_tokens += input;
                provider_entry.output_tokens += output;
                provider_entry.total_tokens += total;
                provider_entry.requests += 1;
                let day = timestamp.get(0..10).unwrap_or("unknown").to_string();
                let day_entry = acc.days.entry(day.clone()).or_insert_with(|| DayStats {
                    day,
                    ..Default::default()
                });
                day_entry.total_tokens += total;
                day_entry.requests += 1;
            }
            for (key, child) in object {
                visit(
                    child,
                    file_name,
                    &format!("{location}.{key}"),
                    model.as_deref(),
                    provider_hint.as_deref(),
                    acc,
                );
            }
        }
        _ => {}
    }
}

fn scan_file(path: &Path, acc: &mut Accumulator) {
    if let Ok(metadata) = fs::metadata(path) {
        acc.snapshot
            .file_sizes
            .insert(path.to_string_lossy().to_string(), metadata.len());
    }
    let Ok(content) = fs::read_to_string(path) else {
        acc.snapshot.unknown_records += 1;
        return;
    };
    acc.snapshot.scanned_files += 1;
    let file_name = path.to_string_lossy().to_string();
    let is_jsonl = path.extension().is_some_and(|ext| ext == "jsonl");
    if is_jsonl {
        for (line_number, line) in content
            .lines()
            .filter(|line| !line.trim().is_empty())
            .enumerate()
        {
            match serde_json::from_str::<Value>(line) {
                Ok(value) => {
                    let before = acc.snapshot.recognized_requests;
                    visit(
                        &value,
                        &file_name,
                        &format!("line:{line_number}"),
                        None,
                        None,
                        acc,
                    );
                    if before == acc.snapshot.recognized_requests {
                        acc.snapshot.unknown_records += 1;
                    }
                }
                Err(_) => acc.snapshot.unknown_records += 1,
            }
        }
    } else {
        match serde_json::from_str::<Value>(&content) {
            Ok(value) => {
                let before = acc.snapshot.recognized_requests;
                visit(&value, &file_name, "document", None, None, acc);
                if before == acc.snapshot.recognized_requests {
                    acc.snapshot.unknown_records += 1;
                }
            }
            Err(_) => acc.snapshot.unknown_records += 1,
        }
    }
}

fn collect_files(path: &Path, files: &mut Vec<PathBuf>) -> std::io::Result<()> {
    let metadata = fs::symlink_metadata(path)?;
    if metadata.file_type().is_symlink() || metadata.file_attributes() & 0x400 != 0 {
        return Ok(());
    }
    if path.is_file() {
        if path
            .extension()
            .is_some_and(|ext| ext == "json" || ext == "jsonl")
        {
            files.push(path.to_path_buf());
        }
        return Ok(());
    }
    for entry in fs::read_dir(path)? {
        let entry = entry?;
        let child = entry.path();
        let metadata = fs::symlink_metadata(&child)?;
        if metadata.file_type().is_symlink() || metadata.file_attributes() & 0x400 != 0 {
            continue;
        }
        if child.is_dir() {
            collect_files(&child, files)?;
        } else if child
            .extension()
            .is_some_and(|ext| ext == "json" || ext == "jsonl")
        {
            files.push(child);
        }
    }
    Ok(())
}

pub fn scan_source(source: &str) -> Result<Snapshot, String> {
    let path = Path::new(source);
    if !path.exists() {
        return Err(format!("数据源不存在：{source}"));
    }
    let mut files = Vec::new();
    collect_files(path, &mut files).map_err(|error| format!("无法扫描数据源：{error}"))?;
    files.sort();
    let mut acc = Accumulator {
        snapshot: Snapshot {
            source: source.to_string(),
            confidence: "exact".to_string(),
            ..Default::default()
        },
        ..Default::default()
    };
    for file in files {
        scan_file(&file, &mut acc);
    }
    acc.snapshot.providers = acc.providers.into_values().collect();
    acc.snapshot
        .providers
        .sort_by(|a, b| b.total_tokens.cmp(&a.total_tokens));
    acc.snapshot.models = acc.models.into_values().collect();
    acc.snapshot
        .models
        .sort_by(|a, b| b.total_tokens.cmp(&a.total_tokens));
    acc.snapshot.days = acc.days.into_values().collect();
    if acc.snapshot.recognized_requests == 0 {
        acc.snapshot.confidence = "unknown".to_string();
        acc.snapshot.notice =
            Some("没有发现明确 usage 字段；未进行字符数或上下文估算。".to_string());
    }
    acc.snapshot.updated_at = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or_default();
    Ok(acc.snapshot)
}

pub fn default_source_path() -> String {
    std::env::var("USERPROFILE")
        .or_else(|_| std::env::var("HOME"))
        .map(|home| format!("{home}\\.codex\\sessions"))
        .unwrap_or_else(|_| ".codex/sessions".to_string())
}

pub fn scan_sources(source_list: &str) -> Result<Snapshot, String> {
    let sources: Vec<&str> = source_list
        .split(';')
        .map(str::trim)
        .filter(|source| !source.is_empty())
        .collect();
    if sources.len() <= 1 {
        return scan_source(sources.first().copied().unwrap_or(source_list));
    }
    let mut roots: Vec<PathBuf> = sources
        .iter()
        .map(|source| {
            fs::canonicalize(source).map_err(|error| format!("数据源不可用：{source} ({error})"))
        })
        .collect::<Result<_, _>>()?;
    roots.sort_by_key(|path| path.components().count());
    roots.dedup();
    let mut covered = Vec::new();
    for root in roots {
        if !covered
            .iter()
            .any(|parent: &PathBuf| root.starts_with(parent))
        {
            covered.push(root);
        }
    }
    let mut iter = covered
        .iter()
        .map(|source| scan_source(&source.to_string_lossy()));
    let mut merged = iter.next().ok_or_else(|| "没有数据源".to_string())??;
    for result in iter {
        let next = result?;
        merged.scanned_files += next.scanned_files;
        merged.recognized_requests += next.recognized_requests;
        merged.unknown_records += next.unknown_records;
        merged.input_tokens += next.input_tokens;
        merged.output_tokens += next.output_tokens;
        merged.cached_input_tokens += next.cached_input_tokens;
        merged.reasoning_tokens += next.reasoning_tokens;
        merged.total_tokens += next.total_tokens;
        merged.file_sizes.extend(next.file_sizes);
        for provider in next.providers {
            if let Some(existing) = merged
                .providers
                .iter_mut()
                .find(|item| item.provider == provider.provider)
            {
                existing.input_tokens += provider.input_tokens;
                existing.output_tokens += provider.output_tokens;
                existing.total_tokens += provider.total_tokens;
                existing.requests += provider.requests;
            } else {
                merged.providers.push(provider);
            }
        }
        for model in next.models {
            if let Some(existing) = merged
                .models
                .iter_mut()
                .find(|item| item.model == model.model && item.provider == model.provider)
            {
                existing.input_tokens += model.input_tokens;
                existing.output_tokens += model.output_tokens;
                existing.cached_input_tokens += model.cached_input_tokens;
                existing.reasoning_tokens += model.reasoning_tokens;
                existing.total_tokens += model.total_tokens;
                existing.requests += model.requests;
            } else {
                merged.models.push(model);
            }
        }
        for day in next.days {
            if let Some(existing) = merged.days.iter_mut().find(|item| item.day == day.day) {
                existing.total_tokens += day.total_tokens;
                existing.requests += day.requests;
            } else {
                merged.days.push(day);
            }
        }
    }
    merged.source = source_list.to_string();
    merged
        .providers
        .sort_by(|a, b| b.total_tokens.cmp(&a.total_tokens));
    merged
        .models
        .sort_by(|a, b| b.total_tokens.cmp(&a.total_tokens));
    merged.days.sort_by(|a, b| a.day.cmp(&b.day));
    if merged.recognized_requests > 0 {
        merged.confidence = "exact".to_string();
        merged.notice = None;
    }
    Ok(merged)
}

#[tauri::command]
fn default_source() -> String {
    default_source_path()
}

#[tauri::command]
fn scan_usage(source: String) -> Result<Snapshot, String> {
    scan_sources(&source)
}

pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let show = MenuItem::with_id(app, "show", "显示监控器", true, None::<&str>)?;
            let hide = MenuItem::with_id(app, "hide", "隐藏到托盘", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show, &hide, &quit])?;
            TrayIconBuilder::new()
                .icon(
                    app.default_window_icon()
                        .expect("configured app icon")
                        .clone(),
                )
                .menu(&menu)
                .tooltip("Hermes Token Monitor")
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "hide" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.hide();
                        }
                    }
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
                        if let Some(window) = tray.app_handle().get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = window.hide();
            }
        })
        .invoke_handler(tauri::generate_handler![default_source, scan_usage])
        .run(tauri::generate_context!())
        .expect("error while running Hermes Token Monitor");
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn fixture(content: &str) -> PathBuf {
        let name = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let dir = std::env::temp_dir().join(format!("hermes-token-monitor-{name}"));
        fs::create_dir_all(&dir).unwrap();
        fs::write(dir.join("session.jsonl"), content).unwrap();
        dir
    }

    #[test]
    fn parses_explicit_usage_and_model() {
        let dir = fixture(
            r#"{"timestamp":"2026-08-04T10:00:00Z","model":"gpt-test","usage":{"prompt_tokens":12,"completion_tokens":8,"total_tokens":20}}"#,
        );
        let snapshot = scan_source(dir.to_str().unwrap()).unwrap();
        assert_eq!(snapshot.recognized_requests, 1);
        assert_eq!(snapshot.input_tokens, 12);
        assert_eq!(snapshot.output_tokens, 8);
        assert_eq!(snapshot.total_tokens, 20);
        assert_eq!(snapshot.models[0].model, "gpt-test");
        assert_eq!(snapshot.providers[0].provider, "GPT / Codex");
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn does_not_estimate_unknown_lines() {
        let dir = fixture("{\"message\":\"not usage\"}\nnot json\n");
        let snapshot = scan_source(dir.to_str().unwrap()).unwrap();
        assert_eq!(snapshot.recognized_requests, 0);
        assert_eq!(snapshot.total_tokens, 0);
        assert!(snapshot.unknown_records >= 2);
        assert_eq!(snapshot.confidence, "unknown");
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn supports_input_output_aliases_and_reasoning() {
        let dir =
            fixture(r#"{"model":"alias","input_tokens":4,"output_tokens":5,"reasoning_tokens":3}"#);
        let snapshot = scan_source(dir.to_str().unwrap()).unwrap();
        assert_eq!(snapshot.total_tokens, 12);
        assert_eq!(snapshot.reasoning_tokens, 3);
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn preserves_identical_requests_on_distinct_jsonl_lines() {
        let line = r#"{"timestamp":"2026-08-04T10:00:00Z","model":"gpt-test","usage":{"input_tokens":2,"output_tokens":3,"total_tokens":5}}"#;
        let dir = fixture(&format!("{line}\n{line}\n"));
        let snapshot = scan_source(dir.to_str().unwrap()).unwrap();
        assert_eq!(snapshot.recognized_requests, 2);
        assert_eq!(snapshot.total_tokens, 10);
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn does_not_double_count_parent_summary_with_nested_usage() {
        let dir = fixture(
            r#"{"model":"gpt-test","total_tokens":5,"usage":{"input_tokens":2,"output_tokens":3,"total_tokens":5}}"#,
        );
        let snapshot = scan_source(dir.to_str().unwrap()).unwrap();
        assert_eq!(snapshot.recognized_requests, 1);
        assert_eq!(snapshot.total_tokens, 5);
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn does_not_double_count_deeply_nested_usage() {
        let dir = fixture(
            r#"{"total_tokens":5,"response":{"payload":{"usage":{"input_tokens":2,"output_tokens":3,"total_tokens":5}}}}"#,
        );
        let snapshot = scan_source(dir.to_str().unwrap()).unwrap();
        assert_eq!(snapshot.recognized_requests, 1);
        assert_eq!(snapshot.total_tokens, 5);
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn respects_explicit_provider_and_keeps_same_model_separate() {
        let dir = fixture(
            r#"{"provider":"deepseek","model":"shared-model","input_tokens":1,"output_tokens":2}
{"provider":"openai","model":"shared-model","input_tokens":3,"output_tokens":4}"#,
        );
        let snapshot = scan_source(dir.to_str().unwrap()).unwrap();
        assert_eq!(snapshot.recognized_requests, 2);
        assert_eq!(snapshot.models.len(), 2);
        assert_eq!(snapshot.providers.len(), 2);
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn ignores_overlapping_parent_and_child_sources() {
        let dir = fixture(r#"{"model":"gpt-test","input_tokens":1,"output_tokens":2}"#);
        let child = dir.join("nested");
        fs::create_dir_all(&child).unwrap();
        let source_list = format!("{};{}", dir.display(), child.display());
        let snapshot = scan_sources(&source_list).unwrap();
        assert_eq!(snapshot.recognized_requests, 1);
        assert_eq!(snapshot.total_tokens, 3);
        fs::remove_dir_all(dir).unwrap();
    }
}
