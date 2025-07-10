#!/bin/bash

# Script para automatizar push para branch atual
# Uso: ./auto_push.sh "mensagem do commit"

set -e  # Para na primeira falha

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se mensagem de commit foi fornecida
if [ -z "$1" ]; then
    print_error "Mensagem de commit é obrigatória!"
    echo "Uso: ./auto_push.sh \"mensagem do commit\""
    exit 1
fi

COMMIT_MSG="$1"

# Obter branch atual
CURRENT_BRANCH=$(git branch --show-current)
print_status "Branch atual: $CURRENT_BRANCH"

# Verificar se há mudanças
if git diff --quiet && git diff --cached --quiet; then
    print_warning "Nenhuma mudança detectada para commit"
    exit 0
fi

# Mostrar status atual
print_status "Status atual do Git:"
git status --short

# Confirmar se quer continuar
echo ""
read -p "Deseja continuar com o push automático? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Push cancelado pelo usuário"
    exit 0
fi

# Adicionar todos os arquivos
print_status "Adicionando arquivos..."
git add .

# Fazer commit
print_status "Fazendo commit..."
git commit -m "$COMMIT_MSG"

# Fazer push
print_status "Fazendo push para origin/$CURRENT_BRANCH..."
git push origin "$CURRENT_BRANCH"

print_success "Push automático concluído com sucesso!"
print_success "Branch: $CURRENT_BRANCH"
print_success "Commit: $COMMIT_MSG" 