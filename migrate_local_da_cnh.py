# -*- coding: utf-8 -*-
"""
🔄 Migração - Adicionar campo local_da_cnh na tabela cnh_requests

Script para adicionar o novo campo local_da_cnh na tabela existente.
"""

import sys
import os
import logging

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_local_da_cnh_field():
    """Adiciona campo local_da_cnh na tabela cnh_requests."""
    try:
        from __init__ import app, db
        
        logger.info("🔄 Iniciando migração do campo local_da_cnh...")
        
        with app.app_context():
            # Executar ALTER TABLE para adicionar novo campo
            with db.engine.connect() as conn:
                try:
                    # Adicionar campo local_da_cnh
                    conn.execute(db.text("""
                        ALTER TABLE cnh_requests 
                        ADD COLUMN local_da_cnh VARCHAR(100)
                    """))
                    logger.info("✅ Campo local_da_cnh adicionado")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        logger.info("ℹ️ Campo local_da_cnh já existe")
                    else:
                        logger.error(f"❌ Erro ao adicionar local_da_cnh: {e}")
                        raise e
                
                # Commit das mudanças
                conn.commit()
            
            logger.info("🎉 Migração concluída com sucesso!")
            return True
            
    except Exception as e:
        logger.error(f"💥 Erro na migração: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_local_da_cnh_field()
    if success:
        print("✅ Migração executada com sucesso!")
    else:
        print("❌ Falha na migração!")