import os
import time
import psutil
import json
import logging
from pathlib import Path
from send2trash import send2trash
from typing import List, Dict, Optional, Callable, Any, Tuple

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
    except Exception as e:
        logging.error(f"Fout bij ophalen schijfinfo: {e}")
        return {'total_gb': 0.0, 'free_gb': 0.0, 'percent_free': 0.0}

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
    should_stop: Callable[[], bool]
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
                        continue
                    # Check volledige pad tegen gebruikers-exclusions
                    if entry.path in exclusions:
                        continue
                    
                    # Recurse (duik dieper)
                    _scan_recursive(entry.path, candidates, errors, exclusions, min_size_mb, min_age_days, age_mode, should_stop)

                # 2. Behandel Bestanden
                elif entry.is_file(follow_symlinks=False):
                    name = entry.name
                    if name.startswith('.'): continue
                    if any(name.endswith(ext) for ext in EXCLUDE_EXTENSIONS): continue
                    if entry.path in exclusions: continue

                    try:
                        # Haal cached stat info op (snel!)
                        stat = entry.stat()
                        size_mb = stat.st_size / (1024 * 1024)
                        
                        if size_mb < min_size_mb: continue

                        # Leeftijd berekenen
                        timestamp = stat.st_atime if age_mode == "last_used" else stat.st_mtime
                        age_days = (time.time() - timestamp) / (60 * 60 * 24)

                        if age_days < min_age_days: continue

                        candidates.append({
                            "path": entry.path,
                            "size_mb": size_mb,
                            "age_days": age_days,
                            "file_type": Path(name).suffix or 'file'
                        })

                    except (OSError, PermissionError):
                        # Skip bestand bij fout
                        continue

    except PermissionError:
        errors.append(directory)
    except Exception as e:
        logging.warning(f"Scan fout in {directory}: {e}")

def scan_disk(
    directories: List[str],
    min_size_mb: int,
    min_age_days: int,
    age_mode: str,
    top_n: int,
    progress_callback: Optional[Callable[[str], None]] = None,
    should_stop: Optional[Callable[[], bool]] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Start de scan. Geeft nu een tuple terug: (resultaten, foutmeldingen).
    """
    candidates = []
    errors = []
    exclusions = set(load_exclusion_list())
    
    # Valideer input
    valid_dirs = [d for d in directories if os.path.isdir(d)]
    
    for folder in valid_dirs:
        if should_stop and should_stop(): break
        
        if progress_callback:
            progress_callback(f"Scannen: {folder}")
            
        _scan_recursive(
            folder, candidates, errors, exclusions,
            min_size_mb, min_age_days, age_mode, 
            should_stop or (lambda: False)
        )

    # Sorteren
    if progress_callback:
        progress_callback("Sorteren en opschonen...")
        
    # Sorteer: Grootste & Oudste eerst
    candidates.sort(key=lambda x: (x["size_mb"], x["age_days"]), reverse=True)
    
    return candidates[:top_n], errors

def delete_files(files: List[Dict[str, Any]], dry_run: bool = False) -> List[str]:
    """Verwijdert bestanden via de Prullenbak."""
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

# ==================================
# 🧪 TEST BLOK
# ==================================
if __name__ == "__main__":
    print("--- Safe Mac Cleaner Engine Test ---")
    print("Start scan op Downloads...")
    
    # Simpele test zonder GUI
    results, errs = scan_disk(
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
    
    if errs:
        print(f"\nFouten ({len(errs)} mappen overgeslagen):")
        print(errs[:5])