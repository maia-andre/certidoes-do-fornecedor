"""Monta o pacote para Windows: pasta com o executável, o Chromium do Playwright e um zip.

Uso, a partir da raiz do repositório:
    .venv\\Scripts\\python empacotar.py

Resultado em dist\\: a pasta "Certidoes do Fornecedor" e o zip para a release.
"""
import os
import pathlib
import shutil
import subprocess
import sys

from certidoes import __version__

RAIZ = pathlib.Path(__file__).resolve().parent
NOME = "Certidoes do Fornecedor"
DIST = RAIZ / "dist"
BUILD = RAIZ / "build"
PASTA = DIST / NOME
# No executável, o Playwright procura o navegador dentro do próprio pacote
# (PLAYWRIGHT_BROWSERS_PATH=0, definido por ele quando sys.frozen).
NAVEGADORES = PASTA / "_internal" / "playwright" / "driver" / "package" / ".local-browsers"


def main() -> None:
    shutil.rmtree(BUILD, ignore_errors=True)
    shutil.rmtree(DIST, ignore_errors=True)

    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--clean", "--windowed",
            "--name", NOME,
            "--paths", str(RAIZ),
            "--add-data", f"{RAIZ / 'certidoes' / 'ui'}{os.pathsep}certidoes/ui",
            "--distpath", str(DIST),
            "--workpath", str(BUILD),
            "--specpath", str(BUILD),
            str(RAIZ / "certidoes" / "__main__.py"),
        ],
        check=True,
    )

    ambiente = dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=str(NAVEGADORES))
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], env=ambiente, check=True)

    arquivo = shutil.make_archive(
        str(DIST / f"certidoes-do-fornecedor-{__version__}-windows"), "zip", root_dir=DIST, base_dir=NOME
    )
    print(f"Pacote: {PASTA}")
    print(f"Zip:    {arquivo}")


if __name__ == "__main__":
    main()
