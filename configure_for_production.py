#!/usr/bin/env python3
"""
Script para configurar o sistema para produção na VPS
"""
import os
import sys

def configure_for_production():
    """Configura o sistema para ambiente de produção"""
    
    # 1. Configurar run.py para produção
    run_py_content = '''# run.py

from __init__ import app

if __name__ == '__main__':
    # Configuração para produção na VPS
    app.run(host='0.0.0.0', debug=False, port=5001)
'''
    
    with open('run.py', 'w') as f:
        f.write(run_py_content)
    
    print("✅ run.py configurado para produção (debug=False)")
    
    # 2. Mostrar instruções para CORS
    print("\n🔒 IMPORTANTE - Configure o CORS no __init__.py:")
    print("   Altere as linhas 46-47 de:")
    print('   "origins": ["*"]')
    print("\n   Para:")
    print('   "origins": ["http://31.97.85.23:5001"]')
    
    # 3. Instruções para firewall
    print("\n🛡️  Configure o firewall da VPS:")
    print("   sudo ufw allow 5001")
    print("   sudo ufw enable")
    
    # 4. Comando para rodar na VPS
    print("\n🚀 Para rodar na VPS:")
    print("   python3 run.py")
    print("   ou")
    print("   nohup python3 run.py &")
    
    print("\n✅ Configuração concluída!")

if __name__ == "__main__":
    configure_for_production() 