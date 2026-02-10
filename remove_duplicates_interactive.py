import os
import hashlib
from pathlib import Path
import subprocess

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

def get_drives():
    """Vrátí seznam zajímavých cest pro prohledání."""
    drives = [
        {"name": "Termux Home", "path": str(Path.home())},
        {"name": "Internal Storage (SDCard)", "path": "/storage/emulated/0"}
    ]
    # Přidání dalších mountů z df, pokud existují a jsou přístupné
    try:
        output = subprocess.check_output(['df', '-h']).decode()
        for line in output.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 6:
                mnt = parts[5]
                if mnt.startswith('/storage/') and mnt not in [d['path'] for d in drives]:
                    drives.append({"name": f"Drive: {mnt}", "path": mnt})
    except:
        pass
    return [d for d in drives if os.path.exists(d['path'])]

def interactive_duplicate_remover():
    print("--- Interaktivní odstraňovač duplicit ---")
    
    # 1. Výběr disku/adresáře
    drives = get_drives()
    print("
Dostupné lokace k prohledání:")
    for i, drive in enumerate(drives):
        print(f"[{i}] {drive['name']} ({drive['path']})")
    print(f"[{len(drives)}] Vlastní cesta...")

    choice = input("
Vyberte číslo lokace: ")
    try:
        idx = int(choice)
        if idx == len(drives):
            search_path = input("Zadejte absolutní cestu: ")
        else:
            search_path = drives[idx]['path']
    except (ValueError, IndexError):
        print("Neplatná volba.")
        return

    if not os.path.exists(search_path):
        print("Cesta neexistuje.")
        return

    # 2. Skenování
    print(f"
Skenuji {search_path}... (to může chvíli trvat)")
    hashes = {} # hash -> list of paths
    
    path_obj = Path(search_path)
    for path in path_obj.rglob('*'):
        if path.is_file():
            # Přeskočíme skript samotný
            if path.resolve() == Path(__file__).resolve():
                continue
            
            f_hash = get_file_hash(path)
            if f_hash:
                if f_hash not in hashes:
                    hashes[f_hash] = []
                hashes[f_hash].append(path)

    # 3. Zobrazení výsledků a mazání
    duplicates = {h: paths for h, paths in hashes.items() if len(paths) > 1}
    
    if not duplicates:
        print("
Nenalezeny žádné duplicity.")
        return

    print(f"
Nalezeno {len(duplicates)} skupin duplicitních souborů.
")

    for h, paths in duplicates.items():
        print(f"Skupina (Hash: {h[:10]}...):")
        for i, p in enumerate(paths):
            size = os.path.getsize(p) / 1024
            print(f"  [{i}] {p} ({size:.2f} KB)")
        
        print("  [s] Přeskočit tuto skupinu")
        print("  [a] Smazat VŠECHNY kromě prvního ([0])")
        
        choice = input("
Vyberte čísla souborů ke SMAZÁNÍ (oddělená mezerou), nebo 'a'/'s': ").strip().lower()
        
        if choice == 's' or not choice:
            continue
        elif choice == 'a':
            to_delete = paths[1:]
        else:
            try:
                indices = [int(x) for x in choice.split()]
                to_delete = [paths[i] for i in indices]
            except (ValueError, IndexError):
                print("Neplatná volba, přeskakuji.")
                continue

        for p in to_delete:
            try:
                p.unlink()
                print(f"  Smazáno: {p}")
            except Exception as e:
                print(f"  Chyba při mazání {p}: {e}")
        print("-" * 20)

if __name__ == "__main__":
    interactive_duplicate_remover()
