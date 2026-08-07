use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use std::time::UNIX_EPOCH;

#[derive(Debug, Deserialize)]
pub struct DeleteItem {
    pub path: String,
    pub size_bytes: u64,
    pub modified_unix: u64,
}

#[derive(Debug, Serialize)]
pub struct DeleteFailure {
    pub path: String,
    pub error: String,
}

#[derive(Debug, Serialize)]
pub struct DeleteResponse {
    pub succeeded: Vec<String>,
    pub failed: Vec<DeleteFailure>,
}

pub fn move_to_trash(items: &[DeleteItem], home: &Path) -> DeleteResponse {
    let mut succeeded = Vec::new();
    let mut failed = Vec::new();

    for item in items {
        match validate_item(item, home) {
            Ok(path) => match trash::delete(&path) {
                Ok(()) => succeeded.push(item.path.clone()),
                Err(error) => failed.push(DeleteFailure {
                    path: item.path.clone(),
                    error: format!("Kon niet naar de Prullenbak verplaatsen: {error}"),
                }),
            },
            Err(error) => failed.push(DeleteFailure {
                path: item.path.clone(),
                error,
            }),
        }
    }

    DeleteResponse { succeeded, failed }
}

pub fn validate_item(item: &DeleteItem, home: &Path) -> Result<PathBuf, String> {
    let home = home
        .canonicalize()
        .map_err(|error| format!("Kan home-directory niet bepalen: {error}"))?;
    let path = PathBuf::from(&item.path)
        .canonicalize()
        .map_err(|error| format!("Bestand bestaat niet meer: {error}"))?;
    if !path.starts_with(&home) || path == home {
        return Err("Bestand valt buiten de veilige home-directory".to_string());
    }
    let metadata =
        fs::metadata(&path).map_err(|error| format!("Kan metadata niet lezen: {error}"))?;
    if !metadata.is_file() {
        return Err("Pad is geen regulier bestand".to_string());
    }
    let modified_unix = metadata
        .modified()
        .ok()
        .and_then(|time| time.duration_since(UNIX_EPOCH).ok())
        .map(|duration| duration.as_secs())
        .unwrap_or(0);
    if metadata.len() != item.size_bytes || modified_unix != item.modified_unix {
        return Err("Bestand is gewijzigd sinds de scan".to_string());
    }
    Ok(path)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    #[test]
    fn rejects_changed_file_before_trash() {
        let suffix = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let root = std::env::temp_dir().join(format!("safe-delete-{suffix}"));
        fs::create_dir_all(&root).unwrap();
        let path = root.join("candidate.txt");
        fs::write(&path, b"before").unwrap();
        let metadata = fs::metadata(&path).unwrap();
        let modified_unix = metadata
            .modified()
            .unwrap()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        fs::write(&path, b"after and different").unwrap();

        let item = DeleteItem {
            path: path.to_string_lossy().to_string(),
            size_bytes: 6,
            modified_unix,
        };
        let error = validate_item(&item, &root).unwrap_err();
        assert!(error.contains("gewijzigd"));
        fs::remove_dir_all(root).unwrap();
    }
}
