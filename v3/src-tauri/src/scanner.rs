use serde::Serialize;
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::SystemTime;

const EXCLUDED_DIRECTORY_NAMES: &[&str] = &[
    ".",
    "..",
    "Library",
    "System",
    "Applications",
    "private",
    "Volumes",
    "bin",
    "sbin",
    "usr",
];
const EXCLUDED_PACKAGE_EXTENSIONS: &[&str] = &[
    ".app",
    ".bundle",
    ".framework",
    ".kext",
    ".photolibrary",
    ".photoslibrary",
    ".plugin",
    ".sparsebundle",
];
const EXCLUDED_FILE_EXTENSIONS: &[&str] = &[
    ".app",
    ".pkg",
    ".framework",
    ".DS_Store",
    ".localized",
    ".plugin",
    ".kext",
];

#[derive(Debug, Serialize)]
pub struct ScanItem {
    pub path: String,
    pub size_mb: f64,
    pub age_days: u64,
    pub file_type: String,
}

#[derive(Debug, Default, Serialize)]
pub struct ScanStats {
    pub inspected_files: u64,
    pub candidates: u64,
    pub skipped_age: u64,
    pub skipped_size: u64,
    pub skipped_hidden: u64,
    pub skipped_excluded: u64,
    pub skipped_directories: u64,
    pub skipped_packages: u64,
    pub permission_errors: u64,
    pub cancelled: bool,
}

#[derive(Debug, Serialize)]
pub struct ScanResponse {
    pub results: Vec<ScanItem>,
    pub errors: Vec<String>,
    pub stats: ScanStats,
}

#[allow(dead_code)]
pub fn scan_directories(
    directories: &[String],
    home: &Path,
    min_size_mb: u64,
    min_age_days: u64,
    age_mode: &str,
    top_n: usize,
) -> ScanResponse {
    scan_directories_with_hooks(
        directories,
        home,
        min_size_mb,
        min_age_days,
        age_mode,
        top_n,
        || false,
        |_, _| {},
    )
}

pub fn scan_directories_with_hooks<C, P>(
    directories: &[String],
    home: &Path,
    min_size_mb: u64,
    min_age_days: u64,
    age_mode: &str,
    top_n: usize,
    should_cancel: C,
    on_progress: P,
) -> ScanResponse
where
    C: Fn() -> bool + Copy,
    P: Fn(&Path, u64) + Copy,
{
    let home = match home.canonicalize() {
        Ok(path) => path,
        Err(error) => {
            return ScanResponse {
                results: Vec::new(),
                errors: vec![format!("Kan home-directory niet bepalen: {error}")],
                stats: ScanStats::default(),
            }
        }
    };

    let (roots, mut errors) = normalize_roots(directories, &home);
    let mut results = Vec::new();
    let mut stats = ScanStats::default();

    for root in roots {
        scan_directory(
            &root,
            &home,
            min_size_mb,
            min_age_days,
            age_mode,
            &mut results,
            &mut errors,
            &mut stats,
            should_cancel,
            on_progress,
        );
    }

    results.sort_by(|left, right| {
        right
            .size_mb
            .total_cmp(&left.size_mb)
            .then_with(|| right.age_days.cmp(&left.age_days))
    });
    results.truncate(top_n);
    ScanResponse {
        results,
        errors,
        stats,
    }
}

fn normalize_roots(directories: &[String], home: &Path) -> (Vec<PathBuf>, Vec<String>) {
    let mut roots = Vec::new();
    let mut errors = Vec::new();
    let mut seen = HashSet::new();

    for directory in directories {
        let path = match PathBuf::from(directory).canonicalize() {
            Ok(path) => path,
            Err(error) => {
                errors.push(format!("{directory}: {error}"));
                continue;
            }
        };
        if path == home || !path.starts_with(home) || !path.is_dir() {
            errors.push(format!(
                "{directory}: scanroot moet een submap van de home-directory zijn"
            ));
            continue;
        }
        if seen.insert(path.clone()) {
            roots.push(path);
        }
    }

    roots.sort_by_key(|path| path.components().count());
    let mut non_overlapping = Vec::new();
    for root in roots {
        if !non_overlapping
            .iter()
            .any(|parent: &PathBuf| root.starts_with(parent))
        {
            non_overlapping.push(root);
        }
    }
    (non_overlapping, errors)
}

fn scan_directory<C, P>(
    directory: &Path,
    home: &Path,
    min_size_mb: u64,
    min_age_days: u64,
    age_mode: &str,
    results: &mut Vec<ScanItem>,
    errors: &mut Vec<String>,
    stats: &mut ScanStats,
    should_cancel: C,
    on_progress: P,
) where
    C: Fn() -> bool + Copy,
    P: Fn(&Path, u64) + Copy,
{
    let entries = match fs::read_dir(directory) {
        Ok(entries) => entries,
        Err(error) => {
            errors.push(format!("{}: {error}", directory.display()));
            stats.permission_errors += 1;
            return;
        }
    };

    for entry in entries {
        if should_cancel() {
            stats.cancelled = true;
            return;
        }
        let entry = match entry {
            Ok(entry) => entry,
            Err(error) => {
                errors.push(format!("{}: {error}", directory.display()));
                stats.permission_errors += 1;
                continue;
            }
        };
        let path = entry.path();
        let file_type = match entry.file_type() {
            Ok(file_type) => file_type,
            Err(_) => continue,
        };

        if file_type.is_dir() {
            let name = entry.file_name().to_string_lossy().to_string();
            let extension = Path::new(&name)
                .extension()
                .map(|value| format!(".{}", value.to_string_lossy().to_lowercase()));
            if name.starts_with('.') || EXCLUDED_DIRECTORY_NAMES.contains(&name.as_str()) {
                stats.skipped_directories += 1;
            } else if extension
                .as_deref()
                .is_some_and(|value| EXCLUDED_PACKAGE_EXTENSIONS.contains(&value))
            {
                stats.skipped_packages += 1;
            } else {
                scan_directory(
                    &path,
                    home,
                    min_size_mb,
                    min_age_days,
                    age_mode,
                    results,
                    errors,
                    stats,
                    should_cancel,
                    on_progress,
                );
            }
            continue;
        }

        if !file_type.is_file() {
            continue;
        }
        let name = entry.file_name().to_string_lossy().to_string();
        if name.starts_with('.') {
            stats.skipped_hidden += 1;
            continue;
        }
        if EXCLUDED_FILE_EXTENSIONS
            .iter()
            .any(|extension| name.ends_with(extension))
        {
            stats.skipped_excluded += 1;
            continue;
        }
        stats.inspected_files += 1;
        on_progress(&path, stats.inspected_files);

        let metadata = match entry.metadata() {
            Ok(metadata) => metadata,
            Err(_) => continue,
        };
        let size_mb = metadata.len() as f64 / (1024.0 * 1024.0);
        if size_mb < min_size_mb as f64 {
            stats.skipped_size += 1;
            continue;
        }
        let timestamp = if age_mode == "last_used" {
            metadata.accessed().ok()
        } else {
            metadata.modified().ok()
        };
        let age_days = timestamp
            .and_then(|time| SystemTime::now().duration_since(time).ok())
            .map(|duration| duration.as_secs() / 86_400)
            .unwrap_or(0);
        if age_days < min_age_days {
            stats.skipped_age += 1;
            continue;
        }
        if !path.starts_with(home) {
            continue;
        }
        stats.candidates += 1;
        results.push(ScanItem {
            path: path.to_string_lossy().to_string(),
            size_mb,
            age_days,
            file_type: Path::new(&name)
                .extension()
                .map(|value| format!(".{}", value.to_string_lossy()))
                .unwrap_or_else(|| "file".to_string()),
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn test_home() -> PathBuf {
        let suffix = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let home = std::env::temp_dir().join(format!("safe-mac-cleaner-{suffix}"));
        fs::create_dir_all(&home).unwrap();
        home
    }

    #[test]
    fn finds_visible_files_and_reports_stats() {
        let home = test_home();
        let folder = home.join("Documents");
        fs::create_dir_all(&folder).unwrap();
        fs::write(folder.join("notes.txt"), b"hello").unwrap();

        let response = scan_directories(
            &[folder.to_string_lossy().to_string()],
            &home,
            0,
            0,
            "last_modified",
            10,
        );

        assert_eq!(response.results.len(), 1);
        assert_eq!(response.stats.inspected_files, 1);
        assert_eq!(response.stats.candidates, 1);
        fs::remove_dir_all(home).unwrap();
    }

    #[test]
    fn skips_photos_library_without_permission_error() {
        let home = test_home();
        let folder = home.join("Pictures");
        let photos = folder.join("Photos Library.photoslibrary");
        fs::create_dir_all(&photos).unwrap();
        fs::write(photos.join("private.dat"), b"private").unwrap();

        let response = scan_directories(
            &[folder.to_string_lossy().to_string()],
            &home,
            0,
            0,
            "last_modified",
            10,
        );

        assert!(response.results.is_empty());
        assert!(response.errors.is_empty());
        assert_eq!(response.stats.skipped_packages, 1);
        fs::remove_dir_all(home).unwrap();
    }

    #[test]
    fn rejects_home_directory_as_scanroot() {
        let home = test_home();
        let response = scan_directories(
            &[home.to_string_lossy().to_string()],
            &home,
            0,
            0,
            "last_modified",
            10,
        );

        assert!(response.results.is_empty());
        assert_eq!(response.errors.len(), 1);
        fs::remove_dir_all(home).unwrap();
    }
}
