import os
import time
import subprocess
from pathlib import Path
from send2trash import send2trash 

# =======================================================
# ⚙️ CONFIGURATIE (MAXIMALE AGRESSIE BINNEN VEILIGE MAPPEN)
# =======================================================

USERNAME = "T"  # <-- UW GEBRUIKERSNAAM
SCAN_DIRECTORIES = [
    f"/Users/{USERNAME}/Downloads",
    f"/Users/{USERNAME}/Desktop",
    f"/Users/{USERNAME}/Documents", 
    f"/Users/{USERNAME}/Movies",    
]

# VERHOOGDE AGRESSIE
MINIMUM_SIZE_MB = 10         # <-- ZEER AGRESSIEF: Zoek nu alles groter dan 10 MB.
MINIMUM_AGE_DAYS = 7         # <-- ZEER AGRESSIEF: Alles ouder dan 1 week is verdacht.
TOP_N_RESULTS = 100           # <-- VERHOOGD: Toon de 100 grootste kandidaten

AGE_MODE = "last_used"       # Gebruikt st_atime (laatst benaderd)
DRY_RUN = False              # LIVE OPSCHONING

EXCLUDE_EXTENSIONS = [".app", ".pkg", ".framework"]
EXCLUDE_PREFIXES = ['.'] # Sluit verborgen bestanden/mappen uit


# ==================================
# 💡 LOGICA FUNCTIES
# ==================================

def get_age_info(path, age_mode):
    """Bepaalt de leeftijd van een bestand op basis van de gekozen mode."""
    now = time.time()
    try:
        stat = os.stat(path)
        if age_mode == "last_used":
            last_used_timestamp = stat.st_atime
            age_source = "atime" # Laatst benaderd (gebruikt)
        else: # last_modified
            last_used_timestamp = stat.st_mtime
            age_source = "mtime" # Laatst gewijzigd
            
        age_days = (now - last_used_timestamp) / (60 * 60 * 24)
        return age_days, age_source
    except Exception:
        return 9999, "ERROR"

def validate_and_scan():
    """Valideert mappen en verzamelt bestanden die voldoen aan de criteria."""
    valid_dirs = []
    # Kritieke systeemmappen uitsluiten
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
                    
                    if size_mb < MINIMUM_SIZE_MB: continue
                        
                    age_days, age_source = get_age_info(path, AGE_MODE)
                    
                    if age_days >= MINIMUM_AGE_DAYS:
                        candidates.append({
                            "path": path,
                            "size_mb": size_mb,
                            "age_days": age_days,
                            "age_source": age_source,
                            "file_type": Path(path).suffix.lstrip('.') or 'file'
                        })
                except Exception:
                    continue
    
    # Sorteer primair op grootte, secundair op ouderdom
    candidates.sort(key=lambda x: (x["size_mb"], x["age_days"]), reverse=True)
    
    # Let op: De lijst kan langer zijn dan TOP_N_RESULTS om de volledige
    # batch-actie mogelijk te maken als de gebruiker meer dan 50 wil zien.
    # Echter, voor de presentatie blijven we bij TOP_N_RESULTS.
    return candidates[:TOP_N_RESULTS]

def execute_deletion(results, indexes):
    """Voert de daadwerkelijke verplaatsing naar de Prullenbak uit."""
    log = []
    
    for i in indexes:
        if 0 <= i < len(results):
            item = results[i]
            action_status = "DRY-RUN" if DRY_RUN else "VERPLAATST"
            
            if DRY_RUN:
                log.append(f"{action_status}: {item['size_mb']:.2f} MB: {item['path']}")
            else:
                try:
                    send2trash(item['path'])
                    log.append(f"{action_status}: {item['size_mb']:.2f} MB: {item['path']}")
                except Exception as e:
                    log.append(f"FOUT bij {item['path']}: {e}")
    
    return log

# ==================================
# 🖥️ HOOFDPROGRAMMA EN INTERACTIE
# ==================================

if __name__ == "__main__":
    
    print(f"🚀 Safe Mac Cleaner v3.2 gestart. Mode: {'DRY-RUN' if DRY_RUN else 'LIVE OPSCHONING'}")
    
    # Stap 1: Scannen en filteren
    ranked_results = validate_and_scan()
    
    if not ranked_results:
        print("\n🎉 Scannen voltooid. Geen bestanden gevonden die voldoen aan de criteria.")
        exit()
        
    # Stap 2: Presentatie van de tabel
    total_size = sum(item['size_mb'] for item in ranked_results)
    print("\n" + "=" * 80)
    print("        🔎 BESLIS-HULP: OUDE BESTANDEN GEVONDEN")
    print("=" * 80)
    print(f"Totaal {len(ranked_results)} bestanden, totale grootte: {total_size:.2f} MB.")
    print(f"Filter: >{MINIMUM_SIZE_MB}MB | >{MINIMUM_AGE_DAYS} dagen niet gebruikt ({AGE_MODE})")
    print("-" * 80)
    
    print(f"{'#':<3} {'Grootte':<9} {'Ouderdom':<9} {'Type':<7} {'Bron':<7} {'Bestand'}")
    print("-" * 80)

    for i, item in enumerate(ranked_results, start=1):
        path_short = str(Path(item['path']).name) 
        print(
            f"{i:<3} {item['size_mb']:<7.1f} MB  {int(item['age_days']):<7}d  "
            f"{item['file_type']:<7} {item['age_source']:<7} {path_short}"
        )

    print("-" * 80)
    
    # Stap 3: Interactieve actie-lus
    print("\nACTIES:")
    print("v 1,3,7 (of v 1) : Verplaats de geselecteerde nummers naar de Prullenbak.")
    print("va               : Verplaats **ALLES** in deze lijst naar Prullenbak.")
    print("p 1              : Open bestand 1 in Finder (voor context).")
    print("q                : Stoppen zonder actie.")
    
    action_log = []
    
    while not action_log: # Blijf vragen totdat een actie is uitgevoerd of gestopt
        action = input("\nVoer uw actie in: ").lower().strip()
        
        if action == 'q':
            print("Operatie geannuleerd. Er is niets verplaatst.")
            break
            
        elif action.startswith('p'):
            try:
                index = int(action.split()[1]) - 1
                subprocess.run(['open', '-R', ranked_results[index]['path']])
                print(f"Finder geopend voor bestand {index + 1}.")
            except Exception:
                print("Ongeldig nummer of fout bij openen.")
                
        elif action == 'va':
            confirm = input(f"WEES ZEKER! Wilt u ECHT alle {len(ranked_results)} bestanden ({total_size:.2f} MB) verplaatsen? (ja/nee): ").lower()
            if confirm == 'ja':
                indexes_to_process = list(range(len(ranked_results)))
                action_log = execute_deletion(ranked_results, indexes_to_process)
            
        elif action.startswith('v'):
            try:
                nums = action.replace('v', '').replace(',', ' ').split()
                indexes_to_process = [int(n) - 1 for n in nums if n.isdigit()]
                
                if indexes_to_process:
                    action_log = execute_deletion(ranked_results, indexes_to_process)
                else:
                    print("Ongeldige invoer. Gebruik 'v 1' of 'v 1,3,7'.")
            except Exception:
                print("Ongeldige invoer. Gebruik 'v 1' of 'v 1,3,7'.")
                
        else:
            print("Onbekende actie. Probeer 'v 1', 'va', 'p 1', of 'q'.")

    # Stap 4: Samenvatting en Logging
    if action_log:
        print("\n" + "=" * 40)
        print("   ✅ OPSCHONINGSSAMENVATTING")
        print("=" * 40)
        
        verplaatste_bestanden = [l for l in action_log if l.startswith('VERPLAATST')]
        
        # FIX: De nieuwe, robuuste logica om de grootte uit de logstring te halen
        try:
            verplaatste_grootte = sum(float(l.split(':')[1].split(' MB')[0].strip()) for l in verplaatste_bestanden)
        except Exception:
            # Fallback als de logica onverhoopt faalt
            verplaatste_grootte = 0 
            
        print(f"Status: **ECHT VERPLAATST** naar de Prullenbak")
        print(f"Aantal verplaatste bestanden: {len(verplaatste_bestanden)}")
        print(f"Totale grootte opgeruimd: **{verplaatste_grootte:.2f} MB**")
        print("\nControleer de Prullenbak als u de bestanden permanent wilt verwijderen.")