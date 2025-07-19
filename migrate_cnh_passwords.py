#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 SCRIPT DE MIGRAÇÃO - CNH Passwords
=============================================

Script para migrar CNHs existentes adicionando o campo cnh_password.

NOVA ARQUITETURA:
- CNHs com data_nascimento: senha = DDMM (ex: 15/03 → 1503)
- CNHs sem data_nascimento: senha = 0101 (padrão)

Usage:
    python migrate_cnh_passwords.py

Será executado automaticamente no primeiro startup do servidor.
"""

import sys
import os
from datetime import datetime
import sqlite3

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from __init__ import app
from models import db
from models.cnh_request import CNHRequest

def add_cnh_password_column():
    """
    Adiciona a coluna cnh_password na tabela cnh_requests se ela não existir.
    
    Returns:
        bool: True se a coluna foi adicionada ou já existia
    """
    print("🔧 Verificando estrutura da tabela cnh_requests...")
    
    with app.app_context():
        try:
            # Obter caminho do banco de dados
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            
            # Conectar diretamente ao SQLite
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar se a coluna já existe
            cursor.execute("PRAGMA table_info(cnh_requests)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'cnh_password' in columns:
                print("✅ Coluna 'cnh_password' já existe na tabela")
                conn.close()
                return True
            
            print("➕ Adicionando coluna 'cnh_password' na tabela cnh_requests...")
            
            # Adicionar a nova coluna
            cursor.execute("ALTER TABLE cnh_requests ADD COLUMN cnh_password VARCHAR(4)")
            conn.commit()
            
            print("✅ Coluna 'cnh_password' adicionada com sucesso!")
            
            # Verificar se foi criada corretamente
            cursor.execute("PRAGMA table_info(cnh_requests)")
            columns_after = [column[1] for column in cursor.fetchall()]
            
            if 'cnh_password' in columns_after:
                print("✓ Verificação: Coluna criada corretamente")
                conn.close()
                return True
            else:
                print("❌ Erro: Coluna não foi criada corretamente")
                conn.close()
                return False
                
        except Exception as e:
            print(f"❌ Erro ao adicionar coluna: {str(e)}")
            if 'conn' in locals():
                conn.close()
            return False

def migrate_cnh_passwords():
    """
    Migra CNHs existentes adicionando senhas baseadas na data de nascimento.
    
    Returns:
        tuple: (total_cnhs, cnhs_migradas, cnhs_com_senha, cnhs_sem_data)
    """
    print("🔄 Iniciando migração de senhas CNH...")
    
    with app.app_context():
        try:
            # Buscar todas as CNHs
            cnhs = CNHRequest.query.all()
            total_cnhs = len(cnhs)
            
            if total_cnhs == 0:
                print("✅ Nenhuma CNH encontrada no banco. Migração não necessária.")
                return 0, 0, 0, 0
            
            cnhs_migradas = 0
            cnhs_com_senha = 0
            cnhs_sem_data = 0
            
            print(f"📊 Encontradas {total_cnhs} CNH(s) no banco")
            
            for cnh in cnhs:
                # Verificar se já tem senha definida
                if cnh.cnh_password:
                    cnhs_com_senha += 1
                    print(f"  ✓ CNH {cnh.id}: Já possui senha ({cnh.cnh_password})")
                    continue
                
                # Gerar senha baseada na data de nascimento
                if cnh.data_nascimento:
                    senha = cnh.gerar_senha_cnh()
                    cnh.cnh_password = senha
                    cnhs_migradas += 1
                    print(f"  🔑 CNH {cnh.id}: Senha gerada ({senha}) para data {cnh.data_nascimento.strftime('%d/%m/%Y')}")
                else:
                    # CNH sem data de nascimento - usar padrão
                    cnh.cnh_password = "0101"
                    cnhs_migradas += 1
                    cnhs_sem_data += 1
                    print(f"  📅 CNH {cnh.id}: Senha padrão (0101) - sem data de nascimento")
            
            # Salvar alterações no banco
            if cnhs_migradas > 0:
                db.session.commit()
                print(f"💾 {cnhs_migradas} senha(s) salva(s) no banco com sucesso!")
            else:
                print("ℹ️  Nenhuma migração necessária - todas as CNHs já possuem senha.")
            
            # Resumo da migração
            print("\n📋 RESUMO DA MIGRAÇÃO:")
            print(f"  📊 Total de CNHs: {total_cnhs}")
            print(f"  🔑 CNHs migradas: {cnhs_migradas}")
            print(f"  ✅ CNHs que já tinham senha: {cnhs_com_senha}")
            print(f"  📅 CNHs sem data (senha padrão): {cnhs_sem_data}")
            print(f"  🎯 CNHs com data (senha gerada): {cnhs_migradas - cnhs_sem_data}")
            
            return total_cnhs, cnhs_migradas, cnhs_com_senha, cnhs_sem_data
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro durante a migração: {str(e)}")
            raise e

def validate_migration():
    """
    Valida se a migração foi bem-sucedida verificando se todas as CNHs têm senha.
    
    Returns:
        bool: True se todas as CNHs têm senha definida
    """
    print("\n🔍 Validando migração...")
    
    with app.app_context():
        try:
            # Contar CNHs sem senha
            cnhs_sem_senha = CNHRequest.query.filter(
                (CNHRequest.cnh_password == None) | (CNHRequest.cnh_password == '')
            ).count()
            
            total_cnhs = CNHRequest.query.count()
            
            if cnhs_sem_senha == 0:
                print(f"✅ Validação APROVADA: Todas as {total_cnhs} CNH(s) possuem senha definida!")
                return True
            else:
                print(f"❌ Validação FALHOU: {cnhs_sem_senha} CNH(s) ainda sem senha de {total_cnhs} total")
                return False
                
        except Exception as e:
            print(f"❌ Erro na validação: {str(e)}")
            return False

def test_login_samples():
    """
    Testa o login com algumas CNHs de amostra para verificar se está funcionando.
    """
    print("\n🧪 Testando login com amostras...")
    
    with app.app_context():
        try:
            # Buscar algumas CNHs para testar
            cnhs_sample = CNHRequest.query.limit(3).all()
            
            if not cnhs_sample:
                print("ℹ️  Nenhuma CNH encontrada para teste")
                return
            
            for cnh in cnhs_sample:
                # Testar validação de senha
                senha_esperada = cnh.cnh_password
                if cnh.validar_senha_cnh(senha_esperada):
                    print(f"  ✅ CNH {cnh.id}: Login OK com senha {senha_esperada}")
                    if cnh.data_nascimento:
                        print(f"      📅 Data nascimento: {cnh.data_nascimento.strftime('%d/%m/%Y')} → Senha: {senha_esperada}")
                    else:
                        print(f"      📅 Sem data nascimento → Senha padrão: {senha_esperada}")
                else:
                    print(f"  ❌ CNH {cnh.id}: Login FALHOU com senha {senha_esperada}")
                    
                # Testar senha incorreta
                senha_incorreta = "9999"
                if not cnh.validar_senha_cnh(senha_incorreta):
                    print(f"  🛡️  CNH {cnh.id}: Senha incorreta ({senha_incorreta}) rejeitada corretamente")
                else:
                    print(f"  ⚠️  CNH {cnh.id}: PROBLEMA - Senha incorreta ({senha_incorreta}) foi aceita!")
                    
        except Exception as e:
            print(f"❌ Erro no teste: {str(e)}")

def show_sample_data():
    """
    Mostra algumas CNHs de exemplo com suas senhas para teste manual.
    """
    print("\n📋 EXEMPLOS PARA TESTE MANUAL:")
    print("=" * 40)
    
    with app.app_context():
        try:
            cnhs = CNHRequest.query.limit(5).all()
            
            if not cnhs:
                print("ℹ️  Nenhuma CNH encontrada para mostrar exemplos")
                return
            
            for cnh in cnhs:
                print(f"🔑 CNH ID: {cnh.id}")
                print(f"   👤 Nome: {cnh.nome_completo or 'Não informado'}")
                print(f"   📄 CPF: {cnh.cpf or 'Não informado'}")
                if cnh.data_nascimento:
                    print(f"   📅 Data nascimento: {cnh.data_nascimento.strftime('%d/%m/%Y')}")
                else:
                    print(f"   📅 Data nascimento: Não informada")
                print(f"   🔐 Senha: {cnh.cnh_password}")
                print(f"   🧪 Teste: curl \"http://localhost:5001/api/cnh/consultar/login?cpf={cnh.cpf or '12345678900'}&senha={cnh.cnh_password}\"")
                print("-" * 40)
                
        except Exception as e:
            print(f"❌ Erro ao mostrar exemplos: {str(e)}")

if __name__ == "__main__":
    """
    Executa a migração quando o script é chamado diretamente.
    """
    print("🚀 MIGRAÇÃO DE SENHAS CNH - NOVA ARQUITETURA")
    print("=" * 50)
    
    try:
        # PASSO 1: Adicionar coluna cnh_password na tabela
        if not add_cnh_password_column():
            print("💥 ERRO: Não foi possível adicionar a coluna cnh_password")
            sys.exit(1)
        
        # PASSO 2: Executar migração de dados
        total, migradas, com_senha, sem_data = migrate_cnh_passwords()
        
        # PASSO 3: Validar migração
        if validate_migration():
            print("\n🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            
            # PASSO 4: Executar testes de amostra
            test_login_samples()
            
            # PASSO 5: Mostrar exemplos para teste manual
            show_sample_data()
            
            print(f"\n📞 PRÓXIMOS PASSOS:")
            print(f"  1. Instalar dependência: pip install flask-cors")
            print(f"  2. Reiniciar servidor: python run.py")
            print(f"  3. Testar API com um dos exemplos acima")
            print(f"  4. Desenvolver Servidor B para visualização de CNH")
        else:
            print("\n⚠️  MIGRAÇÃO INCOMPLETA - Verificar logs de erro")
            
    except Exception as e:
        print(f"\n💥 ERRO CRÍTICO: {str(e)}")
        print("Verifique se o banco de dados está acessível e tente novamente.")
        sys.exit(1) 