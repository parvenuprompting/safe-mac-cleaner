use serde::Serialize;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, OnceLock};
use tauri::{AppHandle, Emitter};

mod deletion;
mod scanner;

static SCAN_CANCELLED: OnceLock<Arc<AtomicBool>> = OnceLock::new();

fn scan_cancel_flag() -> Arc<AtomicBool> {
    SCAN_CANCELLED
        .get_or_init(|| Arc::new(AtomicBool::new(false)))
        .clone()
}

#[derive(Serialize)]
struct AppInfo {
    name: &'static str,
    version: &'static str,
}

#[tauri::command]
fn get_app_info() -> AppInfo {
    AppInfo {
        name: "Safe Mac Cleaner",
        version: env!("CARGO_PKG_VERSION"),
    }
}

#[tauri::command]
async fn scan_files(
    app: AppHandle,
    directories: Vec<String>,
    min_size_mb: u64,
    min_age_days: u64,
    age_mode: String,
    top_n: usize,
) -> scanner::ScanResponse {
    let home = dirs::home_dir().unwrap_or_else(|| std::path::PathBuf::from("/"));
    let directories = if directories.is_empty() {
        [
            "Downloads",
            "Desktop",
            "Documents",
            "Movies",
            "Pictures",
            "Music",
        ]
        .iter()
        .map(|directory| home.join(directory).to_string_lossy().to_string())
        .collect()
    } else {
        directories
    };
    let cancelled = scan_cancel_flag();
    cancelled.store(false, Ordering::Relaxed);
    let scan_cancelled = cancelled.clone();
    tokio::task::spawn_blocking(move || {
        scanner::scan_directories_with_hooks(
            &directories,
            &home,
            min_size_mb,
            min_age_days,
            &age_mode,
            top_n,
            || scan_cancelled.load(Ordering::Relaxed),
            |path, inspected_files| {
                let _ = app.emit(
                    "scan-progress",
                    ScanProgress {
                        path: path.to_string_lossy().to_string(),
                        inspected_files,
                    },
                );
            },
        )
    })
    .await
    .unwrap_or_else(|error| scanner::ScanResponse {
        results: Vec::new(),
        errors: vec![format!("Scanworker mislukt: {error}")],
        stats: scanner::ScanStats::default(),
    })
}

#[derive(Clone, Serialize)]
struct ScanProgress {
    path: String,
    inspected_files: u64,
}

#[tauri::command]
fn cancel_scan() {
    scan_cancel_flag().store(true, Ordering::Relaxed);
}

#[tauri::command]
fn move_to_trash(items: Vec<deletion::DeleteItem>) -> deletion::DeleteResponse {
    let home = dirs::home_dir().unwrap_or_else(|| std::path::PathBuf::from("/"));
    deletion::move_to_trash(&items, &home)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .invoke_handler(tauri::generate_handler![
            get_app_info,
            scan_files,
            cancel_scan,
            move_to_trash
        ])
        .run(tauri::generate_context!())
        .expect("error while running Safe Mac Cleaner v3");
}
