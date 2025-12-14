import os
import time
import psutil 
from pathlib import Path
from send2trash import send2trash 

# =======================================================
# ⚙️ CONFIGURATIE (STANDAARDWAARDEN VOOR INSTANTIE)
# =======================================================

USERNAME = "T"  # <-- UW GEBRUIKERSNAAM
SCAN_DIRECTORIES = [
    f"/Users/{USERNAME}/Downloads",
    f"/Users/{USERNAME}/Desktop",
    f"/Users/{USERNAME}/Documents", 
    f"/Users/{USERNAME}/Movies",    
]

# De startwaarden die de GUI gebruikt, maar de GUI kan ze overschrijven.
MINIMUM_SIZE_MB = 1         
MINIMUM_AGE_DAYS = 7         
TOP_N_RESULTS = 100          

AGE_MODE = "last_used"       
DRY_RUN = False              

EXCLUDE_EXTENSIONS = [".app", ".pkg", ".framework"]
EXCLUDE_PREFIXES = ['.'] 


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
            last_used_timestamp = stat.st_atime
            age_source = "atime" # Laatst benaderd (gebruikt)
        else: # last_modified (of created)
            last_used_timestamp = stat.st_mtime
            age_source = "mtime" 
            
        age_days = (now - last_used_timestamp) / (60 * 60 * 24)
        return age_days, age_source
    except Exception:
        return 9999, "ERROR"

# DEZE FUNCTIE IS AANGEPAST OM DYNAMISCHE FILTERS TE GEBRUIKEN
def validate_and_scan(top_n_results, minimum_age_days, age_mode, minimum_size_mb):
    """Valideert mappen en verzamelt bestanden die voldoen aan de criteria."""
    valid_dirs = []
    unsafe_dirs = ['/', '/System', '/Library', '/Applications', '/usr']
    
    for d in SCAN_DIRECTORIES:
        p = str(Path(d).expanduser().resolve())
        if p not in unsafe_dirs and os.path.isdir(p):
            valid_dirs.append(p)
        else:
            print(f"⚠️ Map uitgesloten (veiligheidsregel): {d}")
            
    if not valid_dirs:
        print("❌ Geen veilige mappen geselecteerd. Stop met scannen.")
        return []

    candidates = []
    for folder in valid_dirs:
        for root, dirs, files in os.walk(folder):
            
            dirs[:] = [d for d in dirs if not d.startswith(tuple(EXCLUDE_PREFIXES))]
            files = [f for f in files if not f.startswith(tuple(EXCLUDE_PREFIXES))]

            for name in files:
                path = os.path.join(root, name)
                
                if any(name.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                    continue

                try:
                    stat = os.stat(path)
                    size_mb = stat.st_size / (1024 * 1024)
                    
                    # GEBRUIK VAN DYNAMISCHE PARAMETER
                    if size_mb < minimum_size_mb: continue
                        
                    # GEBRUIK VAN DYNAMISCHE PARAMETER
                    age_days, age_source = get_age_info(path, age_mode)
                    
                    # GEBRUIK VAN DYNAMISCHE PARAMETER
                    if age_days >= minimum_age_days:
                        candidates.append({
                            "path": "file://" + path, 
                            "size_mb": size_mb,
                            "age_days": age_days,
                            "age_source": age_source,
                            "file_type": Path(path).suffix.lstrip('.') or 'file'
                        })
                except Exception:
                    continue
    
    # Sorteer primair op grootte, secundair op ouderdom
    candidates.sort(key=lambda x: (x["size_mb"], x["age_days"]), reverse=True)
    
    # De GUI is nu verantwoordelijk voor het filteren op TOP_N_RESULTS
    return candidates

def execute_deletion(results, indexes):
    """Voert de daadwerkelijke verplaatsing naar de Prullenbak uit."""
    log = []
    
    for i in indexes:
        if 0 <= i < len(results):
            item = results[i]
            action_status = "DRY-RUN" if DRY_RUN else "VERPLAATST"
            
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