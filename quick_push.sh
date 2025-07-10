#!/bin/bash

# Script para push automático RÁPIDO (sem confirmação)
# Uso: ./quick_push.sh "mensagem do commit"

set -e

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar mensagem
if [ -z "$1" ]; then
    echo -e "${RED}❌ Mensagem de commit obrigatória!${NC}"
    echo "Uso: ./quick_push.sh \"mensagem\""
    exit 1
fi

COMMIT_MSG="$1"
CURRENT_BRANCH=$(git branch --show-current)

# Verificar se há mudanças
if git diff --quiet && git diff --cached --quiet; then
    echo -e "${BLUE}ℹ️  Nenhuma mudança para commit${NC}"
    exit 0
fi

echo -e "${BLUE}🚀 Push automático iniciado...${NC}"
echo -e "${BLUE}📁 Branch: $CURRENT_BRANCH${NC}"
echo -e "${BLUE}💬 Commit: $COMMIT_MSG${NC}"

# Executar comandos
git add .
git commit -m "$COMMIT_MSG"
git push origin "$CURRENT_BRANCH"

echo -e "${GREEN}✅ Push concluído com sucesso!${NC}" 