# 💳 Sistema de Créditos Manuais

Este documento explica como adicionar créditos manualmente aos usuários via linha de comando.

## 🚀 Script: `add_credits_manual.py`

### Uso Básico
```bash
python3 add_credits_manual.py <username> <valor> [descrição]
```

### Exemplos Práticos

#### 1. Adicionar créditos com descrição personalizada
```bash
python3 add_credits_manual.py tidos 50.00 "Crédito promocional"
```

#### 2. Adicionar créditos sem descrição (usa descrição padrão)
```bash
python3 add_credits_manual.py maria 25.50
```

#### 3. Compensação por erro/problema
```bash
python3 add_credits_manual.py joao 100.00 "Compensação por erro no sistema"
```

#### 4. Crédito de cortesia
```bash
python3 add_credits_manual.py ana 15.00 "Cortesia - Cliente VIP"
```

### Comandos Auxiliares

#### Listar usuários disponíveis
```bash
python3 add_credits_manual.py --list-users
# ou
python3 add_credits_manual.py -l
```

#### Ver ajuda completa
```bash
python3 add_credits_manual.py --help
```

## 📊 O que acontece quando você adiciona créditos

1. **Validação**: Verifica se o usuário existe e o valor é positivo
2. **Registro**: Cria uma transação do tipo `manual_credit`
3. **Atualização**: Atualiza o saldo do usuário de forma segura
4. **Log**: Registra a operação nos logs do sistema
5. **Confirmação**: Mostra resumo completo da operação

## ✅ Exemplo de Saída Bem-Sucedida

```
💳 Adicionando R$ 50.00 para o usuário 'tidos'...

✅ CRÉDITOS ADICIONADOS COM SUCESSO!
==================================================
👤 Usuário: tidos (ID: 2)
💰 Valor adicionado: R$ 50.00
📊 Saldo anterior: R$ 120.00
📈 Novo saldo: R$ 170.00
🆔 ID da transação: 47
📝 Descrição: Crédito promocional de teste
==================================================
```

## ⚠️ Casos de Erro

### Usuário não encontrado
```bash
python3 add_credits_manual.py inexistente 50.00
# Output: ❌ Usuário 'inexistente' não encontrado
```

### Valor inválido
```bash
python3 add_credits_manual.py tidos -10.00
# Output: ❌ Valor deve ser positivo: -10.0
```

## 🔄 Tipos de Transação

O script cria transações do tipo:
- **`manual_credit`**: Créditos adicionados manualmente via admin

Essas transações aparecem no histórico do usuário e podem ser consultadas via interface web.

## 🛡️ Segurança

- ✅ Usa os métodos seguros da classe `User`
- ✅ Validação de entrada
- ✅ Registro completo de auditoria
- ✅ Tratamento de erros
- ✅ Transações atômicas no banco

## 📈 Casos de Uso Comuns

1. **Suporte ao Cliente**: Compensar erros do sistema
2. **Promoções**: Adicionar créditos promocionais
3. **Cortesias**: Bonificar clientes especiais
4. **Testes**: Adicionar créditos para testes internos
5. **Correções**: Ajustar saldos após problemas técnicos 