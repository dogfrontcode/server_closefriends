# 🚀 Scripts de Push Automático

Este repositório contém scripts para automatizar o processo de git add, commit e push para a branch atual.

## 📋 Scripts Disponíveis

### 1. `quick_push.sh` - Push Rápido ⚡
Script para push automático **sem confirmação**.

**Uso:**
```bash
./quick_push.sh "mensagem do commit"
```

**Exemplo:**
```bash
./quick_push.sh "Corrige bug na validação de dados"
```

**Alias disponível:**
```bash
qp "mensagem do commit"
```

### 2. `auto_push.sh` - Push com Confirmação 🔒
Script para push automático **com confirmação** do usuário.

**Uso:**
```bash
./auto_push.sh "mensagem do commit"
```

**Exemplo:**
```bash
./auto_push.sh "Adiciona nova funcionalidade"
```

## 🛠️ Funcionalidades

### ✅ O que os scripts fazem:
- **Detectam a branch atual** automaticamente
- **Verificam se há mudanças** para commit
- **Adicionam todos os arquivos** (`git add .`)
- **Fazem commit** com a mensagem fornecida
- **Fazem push** para `origin/branch-atual`
- **Mostram status colorido** durante o processo

### 🔍 Verificações automáticas:
- ✅ Verificam se a mensagem foi fornecida
- ✅ Verificam se há mudanças para commit
- ✅ Param na primeira falha (`set -e`)
- ✅ Mostram feedback visual colorido

## 🎨 Output Visual

### Quick Push (`quick_push.sh`):
```
🚀 Push automático iniciado...
📁 Branch: feature/minha-branch
💬 Commit: Minha mensagem de commit
[commit info...]
✅ Push concluído com sucesso!
```

### Auto Push (`auto_push.sh`):
```
[INFO] Branch atual: feature/minha-branch
[INFO] Status atual do Git:
 M arquivo_modificado.py
 A arquivo_novo.py

Deseja continuar com o push automático? (y/n): y
[INFO] Adicionando arquivos...
[INFO] Fazendo commit...
[INFO] Fazendo push para origin/feature/minha-branch...
[SUCCESS] Push automático concluído com sucesso!
```

## 🔧 Configuração

### Permissões de Execução:
```bash
chmod +x auto_push.sh quick_push.sh
```

### Alias no .zshrc:
```bash
echo 'alias qp="./quick_push.sh"' >> ~/.zshrc
source ~/.zshrc
```

## 📚 Exemplos de Uso

### Para mudanças rápidas:
```bash
# Usando o script diretamente
./quick_push.sh "Fix typo"

# Usando o alias
qp "Fix typo"
```

### Para mudanças importantes:
```bash
# Com confirmação
./auto_push.sh "Implementa nova funcionalidade de relatórios"
```

### Para diferentes tipos de commit:
```bash
qp "feat: adiciona endpoint de consulta"
qp "fix: corrige validação de CPF"
qp "docs: atualiza documentação da API"
qp "refactor: melhora estrutura do código"
```

## ⚠️ Cuidados

### ❌ Não usar quando:
- Há conflitos não resolvidos
- Precisa fazer commit parcial (apenas alguns arquivos)
- Está em uma branch compartilhada importante (main/master)
- Precisa fazer rebase antes do push

### ✅ Ideal para:
- Branches de feature pessoais
- Commits rápidos de desenvolvimento
- Correções pequenas
- Atualizações de documentação

## 🏃‍♂️ Fluxo de Trabalho Recomendado

```bash
# 1. Fazer suas modificações
vim meu_arquivo.py

# 2. Push rápido
qp "Implementa validação de dados"

# 3. Continuar desenvolvendo...
```

## 🔄 Branch Atual

Os scripts sempre fazem push para a branch atual, detectada automaticamente:

```bash
git branch --show-current
```

**Exemplo:** Se você está na branch `feature/nova-funcionalidade`, o push será para `origin/feature/nova-funcionalidade`.

---

**💡 Dica:** Use `qp` para commits rápidos e `./auto_push.sh` para commits mais críticos que precisam de confirmação. 