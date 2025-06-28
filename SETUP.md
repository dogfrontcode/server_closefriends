# 🚀 Setup Rápido - OnlyMonkeys

Guia de configuração inicial para novos desenvolvedores.

## ⚡ Instalação Rápida (1 minuto)

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/onlymonkeys.git
cd onlymonkeys

# 2. Instale dependências
pip3 install -r requirements.txt

# 3. Execute o servidor
python3 run.py
```

🎉 **Pronto!** Acesse: http://localhost:5001

## 👤 Usuários de Teste

| Username | Password | Créditos | Descrição |
|----------|----------|----------|-----------|
| `Tidos`  | `123456` | 1140.50  | Admin principal |
| `tidos`  | `123456` | 170.00   | Usuário teste |

## 🧪 Comandos Úteis

### Ver banco de dados
```bash
python3 view_database.py
```

### Adicionar créditos
```bash
# Listar usuários
python3 add_credits_manual.py --list-users

# Adicionar R$ 50 ao usuário
python3 add_credits_manual.py tidos 50.00 "Teste"
```

### Verificar logs
```bash
# Execute o servidor e acompanhe os logs
python3 run.py
```

## 🔧 Resolver Problemas Comuns

### Porta em uso
```bash
# Matar processo na porta 5001
kill -9 $(lsof -ti:5001)
```

### Banco corrompido
```bash
# Backup e recriar
cp instance/app.db instance/backup.db
rm instance/app.db
python3 run.py  # Recria automaticamente
```

## 💰 Testar PIX

1. **Login** com `tidos` / `123456`
2. **Clicar** em "PIX R$ 10,00"
3. **Copiar** código PIX do modal
4. **Aguardar** 15 segundos (timeout em desenvolvimento)

## 📱 URLs Importantes

- **Home**: http://localhost:5001/home
- **Login**: http://localhost:5001/
- **API Health**: http://localhost:5001/api/session/check

## 📚 Próximos Passos

1. **Leia**: `README.md` para visão geral
2. **Estude**: `TECHNICAL_NOTES.md` para detalhes técnicos
3. **Configure**: Credenciais PIX em `controllers/pix_payment.py`
4. **Teste**: Gere uma CNH e faça um PIX

## 🆘 Suporte

- 📖 Documentação completa: `README.md`
- 🔧 Notas técnicas: `TECHNICAL_NOTES.md`
- 💳 Sistema de créditos: `MANUAL_CREDITS.md`
- 🐛 Problemas? Verifique os logs no console

---
**Tempo estimado de setup: < 5 minutos** ⏱️ 