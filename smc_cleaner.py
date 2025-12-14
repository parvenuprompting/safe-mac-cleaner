import os
import time
import psutil 
import json
import getpass
from pathlib import Path
from send2trash import send2trash 

# =======================================================
# ⚙️ CONFIGURATIE (STANDAARDWAARDEN VOOR INSTANTIE)
# =======================================================

# FIX: Automatische detectie van de huidige gebruiker
USERNAME = getpass.getuser()

SCAN_DIRECTORIES = [
    f"/Users/{USERNAME}/Downloads",
    f"/Users/{USERNAME}/Desktop",
    f"/Users/{USERNAME}/Documents", 
    f"/Users/{USERNAME}/Movies",    
]

# De startwaarden die de GUI gebruikt
MINIMUM_SIZE_MB = 1         
MINIMUM_AGE_DAYS = 7         
TOP_N_RESULTS = 100          

AGE_MODE = "last_used"
DRY_RUN = False              

# FIX: Ontbrekende constante toegevoegd voor de GUI
AGE_MODES = {
    "last_used": "Laatst gebruikt",
    "last_modified": "Laatst gewijzigd"
}

EXCLUDE_EXTENSIONS = [".app", ".pkg", ".framework"]
EXCLUDE_PREFIXES = ['.'] 
EXCLUSION_FILE = os.path.expanduser("~/.smc_exclusions.json")

# ==================================
# 💡 LOGICA FUNCTIES
# ==================================

def get_disk_stats():
    """Haalt de schijfgebruikstatistieken op (totaal, vrij, percentage)."""
    partition_path = os.path.expanduser('~') 
    disk_info = psutil.disk_usage(partition_path)
    
    total_gb = disk_info.total / (1024**3)
    free_gb = disk_info.free / (1024**3)
    percent_used = disk_info.percent
    
    return {
        'total_gb': total_gb,
        'free_gb': free_gb,
        'percent_free': 100.0 - percent_used,
    }


def get_age_info(path, age_mode):
    """Bepaalt de leeftijd van een bestand op basis van de gekozen mode."""
    now = time.time()
    try:
        stat = os.stat(path)
        if age_mode == "last_used":
            # atime is 'access time'
            last_used_timestamp = stat.st_atime
            age_source = "atime" 
        else: 
            # mtime is 'modification time'
            last_used_timestamp = stat.st_mtime
            age_source = "mtime" 
            
        age_days = (now - last_used_timestamp) / (60 * 60 * 24)
        return age_days, age_source
    except Exception:
        return 9999, "ERROR"

# ==================================
# 🛡️ EXCLUSIE LIJST FUNCTIES (TOEGEVOEGD)
# ==================================

def load_exclusion_list():
    """Laadt de lijst met permanent uitgesloten bestanden."""
    if not os.path.exists(EXCLUSION_FILE):
        return []
    try:
        with open(EXCLUSION_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def add_to_exclusion_list(path):
    """Voegt een pad toe aan de exclusielijst."""
    current = load_exclusion_list()
    # Voorkom duplicaten
    if path not in current:
        current.append(path)
        try:
            with open(EXCLUSION_FILE, 'w') as f:
                json.dump(current, f, indent=4)
            return True
        except Exception:
            return False
    return True

def remove_from_exclusion_list(path):
    """Verwijdert een pad van de exclusielijst."""
    current = load_exclusion_list()
    if path in current:
        current.remove(path)
        try:
            with open(EXCLUSION_FILE, 'w') as f:
                json.dump(current, f, indent=4)
            return True
        except Exception:
            return False
    return False


def validate_and_scan(top_n_results, minimum_age_days, age_mode, minimum_size_mb):
    """Valideert mappen en verzamelt bestanden die voldoen aan de criteria."""
    valid_dirs = []
    unsafe_dirs = ['/', '/System', '/Library', '/Applications', '/usr']
    
    # Laad de exclusies zodat we deze bestanden kunnen overslaan
    exclusions = load_exclusion_list()

    for d in SCAN_DIRECTORIES:
        p = str(Path(d).expanduser().resolve())
        # Check of map bestaat én veilig is
        if p not in unsafe_dirs and os.path.isdir(p):
            valid_dirs.append(p)
        else:
            # Dit kan gebeuren als bijv. de map 'Movies' niet bestaat
            pass 
            
    if not valid_dirs:
        print("❌ Geen veilige mappen gevonden. Stop met scannen.")
        return []

    candidates = []
    for folder in valid_dirs:
        for root, dirs, files in os.walk(folder):
            
            # Filter verborgen mappen (.git, .vscode etc)
            dirs[:] = [d for d in dirs if not d.startswith(tuple(EXCLUDE_PREFIXES))]
            files = [f for f in files if not f.startswith(tuple(EXCLUDE_PREFIXES))]

            for name in files:
                path = os.path.join(root, name)
                
                # Check 1: Extensies
                if any(name.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                    continue
                
                # Check 2: Exclusielijst (FIX toegevoegd)
                # We checken of het pad in de exclusielijst staat
                # Voor de zekerheid checken we zowel 'met' als 'zonder' file:// prefix
                clean_path = path
                if clean_path in exclusions or ("file://" + clean_path) in exclusions:
                    continue

                try:
                    stat = os.stat(path)
                    size_mb = stat.st_size / (1024 * 1024)
                    
                    if size_mb < minimum_size_mb: continue
                        
                    age_days, age_source = get_age_info(path, age_mode)
                    
                    if age_days >= minimum_age_days:
                        candidates.append({
                            "path": path, # Geen file:// prefix nodig voor os.stat, maar GUI wil het misschien puur
                            "size_mb": size_mb,
                            "age_days": age_days,
                            "age_source": age_source,
                            "file_type": Path(path).suffix.lstrip('.') or 'file'
                        })
                except Exception:
                    continue
    
    candidates.sort(key=lambda x: (x["size_mb"], x["age_days"]), reverse=True)
    
    return candidates

def execute_deletion(results, indexes):
    """Voert de daadwerkelijke verplaatsing naar de Prullenbak uit."""
    log = []
    
    for i in indexes:
        if 0 <= i < len(results):
            item = results[i]
            action_status = "DRY-RUN" if DRY_RUN else "VERPLAATST"
            
            # Zorg dat we een schoon pad hebben
            file_path = item['path'].replace("file://", "")
            
            if DRY_RUN:
                log.append(f"{action_status}: {item['size_mb']:.2f} MB: {file_path}")
            else:
                try:
                    send2trash(file_path)
                    log.append(f"{action_status}: {item['size_mb']:.2f} MB: {file_path}")
                except Exception as e:
                    log.append(f"FOUT bij {file_path}: {e}")
    
    return log