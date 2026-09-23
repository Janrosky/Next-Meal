"""Start the local server and open the browser only after a readiness check."""

import argparse
import importlib.util
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


def ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url + '/api/health', timeout=1) as response:
            health = json.load(response)
        with urllib.request.urlopen(url + '/', timeout=1) as response:
            html = response.read().decode('utf-8')
        return health.get('product') == 'Next-Fix' and 'id="root"' in html
    except (OSError, ValueError, urllib.error.URLError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description='Iniciar Next-Fix localmente')
    parser.add_argument('--port', type=int, default=8001)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--check', action='store_true', help='Verificar el arranque y detenerse')
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[2]
    for package in ('fastapi', 'uvicorn', 'sqlalchemy'):
        if importlib.util.find_spec(package) is None:
            print(f'Falta {package}. Ejecuta Instalar.cmd y comprueba que termine correctamente.')
            return 1
    from app.config import Settings

    if not (Settings.from_environment().static_path / 'index.html').is_file():
        print('Falta la interfaz compilada. Ejecuta Instalar.cmd nuevamente.')
        return 1
    url = f'http://127.0.0.1:{args.port}'
    with socket.socket() as probe:
        try:
            probe.bind(('127.0.0.1', args.port))
        except OSError:
            if ready(url):
                print(f'Next-Fix ya esta abierto en {url}')
                if not args.no_browser and not args.check:
                    webbrowser.open(url)
                return 0
            print(f'El puerto {args.port} esta ocupado por otra aplicacion. Cierra esa aplicacion o usa --port con otro puerto.')
            return 1

    process = None
    try:
        process = subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', 'app.main:app', '--app-dir', str(project / 'backend'),
             '--host', '127.0.0.1', '--port', str(args.port)],
            cwd=project,
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                print('No se pudo iniciar Next-Fix. Revisa el error del servidor que aparece arriba.')
                return 1
            if ready(url):
                print(f'Next-Fix listo: {url}', flush=True)
                if args.check:
                    return 0
                if not args.no_browser:
                    webbrowser.open(url)
                print('Mantene esta ventana abierta. Para detener el servidor usa Ctrl+C.', flush=True)
                return process.wait()
            time.sleep(0.2)
        print('El servidor no estuvo listo en 30 segundos. Revisa el error que aparece arriba.')
        return 1
    except KeyboardInterrupt:
        print('\nCerrando Next-Fix...')
        return 0
    except OSError as error:
        print(f'No se pudo iniciar el servidor: {error}')
        return 1
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    raise SystemExit(main())
