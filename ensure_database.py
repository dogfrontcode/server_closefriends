#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ GARANTIR BANCO CORRETO - Always Run
=====================================

Script que SEMPRE executa antes do servidor rodar para garantir 
que o banco está com a estrutura correta.

Será chamado automaticamente pelo __init__.py
"""

import sys
import os
import sqlite3
from datetime import date

def ensure_cnh_password_column():
    """Garante que a coluna cnh_password existe, criando se necessário."""
    try:
        # Obter caminho do banco
        from __init__ import app
        with app.app_context():
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            db_path = db_uri.replace('sqlite:///', '')
            
            # Se banco não existe, criar do zero
            if not os.path.exists(db_path):
                print("🆕 Criando banco novo...")
                from models import db
                db.create_all()
                create_admin_and_sample()
                return True
            
            # Verificar se coluna existe
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar se tabela existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cnh_requests'")
            if not cursor.fetchone():
                print("🆕 Tabela cnh_requests não existe, criando...")
                conn.close()
                from models import db
                db.create_all()
                create_admin_and_sample()
                return True
            
            # Verificar se coluna cnh_password existe
            cursor.execute("PRAGMA table_info(cnh_requests)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'cnh_password' not in columns:
                print("➕ Adicionando coluna cnh_password...")
                cursor.execute("ALTER TABLE cnh_requests ADD COLUMN cnh_password VARCHAR(4) DEFAULT '0101'")
                conn.commit()
                print("✅ Coluna adicionada!")
                
                # Popular CNHs existentes com senha 0101
                cursor.execute("UPDATE cnh_requests SET cnh_password = '0101' WHERE cnh_password IS NULL")
                conn.commit()
                print("✅ CNHs existentes atualizadas com senha 0101")
            
            conn.close()
            return True
            
    except Exception as e:
        print(f"⚠️ Erro ao garantir estrutura: {str(e)}")
        return False

def create_admin_and_sample():
    """Cria admin e CNH de exemplo se não existirem."""
    try:
        from __init__ import app
        from models import db
        from models.user import User
        from models.cnh_request import CNHRequest
        
        with app.app_context():
            # Criar admin se não existir
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin', phone_number='11999999999', credits=1000.0)
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin criado: admin/admin123")
            
            # Criar CNH de exemplo se não existir
            if not CNHRequest.query.filter_by(user_id=admin.id).first():
                sample_cnh = CNHRequest(
                    user_id=admin.id,
                    nome_completo="João Silva Santos",
                    cpf="123.456.789-00",
                    data_nascimento=date(1990, 3, 15),
                    categoria_habilitacao="B",
                    custo=5.0,
                    status="completed",
                    cnh_password="1503"  # 15/03
                )
                db.session.add(sample_cnh)
                db.session.commit()
                print("✅ CNH de exemplo criada")
        
        return True
    except Exception as e:
        print(f"⚠️ Erro ao criar dados: {str(e)}")
        return False

def run_database_check():
    """Função principal que executa a verificação."""
    print("🛡️ Verificando estrutura do banco...")
    
    try:
        # Garantir que a coluna existe
        if ensure_cnh_password_column():
            print("✅ Banco está correto!")
            return True
        else:
            print("❌ Problema no banco")
            return False
    except Exception as e:
        print(f"❌ Erro crítico: {str(e)}")
        return False

if __name__ == "__main__":
    # Se executado diretamente, só roda a verificação
    success = run_database_check()
    if success:
        print("🎉 Banco pronto!")
    else:
        print("⚠️ Verificar logs de erro")
    sys.exit(0 if success else 1) 