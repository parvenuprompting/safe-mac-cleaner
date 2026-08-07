use serde::Serialize;

mod scanner;

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
fn scan_files(
    directories: Vec<String>,
    min_size_mb: u64,
    min_age_days: u64,
    age_mode: String,
    top_n: usize,
) -> scanner::ScanResponse {
    let home = dirs::home_dir().unwrap_or_else(|| std::path::PathBuf::from("/"));
    scanner::scan_directories(
        &directories,
        &home,
        min_size_mb,
        min_age_days,
        &age_mode,
        top_n,
    )
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .invoke_handler(tauri::generate_handler![get_app_info, scan_files])
        .run(tauri::generate_context!())
        .expect("error while running Safe Mac Cleaner v3");
}
