# run.py
import sys
import os

# Adiciona o diretório atual ao path para permitir importações
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Importa o app do módulo __init__
try:
    from __init__ import app
except ImportError:
    # Se não conseguir importar, tenta criar o app diretamente
    import __init__
    app = __init__.create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True, port=5001)
