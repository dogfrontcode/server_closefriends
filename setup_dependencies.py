#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SETUP DEPENDÊNCIAS - Nova Arquitetura CNH
==========================================

Script para instalar dependências necessárias para a nova arquitetura.

Usage:
    python setup_dependencies.py
"""

import subprocess
import sys

def install_flask_cors():
    """Instala flask-cors se não estiver instalado."""
    try:
        print("🔧 Verificando flask-cors...")
        import flask_cors
        print("✅ flask-cors já está instalado")
        return True
    except ImportError:
        print("📦 Instalando flask-cors...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "flask-cors==4.0.0"])
            print("✅ flask-cors instalado com sucesso!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar flask-cors: {e}")
            return False

if __name__ == "__main__":
    print("🚀 CONFIGURANDO DEPENDÊNCIAS")
    print("=" * 30)
    
    if install_flask_cors():
        print("\n✅ Todas as dependências estão prontas!")
        print("\n📞 PRÓXIMOS PASSOS:")
        print("  1. python migrate_cnh_passwords.py")
        print("  2. python run.py")
    else:
        print("\n❌ Erro na instalação das dependências")
        sys.exit(1) 