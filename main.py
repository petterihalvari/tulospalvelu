import subprocess
import sys
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

PIPELINE = [
    ("Haetaan sarjat, ottelut ja kokoonpanot", "tulospalvelu_tilasto.py"),
    ("Rakennetaan pelaajadata", "build_player_data.py"),
    ("Luodaan sarja- ja etusivut", "create_html.py"),
    ("Luodaan ottelusivut", "create_game_html.py"),
    ("Luodaan pelaajasivut", "create_player.py"),
]


def run_step(number, total, description, script_name):
    script_path = BASE_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(
            f"Skriptiä ei löytynyt: {script_path}"
        )

    print()
    print("=" * 60)
    print(f"[{number}/{total}] {description}")
    print(f"Ajetaan: {script_name}")
    print("=" * 60)

    start = time.time()

    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=BASE_DIR,
        check=True,
    )

    elapsed = time.time() - start

    print(f"Valmis: {script_name} ({elapsed:.1f} s)")


def main():
    print()
    print("Jääkiekkotilastojen päivitys")
    print("=" * 60)

    start = time.time()
    total = len(PIPELINE)

    try:
        for number, (description, script_name) in enumerate(
            PIPELINE,
            start=1,
        ):
            run_step(
                number,
                total,
                description,
                script_name,
            )

    except FileNotFoundError as error:
        print()
        print("VIRHE:")
        print(error)
        sys.exit(1)

    except subprocess.CalledProcessError as error:
        print()
        print("PÄIVITYS KESKEYTETTIIN")
        print(
            f"Skripti epäonnistui "
            f"(exit code {error.returncode})."
        )
        sys.exit(error.returncode)

    elapsed = time.time() - start

    print()
    print("=" * 60)
    print("KOKO PÄIVITYS VALMIS")
    print(f"Kokonaisaika: {elapsed:.1f} s")
    print(f"Verkkosivut: {BASE_DIR / 'output'}")
    print("=" * 60)


if __name__ == "__main__":
    main()