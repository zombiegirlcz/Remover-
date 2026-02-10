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
        import string
        from ctypes import windll
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append({"name": f"Disk {letter}:", "path": drive})
            bitmask >>= 1
    else:
        drives.append({"name": "Domovský adresář", "path": str(Path.home())})
        try:
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
    
    drives = get_system_drives()
    print("\nNalezené lokace v systému:")
    for i, drive in enumerate(drives):
        print(f"[{i}] {drive['name']} ({drive['path']})")
    print(f"[{len(drives)}] Vlastní cesta (zadat ručně)")

    choice = input("\nVyberte číslo lokace: ").strip()
    try:
        idx = int(choice)
        if idx == len(drives):
            search_path = input("Zadejte absolutní cestu: ").strip()
        else:
            search_path = drives[idx]['path']
    except (ValueError, IndexError):
        print("Neplatná volba.")
        return

    if not os.path.exists(search_path):
        print(f"Chyba: Cesta '{search_path}' neexistuje.")
        return

    print(f"\nSkenuji: {search_path}")
    print("Probíhá výpočet hashů...")
    
    hashes = {}
    file_count = 0
    
    try:
        for root, dirs, files in os.walk(search_path):
            for name in files:
                file_path = Path(os.path.join(root, name))
                if file_path.resolve() == Path(__file__).resolve():
                    continue
                f_hash = get_file_hash(file_path)
                if f_hash:
                    if f_hash not in hashes:
                        hashes[f_hash] = []
                    hashes[f_hash].append(file_path)
                    file_count += 1
                    if file_count % 100 == 0:
                        print(f" Zpracováno {file_count} souborů...", end="\r")
    except KeyboardInterrupt:
        print("\nSkenování přerušeno.")
    
    duplicates = {h: paths for h, paths in hashes.items() if len(paths) > 1}
    
    if not duplicates:
        print("\n\nNenalezeny žádné duplicitní soubory.")
        return

    print(f"\n\nNalezeno {len(duplicates)} skupin duplicit.\n")

    for h, paths in duplicates.items():
        print(f"Skupina (Hash: {h[:12]}...):")
        for i, p in enumerate(paths):
            try:
                size = os.path.getsize(p) / 1024
                print(f"  [{i}] {p} ({size:.2f} KB)")
            except:
                print(f"  [{i}] {p}")
        
        print("\n  [čísla] Smazat tyto indexy | [a] Smazat vše kromě [0] | [s] Přeskočit")
        choice = input("Vaše volba: ").strip().lower()
        
        if choice == 's' or not choice:
            continue
        
        to_delete = []
        if choice == 'a':
            to_delete = paths[1:]
        else:
            try:
                indices = [int(x) for x in choice.split()]
                to_delete = [paths[i] for i in indices]
            except (ValueError, IndexError):
                continue

        for p in to_delete:
            try:
                os.remove(p)
                print(f"  SMAZÁNO: {p}")
            except Exception as e:
                print(f"  CHYBA: {e}")
        print("-" * 30)

    print("\nHotovo.")

if __name__ == "__main__":
    interactive_duplicate_remover()