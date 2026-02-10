import os
import hashlib
import argparse
from pathlib import Path

def get_file_hash(file_path):
    """Vypočítá SHA-256 hash souboru."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (OSError, IOError) as e:
        print(f"Chyba při čtení souboru {file_path}: {e}")
        return None

def find_and_remove_duplicates(directory, dry_run=True):
    """Najde a případně smaže duplicitní soubory."""
    hashes = {}
    duplicates = []
    
    print(f"Skenuji adresář: {directory}")
    
    path_obj = Path(directory)
    if not path_obj.is_dir():
        print(f"Chyba: {directory} není platný adresář.")
        return

    for path in path_obj.rglob('*'):
        if path.is_file():
            # Přeskočíme samotný skript, pokud je v cílovém adresáři
            if path.resolve() == Path(__file__).resolve():
                continue
                
            f_hash = get_file_hash(path)
            if f_hash:
                if f_hash in hashes:
                    duplicates.append(path)
                else:
                    hashes[f_hash] = path

    if not duplicates:
        print("Nenalezeny žádné duplicitní soubory.")
        return

    print(f"Nalezeno {len(duplicates)} duplicitních souborů:")
    for dup in duplicates:
        print(f" - {dup}")

    if dry_run:
        print("\nToto byl pouze test (dry run). Pro skutečné smazání použijte parametr --delete.")
    else:
        confirm = input(f"\nOpravdu chcete smazat těchto {len(duplicates)} souborů? (ano/ne): ")
        if confirm.lower() in ['ano', 'a', 'yes', 'y']:
            for dup in duplicates:
                try:
                    dup.unlink()
                    print(f"Smazáno: {dup}")
                except Exception as e:
                    print(f"Chyba při mazání {dup}: {e}")
        else:
            print("Mazání zrušeno.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vyhledávání a mazání duplicitních souborů podle hashe.")
    parser.add_argument("directory", help="Adresář, který se má prohledat")
    parser.add_argument("--delete", action="store_true", help="Skutečně smazat nalezené duplicity")
    
    args = parser.parse_args()
    
    find_and_remove_duplicates(args.directory, dry_run=not args.delete)