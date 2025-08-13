# run.py
import sys
import os

# Adiciona o diretório atual ao path para permitir importações
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from __init__ import app

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True, port=5001)
