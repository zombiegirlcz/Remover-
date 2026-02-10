import os
import hashlib
import platform
import subprocess
from pathlib import Path

def get_file_hash(file_path):
    """Vypočítá SHA-256 hash souboru."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (OSError, IOError):
        return None

def get_system_drives():
    """Vrátí seznam dostupných disků/jednotek v systému."""
    drives = []
    system = platform.system()

    if system == "Windows":
        # Pro Windows zkusíme získat seznam písmen jednotek
        import string
        from ctypes import windll
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive = f"{letter}:"
                if os.path.exists(drive):
                    drives.append({"name": f"Disk {letter}:", "path": drive})
            bitmask >>= 1
    else:
        # Pro Linux/macOS použijeme standardní cesty a mounty
        drives.append({"name": "Domovský adresář", "path": str(Path.home())})
        try:
            # Zkusíme najít další přípojné body (např. v /media nebo /mnt)
            output = subprocess.check_output(['df', '-h']).decode()
            for line in output.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 6:
                    mnt = parts[5]
                    if mnt.startswith(('/media/', '/mnt/')) or mnt == '/':
                        drives.append({"name": f"Mount: {mnt}", "path": mnt})
        except:
            pass
            
    return drives

def interactive_duplicate_remover():
    print("="*40)
    print("  PC ODSTRAŇOVAČ DUPLICIT (HASH-BASED)")
    print("="*40)
    
    # 1. Výběr disku/adresáře
    drives = get_system_drives()
    print("
Nalezené lokace v systému:")
    for i, drive in enumerate(drives):
        print(f"[{i}] {drive['name']} ({drive['path']})")
    print(f"[{len(drives)}] Vlastní cesta (zadat ručně)")

    choice = input("
Vyberte číslo lokace: ").strip()
    try:
        idx = int(choice)
        if idx == len(drives):
            search_path = input("Zadejte absolutní cestu (např. C:\Data): ").strip()
        else:
            search_path = drives[idx]['path']
    except (ValueError, IndexError):
        print("Neplatná volba.")
        return

    if not os.path.exists(search_path):
        print(f"Chyba: Cesta '{search_path}' neexistuje.")
        return

    # 2. Skenování
    print(f"
Skenuji: {search_path}")
    print("Probíhá výpočet hashů, u velkého množství dat to může trvat...")
    
    hashes = {} # hash -> list of paths
    file_count = 0
    
    try:
        # Rekurzivně projdeme adresář
        for root, dirs, files in os.walk(search_path):
            for name in files:
                file_path = Path(os.path.join(root, name))
                
                # Přeskočíme skript samotný
                if file_path.resolve() == Path(__file__).resolve():
                    continue
                
                f_hash = get_file_hash(file_path)
                if f_hash:
                    if f_hash not in hashes:
                        hashes[f_hash] = []
                    hashes[f_hash].append(file_path)
                    file_count += 1
                    if file_count % 100 == 0:
                        print(f" Zpracováno {file_count} souborů...", end="")
    except KeyboardInterrupt:
        print("
Skenování přerušeno uživatelem.")
    
    # 3. Zobrazení výsledků a interaktivní mazání
    duplicates = {h: paths for h, paths in hashes.items() if len(paths) > 1}
    
    if not duplicates:
        print("

Nenalezeny žádné duplicitní soubory.")
        return

    print(f"

Nalezeno {len(duplicates)} skupin duplicitních souborů.
")

    for h, paths in duplicates.items():
        print(f"Skupina stejných souborů (Hash: {h[:12]}...):")
        for i, p in enumerate(paths):
            try:
                size = os.path.getsize(p) / 1024
                print(f"  [{i}] {p} ({size:.2f} KB)")
            except:
                print(f"  [{i}] {p} (Nepodařilo se zjistit velikost)")
        
        print("
  Možnosti:")
        print("  [čísla] Např. '1 2' - smaže soubory s těmito indexy")
        print("  [a]      Smazat VŠECHNY kromě prvního (ponechat jen [0])")
        print("  [s]      Přeskočit (nic nemazat v této skupině)")
        
        choice = input("
Vaše volba: ").strip().lower()
        
        if choice == 's' or not choice:
            print(" Přeskočeno.")
            continue
        
        to_delete = []
        if choice == 'a':
            to_delete = paths[1:]
        else:
            try:
                indices = [int(x) for x in choice.split()]
                to_delete = [paths[i] for i in indices]
            except (ValueError, IndexError):
                print(" Neplatná volba, přeskakuji tuto skupinu.")
                continue

        for p in to_delete:
            try:
                os.remove(p)
                print(f"  ODSTRANĚNO: {p}")
            except Exception as e:
                print(f"  CHYBA při mazání {p}: {e}")
        print("-" * 30)

    print("
Hotovo. Všechny vybrané duplicity byly zpracovány.")

if __name__ == "__main__":
    interactive_duplicate_remover()
