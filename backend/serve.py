"""
Servidor de producción con Waitress para Windows Server 2022.
Uso: python serve.py
"""
import os
import sys

# Asegura que el directorio del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_api.settings')

from waitress import serve
from backend_api.wsgi import application

if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8000
    threads = 8

    print(f'Iniciando servidor Waitress en http://{host}:{port}')
    print('Presiona Ctrl+C para detener.')

    serve(
        application,
        host=host,
        port=port,
        threads=threads,
        channel_timeout=120,
        connection_limit=1000,
        cleanup_interval=30,
        ident='lf-itse',
    )
