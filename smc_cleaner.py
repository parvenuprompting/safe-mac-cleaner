import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil
from send2trash import send2trash

logger = logging.getLogger(__name__)

# =======================================================
# ⚙️ CONFIGURATIE & CONSTANTEN
# =======================================================

# Logica config
DEFAULT_MIN_SIZE_MB = 100
DEFAULT_MIN_AGE_DAYS = 30
DEFAULT_TOP_N = 100
DEFAULT_AGE_MODE = "last_used"

# Veiligheidsregels
# Extensies die we NOOIT aanraken (Apps, Systeem, etc.)
EXCLUDE_EXTENSIONS = {".app", ".pkg", ".framework", ".DS_Store", ".localized", ".plugin", ".kext"}

# Mappen die we overslaan tijdens recursie
EXCLUDE_DIR_NAMES = {'.', '..', 'Library', 'System', 'Applications', 'private', 'Volumes', 'bin', 'sbin', 'usr'}
EXCLUDE_PACKAGE_DIR_EXTENSIONS = {
    ".app", ".bundle", ".framework", ".kext", ".photolibrary", ".photoslibrary",
    ".plugin", ".sparsebundle",
}

# Persistente uitsluitingen bestand
EXCLUSION_FILE = Path.home() / ".smc_exclusions.json"

# Standaard scan mappen
DEFAULT_SCAN_DIRS = [
    str(Path.home() / "Downloads"),
    str(Path.home() / "Desktop"),
    str(Path.home() / "Documents"),
    str(Path.home() / "Movies"),
    str(Path.home() / "Pictures"),
    str(Path.home() / "Music"),
]

HOME_PATH = Path.home().resolve()

AGE_MODES = {
    "last_used": "Laatst gebruikt (Access Time)",
    "last_modified": "Laatst gewijzigd (Modify Time)"
}

# Logging instellen
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==================================
# 💡 HULP FUNCTIES
# ==================================

def get_disk_stats() -> Dict[str, float]:
    """Haalt de schijfgebruikstatistieken op."""
    try:
        disk_info = psutil.disk_usage(str(Path.home()))
        return {
            'total_gb': disk_info.total / (1024**3),
            'free_gb': disk_info.free / (1024**3),
            'percent_free': 100.0 - disk_info.percent,
        }
    except Exception:
        logger.exception("Fout bij ophalen schijfinfo")
        return {'total_gb': 0.0, 'free_gb': 0.0, 'percent_free': 0.0}


def validate_scan_directories(directories: List[str]) -> Tuple[List[str], List[str]]:
    """Return existing directories below the user's home directory only."""
    valid = []
    errors = []
    seen = set()

    for directory in directories:
        try:
            path = Path(directory).expanduser().resolve(strict=True)
            path.relative_to(HOME_PATH)
            if path == HOME_PATH or not path.is_dir():
                raise ValueError("scanroot moet een submap van de home-directory zijn")
            path_string = str(path)
            if path_string not in seen:
                valid.append(path_string)
                seen.add(path_string)
        except (OSError, RuntimeError, ValueError) as error:
            errors.append(f"{directory}: {error}")

    # A parent scanroot already includes all of its child scanroots.
    valid.sort(key=len)
    non_overlapping = []
    for path_string in valid:
        path = Path(path_string)
        if not any(path.is_relative_to(parent) for parent in non_overlapping):
            non_overlapping.append(path)
    return [str(path) for path in non_overlapping], errors

# ==================================
# 🛡️ EXCLUSIE LIJST BEHEER
# ==================================

def load_exclusion_list() -> List[str]:
    if not EXCLUSION_FILE.exists():
        return []
    try:
        with EXCLUSION_FILE.open('r') as f:
            exclusions = json.load(f)
        if not isinstance(exclusions, list) or not all(isinstance(path, str) for path in exclusions):
            raise ValueError("uitsluitingen moeten een lijst met paden zijn")
        return exclusions
    except Exception:
        logger.exception("Kon exclusielijst niet laden")
        return []

def toggle_exclusion(path: str, add: bool = True) -> bool:
    path = str(Path(path).expanduser().resolve())
    current = load_exclusion_list()
    current = [str(Path(item).expanduser().resolve()) for item in current]
    try:
        if add:
            if path not in current:
                current.append(path)
        else:
            if path in current:
                current.remove(path)
        
        temporary_file = EXCLUSION_FILE.with_suffix('.tmp')
        with temporary_file.open('w') as f:
            json.dump(current, f, indent=4)
        temporary_file.replace(EXCLUSION_FILE)
        return True
    except Exception:
        logger.exception("Fout bij bijwerken exclusielijst")
        return False

# ==================================
# 🚀 SCAN ENGINE (GEOPTIMALISEERD MET SCANDIR)
# ==================================

def _scan_recursive(
    directory: str, 
    candidates: List[Dict[str, Any]], 
    errors: List[str],
    exclusions: set,
    min_size_mb: int, 
    min_age_days: int, 
    age_mode: str,
    should_stop: Callable[[], bool],
    stats: Dict[str, int],
):
    """Interne recursieve functie gebruikmakend van os.scandir voor performance."""
    if should_stop(): 
        return

    try:
        # os.scandir is veel sneller dan os.walk omdat het stat info vaak al heeft
        with os.scandir(directory) as it:
            for entry in it:
                if should_stop(): return

                # 1. Behandel Mappen
                if entry.is_dir(follow_symlinks=False):
                    # Check of mapnaam verboden is of begint met .
                    if entry.name.startswith('.') or entry.name in EXCLUDE_DIR_NAMES:
                        stats["skipped_directories"] += 1
                        continue
                    if Path(entry.name).suffix.lower() in EXCLUDE_PACKAGE_DIR_EXTENSIONS:
                        stats["skipped_packages"] += 1
                        continue
                    # Check volledige pad tegen gebruikers-exclusions
                    if entry.path in exclusions:
                        continue
                    
                    # Recurse (duik dieper)
                    _scan_recursive(
                        entry.path, candidates, errors, exclusions, min_size_mb,
                        min_age_days, age_mode, should_stop, stats,
                    )

                # 2. Behandel Bestanden
                elif entry.is_file(follow_symlinks=False):
                    name = entry.name
                    if name.startswith('.'):
                        stats["skipped_hidden"] += 1
                        continue
                    if any(name.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                        stats["skipped_excluded"] += 1
                        continue
                    if entry.path in exclusions:
                        stats["skipped_excluded"] += 1
                        continue

                    try:
                        stats["inspected_files"] += 1
                        # Haal cached stat info op (snel!)
                        stat = entry.stat()
                        size_mb = stat.st_size / (1024 * 1024)
                        
                        if size_mb < min_size_mb:
                            stats["skipped_size"] += 1
                            continue

                        # Leeftijd berekenen
                        timestamp = stat.st_atime if age_mode == "last_used" else stat.st_mtime
                        age_days = (time.time() - timestamp) / (60 * 60 * 24)

                        if age_days < min_age_days:
                            stats["skipped_age"] += 1
                            continue

                        candidates.append({
                            "path": entry.path,
                            "size_mb": size_mb,
                            "age_days": age_days,
                            "file_type": Path(name).suffix or 'file',
                            "_st_dev": stat.st_dev,
                            "_st_ino": stat.st_ino,
                            "_st_size": stat.st_size,
                            "_st_mtime_ns": stat.st_mtime_ns,
                        })
                        stats["candidates"] += 1

                    except (OSError, PermissionError):
                        # Skip bestand bij fout
                        continue

    except PermissionError:
        errors.append(directory)
        stats["permission_errors"] += 1
    except Exception:
        logger.exception("Scan fout in %s", directory)

def scan_disk(
    directories: List[str],
    min_size_mb: int,
    min_age_days: int,
    age_mode: str,
    top_n: int,
    progress_callback: Optional[Callable[[str], None]] = None,
    should_stop: Optional[Callable[[], bool]] = None
) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, int]]:
    """
    Start de scan. Geeft nu een tuple terug: (resultaten, foutmeldingen).
    """
    candidates = []
    errors = []
    stats = {
        "inspected_files": 0,
        "candidates": 0,
        "skipped_age": 0,
        "skipped_size": 0,
        "skipped_hidden": 0,
        "skipped_excluded": 0,
        "skipped_directories": 0,
        "skipped_packages": 0,
        "permission_errors": 0,
    }
    exclusions = {str(Path(path).expanduser().resolve()) for path in load_exclusion_list()}
    
    # Valideer input
    valid_dirs, directory_errors = validate_scan_directories(directories)
    errors.extend(directory_errors)
    
    for folder in valid_dirs:
        if should_stop and should_stop(): break
        
        if progress_callback:
            progress_callback(f"Scannen: {folder}")
            
        _scan_recursive(
            folder, candidates, errors, exclusions,
            min_size_mb, min_age_days, age_mode, 
            should_stop or (lambda: False),
            stats,
        )

    # Sorteren
    if progress_callback:
        progress_callback("Sorteren en opschonen...")
        
    # Sorteer: Grootste & Oudste eerst
    candidates.sort(key=lambda x: (x["size_mb"], x["age_days"]), reverse=True)
    
    return candidates[:top_n], errors, stats

def delete_files(files: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
    """Move verified files to the Trash and return separate success/failure results."""
    succeeded = []
    failed = []
    for item in files:
        path = item['path']
        try:
            resolved_path = Path(path).resolve(strict=True)
            resolved_path.relative_to(HOME_PATH)
            current = os.stat(path, follow_symlinks=False)
            expected = (
                item.get('_st_dev'),
                item.get('_st_ino'),
                item.get('_st_size'),
                item.get('_st_mtime_ns'),
            )
            actual = (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns)
            if any(value is not None for value in expected) and actual != expected:
                raise RuntimeError("bestand is gewijzigd sinds de scan")
            if not os.path.isfile(path):
                raise RuntimeError("pad is geen regulier bestand")
            if not dry_run:
                send2trash(path)
            succeeded.append(path)
        except Exception as e:
            failed.append({"path": path, "error": str(e)})
    return {
        "succeeded": succeeded,
        "failed": failed,
        "total_size_mb": sum(item.get('size_mb', 0) for item in files if item['path'] in succeeded),
    }

# ==================================
# 🧪 TEST BLOK
# ==================================
if __name__ == "__main__":
    print("--- Safe Mac Cleaner Engine Test ---")
    print("Start scan op Downloads...")
    
    # Simpele test zonder GUI
    results, errs, stats = scan_disk(
        directories=[str(Path.home() / "Downloads")],
        min_size_mb=10,
        min_age_days=0,
        age_mode="last_modified",
        top_n=5,
        progress_callback=print
    )
    
    print(f"\nResultaten ({len(results)}):")
    for r in results:
        print(f"- {r['size_mb']:.1f}MB | {r['path']}")
    print(f"\nStatistieken: {stats}")
    
    if errs:
        print(f"\nFouten ({len(errs)} mappen overgeslagen):")
        print(errs[:5])
