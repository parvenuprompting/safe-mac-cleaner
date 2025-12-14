import os
import time
import psutil 
import json
from pathlib import Path
from send2trash import send2trash 

# =======================================================
# ⚙️ CONFIGURATIE 
# =======================================================

# JOUW SPECIFIEKE GEBRUIKERSMAP
USERNAME = "T"

SCAN_DIRECTORIES = [
    f"/Users/{USERNAME}/Downloads",
    f"/Users/{USERNAME}/Desktop",
    f"/Users/{USERNAME}/Documents", 
    f"/Users/{USERNAME}/Movies",    
]

# Startwaarden
MINIMUM_SIZE_MB = 1         
MINIMUM_AGE_DAYS = 7         
TOP_N_RESULTS = 100          
AGE_MODE = "last_used"
DRY_RUN = False              

# Constante voor vertaling in de GUI
AGE_MODES = {
    "last_used": "Laatst gebruikt",
    "last_modified": "Laatst gewijzigd"
}

# Veiligheidsregels: Deze bestanden slaan we ALTIJD over
EXCLUDE_EXTENSIONS = [".app", ".pkg", ".framework", ".DS_Store"]
EXCLUDE_PREFIXES = ['.'] 
EXCLUSION_FILE = os.path.expanduser("~/.smc_exclusions.json")

# ==================================
# 💡 LOGICA FUNCTIES
# ==================================

def get_disk_stats():
    """Haalt de schijfgebruikstatistieken op."""
    partition_path = os.path.expanduser('~') 
    try:
        disk_info = psutil.disk_usage(partition_path)
        return {
            'total_gb': disk_info.total / (1024**3),
            'free_gb': disk_info.free / (1024**3),
            'percent_free': 100.0 - disk_info.percent,
        }
    except:
        return {'total_gb': 0, 'free_gb': 0, 'percent_free': 0}


def get_age_info(path, age_mode):
    """Bepaalt de leeftijd van een bestand."""
    now = time.time()
    try:
        stat = os.stat(path)
        if age_mode == "last_used":
            # atime = access time
            timestamp = stat.st_atime
            source = "atime" 
        else: 
            # mtime = modification time
            timestamp = stat.st_mtime
            source = "mtime" 
            
        age_days = (now - timestamp) / (60 * 60 * 24)
        return age_days, source
    except Exception:
        return 0, "ERROR"

# ==================================
# 🛡️ EXCLUSIE LIJST FUNCTIES
# ==================================

def load_exclusion_list():
    if not os.path.exists(EXCLUSION_FILE): return []
    try:
        with open(EXCLUSION_FILE, 'r') as f: return json.load(f)
    except: return []

def add_to_exclusion_list(path):
    current = load_exclusion_list()
    if path not in current:
        current.append(path)
        try:
            with open(EXCLUSION_FILE, 'w') as f: json.dump(current, f, indent=4)
            return True
        except: return False
    return True

def remove_from_exclusion_list(path):
    current = load_exclusion_list()
    if path in current:
        current.remove(path)
        try:
            with open(EXCLUSION_FILE, 'w') as f: json.dump(current, f, indent=4)
            return True
        except: return False
    return False


def validate_and_scan(top_n_results, minimum_age_days, age_mode, minimum_size_mb):
    """De scanfunctie die de bestanden verzamelt."""
    valid_dirs = []
    
    # Check of mappen bestaan
    for d in SCAN_DIRECTORIES:
        if os.path.isdir(d):
            valid_dirs.append(d)
            
    if not valid_dirs:
        return []

    exclusions = load_exclusion_list()
    candidates = []

    for folder in valid_dirs:
        for root, dirs, files in os.walk(folder):
            
            # Filter verborgen mappen (.git, etc)
            dirs[:] = [d for d in dirs if not d.startswith(tuple(EXCLUDE_PREFIXES))]
            
            for name in files:
                # Sla verborgen bestanden over
                if name.startswith('.'): continue
                
                path = os.path.join(root, name)
                
                # Veiligheidscheck extensies
                if any(name.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                    continue
                
                # Check exclusielijst
                if path in exclusions:
                    continue

                try:
                    stat = os.stat(path)
                    size_mb = stat.st_size / (1024 * 1024)
                    
                    # 1. Filter op grootte
                    if size_mb < minimum_size_mb: continue
                        
                    # 2. Filter op leeftijd
                    age_days, age_source = get_age_info(path, age_mode)
                    if age_days < minimum_age_days: continue
                    
                    # Als we hier zijn, mag het bestand getoond worden
                    candidates.append({
                        "path": path,
                        "size_mb": size_mb,
                        "age_days": age_days,
                        "age_source": age_source,
                        "file_type": Path(path).suffix.lstrip('.') or 'file'
                    })
                except Exception:
                    continue
    
    # Sorteren: Grootste en oudste eerst
    candidates.sort(key=lambda x: (x["size_mb"], x["age_days"]), reverse=True)
    
    return candidates

def execute_deletion(results, indexes):
    """Verplaatst bestanden naar de prullenbak."""
    log = []
    
    for i in indexes:
        if 0 <= i < len(results):
            item = results[i]
            file_path = item['path']
            
            if DRY_RUN:
                log.append(f"DRY-RUN: {item['size_mb']:.2f} MB: {file_path}")
            else:
                try:
                    send2trash(file_path)
                    log.append(f"VERPLAATST: {item['size_mb']:.2f} MB: {file_path}")
                except Exception as e:
                    log.append(f"FOUT bij {file_path}: {e}")
    
    return log