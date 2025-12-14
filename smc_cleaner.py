import os
import time
import psutil
import json
import logging
from pathlib import Path
from send2trash import send2trash
from typing import List, Dict, Optional, Callable, Any

# =======================================================
# ⚙️ CONFIGURATIE & CONSTANTEN
# =======================================================

# Logica config
DEFAULT_MIN_SIZE_MB = 1
DEFAULT_MIN_AGE_DAYS = 7
DEFAULT_TOP_N = 100
DEFAULT_AGE_MODE = "last_used"

# Veiligheidsregels
EXCLUDE_EXTENSIONS = {".app", ".pkg", ".framework", ".DS_Store", ".localized"}
EXCLUDE_PREFIXES = {'.', 'Library', 'System'}
EXCLUSION_FILE = Path.home() / ".smc_exclusions.json"

# Standaard mappen (als fallback)
DEFAULT_SCAN_DIRS = [
    str(Path.home() / "Downloads"),
    str(Path.home() / "Desktop"),
    str(Path.home() / "Documents"),
    str(Path.home() / "Movies"),
]

AGE_MODES = {
    "last_used": "Laatst gebruikt",
    "last_modified": "Laatst gewijzigd"
}

# Logging instellen voor debugging
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
    except Exception as e:
        logging.error(f"Fout bij ophalen schijfinfo: {e}")
        return {'total_gb': 0.0, 'free_gb': 0.0, 'percent_free': 0.0}

def get_age_info(path: str, age_mode: str) -> float:
    """Bepaalt de leeftijd van een bestand in dagen."""
    try:
        stat = os.stat(path)
        timestamp = stat.st_atime if age_mode == "last_used" else stat.st_mtime
        age_days = (time.time() - timestamp) / (60 * 60 * 24)
        return age_days
    except Exception:
        return 0.0

# ==================================
# 🛡️ EXCLUSIE LIJST BEHEER
# ==================================

def load_exclusion_list() -> List[str]:
    if not EXCLUSION_FILE.exists():
        return []
    try:
        with open(EXCLUSION_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Kon exclusielijst niet laden: {e}")
        return []

def toggle_exclusion(path: str, add: bool = True) -> bool:
    current = load_exclusion_list()
    try:
        if add:
            if path not in current:
                current.append(path)
        else:
            if path in current:
                current.remove(path)
        
        with open(EXCLUSION_FILE, 'w') as f:
            json.dump(current, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Fout bij bijwerken exclusielijst: {e}")
        return False

# ==================================
# 🚀 SCAN ENGINE (NU MET PROGRESSIE)
# ==================================

def scan_disk(
    directories: List[str],
    min_size_mb: int,
    min_age_days: int,
    age_mode: str,
    top_n: int,
    progress_callback: Optional[Callable[[str], None]] = None,
    should_stop: Optional[Callable[[], bool]] = None
) -> List[Dict[str, Any]]:
    """
    Scant de schijf met ondersteuning voor voortgang en annulering.
    """
    candidates = []
    exclusions = set(load_exclusion_list())
    
    # Valideer mappen
    valid_dirs = [d for d in directories if os.path.isdir(d)]
    
    for folder in valid_dirs:
        # Check voor annulering
        if should_stop and should_stop():
            return []

        if progress_callback:
            progress_callback(f"Scannen van: {folder}...")

        for root, dirs, files in os.walk(folder):
            if should_stop and should_stop():
                return []
            
            # Filter verborgen/systeem mappen
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in EXCLUDE_PREFIXES]
            
            for name in files:
                # Basis filters
                if name.startswith('.'): continue
                if any(name.endswith(ext) for ext in EXCLUDE_EXTENSIONS): continue
                
                path = os.path.join(root, name)
                if path in exclusions: continue
                
                try:
                    stat = os.stat(path)
                    size_mb = stat.st_size / (1024 * 1024)
                    
                    if size_mb < min_size_mb: continue
                    
                    age_days = get_age_info(path, age_mode)
                    if age_days < min_age_days: continue
                    
                    candidates.append({
                        "path": path,
                        "size_mb": size_mb,
                        "age_days": age_days,
                        "file_type": Path(path).suffix or 'file'
                    })
                except (PermissionError, OSError):
                    continue

    # Sorteren
    if progress_callback:
        progress_callback("Resultaten sorteren...")
        
    candidates.sort(key=lambda x: (x["size_mb"], x["age_days"]), reverse=True)
    return candidates[:top_n]

def delete_files(files: List[Dict[str, Any]], dry_run: bool = False) -> List[str]:
    """Verwijdert bestanden (of simuleert dit)."""
    log = []
    for item in files:
        path = item['path']
        try:
            if not dry_run:
                send2trash(path)
                log.append(f"VERPLAATST: {path}")
            else:
                log.append(f"DRY-RUN: {path}")
        except Exception as e:
            log.append(f"FOUT: {path} - {e}")
    return log