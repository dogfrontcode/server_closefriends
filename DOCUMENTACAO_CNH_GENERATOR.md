# 📋 Documentação: Sistema de Coordenadas e Gerador de CNH

## 🎯 Visão Geral

O sistema de geração de CNH funciona através de dois componentes principais:

1. **Sistema de Coordenadas (`coordinates.py`)** - Define onde cada elemento deve ser posicionado na CNH
2. **Gerador de CNH (`cnh_generator.py`)** - Renderiza os elementos na imagem usando as coordenadas

## 🗺️ Sistema de Coordenadas

### Estrutura Base

O arquivo `static/cnh_matriz/coordinates.py` define a matriz de coordenadas baseada no template oficial da CNH brasileira.

```python
# Dimensões do template CNH
TEMPLATE_WIDTH = 700   # pixels
TEMPLATE_HEIGHT = 440  # pixels

# Template base
TEMPLATE_PATH = "static/cnh_matriz/front-cnh.png"
```

### Coordenadas dos Campos

As coordenadas são definidas em formato `(x, y)` onde:
- **x**: Posição horizontal (0 = esquerda, 700 = direita)
- **y**: Posição vertical (0 = topo, 440 = base)

```python
CNH_COORDINATES = {
    "nome_completo": (120.5, 144.5),      # Nome do portador
    "numero_habilitacao": (50, 304),       # Número da habilitação (vertical)
    "data_nascimento": (483, 171),         # Data de nascimento
    "cpf": (315, 305),                     # CPF
    "categoria": (581, 305),               # Categoria (A, B, C, D, E)
    # ... outros campos
}
```

### Configurações de Fonte

Cada campo tem suas próprias configurações de fonte:

```python
FONT_CONFIGS = {
    "nome_completo": {"size": 14, "color": (0, 0, 0)},
    "numero_habilitacao": {"size": 30, "color": (0, 0, 0), "bold": True},
    "validade": {"size": 11, "color": (195, 0, 30)},        # VERMELHO
    "categoria": {"size": 12, "color": (195, 0, 30)},       # VERMELHO
    "numero_registro": {"size": 12, "color": (195, 0, 30), "bold": True}, # VERMELHO + BOLD
    "nacionalidade": {"size": 12, "color": (0, 0, 0)},     # SEMPRE "BRASILEIRO(A)"
    "cpf": {"size": 11, "color": (0, 0, 0)},
    # ... outras configurações
}
```

## 🏗️ Gerador de CNH

### Classe Principal: `CNHImageGenerator`

A classe principal que coordena todo o processo de geração:

```python
class CNHImageGenerator:
    # Configurações da imagem
    IMAGE_WIDTH = 700
    IMAGE_HEIGHT = 440
    TEXT_COLOR = (0, 0, 0)
    
    # Diretórios
    OUTPUT_DIR = "static/generated_cnhs"
    FONTS_DIR = "static/fonts"
    TEMPLATE_PATH = "static/cnh_matriz/front-cnh.png"
```

### Fluxo Principal de Geração

1. **Inicialização** (`__init__`)
   - Cria diretórios necessários
   - Carrega fontes disponíveis

2. **Geração da CNH** (`generate_basic_cnh`)
   - Carrega template base
   - Aplica dados usando coordenadas
   - Processa foto 3x4
   - Processa assinatura
   - Salva arquivo final

3. **Aplicação de Dados** (`_apply_data_with_coordinates`)
   - Itera sobre os campos do CNH request
   - Aplica coordenadas e fontes específicas
   - Trata campos especiais (como número vertical)

## 🎨 Métodos de Renderização

### Texto Normal
```python
def draw_field_if_exists(field_name, text):
    if field_name in CNH_COORDINATES and field_name in FONT_CONFIGS:
        coord = CNH_COORDINATES[field_name]
        font_config = FONT_CONFIGS[field_name]
        font = self._get_font(font_config["size"], bold=font_config.get("bold", False))
        draw.text(coord, str(text), fill=font_config["color"], font=font)
```

### Texto Rotacionado
```python
def _draw_rotated_text(self, draw, text, position, font, color, rotation=90):
    # Cria imagem temporária
    # Desenha texto na imagem temporária
    # Rotaciona a imagem
    # Cola na imagem principal
```

### Número da Habilitação (Caso Especial)
```python
def _draw_numero_habilitacao_vertical(self, draw, numero_text, position):
    # Dimensões específicas: 23x161 pixels
    # Fonte bold obrigatória
    # Rotação 90° para ficar vertical
    # Ajuste automático de tamanho se necessário
```

## 📐 Sistema de Coordenadas Detalhado

### Áreas Principais da CNH

```
┌─────────────────────────────────────────────────────────────────────┐
│ CABEÇALHO (0, 0) - REPÚBLICA FEDERATIVA DO BRASIL                  │
├─────────────────────────────────────────────────────────────────────┤
│ │ FOTO 3x4          │ DADOS PESSOAIS                               │
│ │ (121, 180)        │ Nome: (120.5, 144.5) [PRETO]                │
│ │ 169x237px         │ Data Nasc: (483, 171) [PRETO]               │
│ │                   │ CPF: (315, 305) [PRETO]                      │
│ │                   │ Categoria: (581, 305) [🔴 VERMELHO]         │
├─┼───────────────────┼──────────────────────────────────────────────┤
│N│                   │ INFORMAÇÕES DA HABILITAÇÃO                   │
│Ú│                   │ Data Emissão: (317, 223) [PRETO]             │
│M│                   │ Validade: (440, 223) [🔴 VERMELHO]          │
│E│                   │ Nº Registro: (450, 305) [🔴 VERMELHO+BOLD]   │
│R│                   │ ACC: (579, 213) [PRETO]                       │
│O│                   │                                               │
│ │                   │ FILIAÇÃO                                      │
│(│                   │ Pai: (317, 385) [PRETO]                      │
│5│                   │ Mãe: (317, 400) [PRETO]                      │
│0│                   │                                               │
│,│                   │ ASSINATURA                                    │
│3│                   │ (120, 430) - 168x50px [PRETO]                │
│0│                   │                                               │
│4│                   │                                               │
│)│                   │                                               │
└─┴───────────────────┴──────────────────────────────────────────────┘

LEGENDA DE CORES:
🔴 VERMELHO: Campos de destaque (validade, categoria, numero_registro)
⚫ PRETO: Campos padrão (todos os outros)
```

### Coordenadas Críticas

#### Foto 3x4
```python
FOTO_3X4_AREA = {
    "position": (121, 180),    # Posição x, y
    "width": 169,              # Largura
    "height": 237              # Altura
}
```

#### Assinatura
```python
ASSINATURA_AREA = {
    "position": (120, 430),    # Posição x, y
    "width": 168,              # Largura
    "height": 50               # Altura
}
```

## 🔤 Sistema de Fontes

### Configuração Atual (ASUL)

O sistema foi configurado para usar as fontes **ASUL** como padrão:

- **ASUL-REGULAR.TTF**: Usado para TODOS os campos da CNH
- **ASUL-BOLD.TTF**: Usado APENAS para o número de registro (campo especial)

Esta configuração garante uma aparência consistente em toda a CNH, com destaque especial para o número de registro que usa a versão bold da fonte ASUL.

### Cores Especiais

Alguns campos possuem cores diferenciadas para destaque visual:

#### Campos Vermelhos
- **validade**: Data de validade da CNH - `color: (195, 0, 30)`
- **categoria**: Categoria da habilitação - `color: (195, 0, 30)`  
- **numero_registro**: Número de registro - `color: (195, 0, 30)` + **ASUL-BOLD**

#### Campos Padrão (Preto)
- Todos os outros campos usam cor preta - `color: (0, 0, 0)`
- Fonte padrão: **ASUL-REGULAR.TTF**

#### Campos com Valores Fixos
- **nacionalidade**: Sempre exibe "BRASILEIRO(A)" independentemente do valor do banco de dados
- Esta configuração garante consistência para documentos brasileiros

Esta configuração de cores facilita a identificação visual dos campos mais importantes da CNH.

### Hierarquia de Fontes

1. **Fontes Preferidas** (ASUL)
   - `ASUL-BOLD.TTF` - Para número de registro (campo especial)
   - `ASUL-REGULAR.TTF` - Para todos os outros campos

2. **Fontes Secundárias** (Google Fonts - Arvo)
   - `Arvo-Bold.ttf` - Fallback para negrito
   - `Arvo-Regular.ttf` - Fallback para texto normal

3. **Fontes do Sistema** (Fallback Final)
   - macOS: Arial, Helvetica
   - Linux: DejaVu Sans, Liberation Sans
   - Windows: Arial, Calibri

### Método de Carregamento

```python
def _get_font(self, size, bold=False):
    if bold:
        font_candidates = [
            "static/fonts/ASUL-BOLD.TTF",        # Prioridade: ASUL-BOLD
            "static/fonts/ASUL-REGULAR.TTF",     # Fallback: ASUL-REGULAR
            "static/fonts/Arvo-Bold.ttf",        # Fallback: Arvo-Bold
            "static/fonts/Arvo-Regular.ttf",     # Fallback: Arvo-Regular
        ]
    else:
        font_candidates = [
            "static/fonts/ASUL-REGULAR.TTF",     # Prioridade: ASUL-REGULAR
            "static/fonts/ASUL-BOLD.TTF",        # Fallback: ASUL-BOLD
            "static/fonts/Arvo-Regular.ttf",     # Fallback: Arvo-Regular
            "static/fonts/Arvo-Bold.ttf",        # Fallback: Arvo-Bold
        ]
    
    # Tenta cada fonte da lista
    for font_path in font_candidates:
        try:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, size)
                self._test_font_utf8(font)  # Testa suporte a acentos
                return font
        except Exception:
            continue
    
    # Fallback final
    return ImageFont.load_default()
```

## 🎯 Casos Especiais

### Número da Habilitação Vertical

Este é o caso mais complexo do sistema, pois precisa:

1. **Dimensões Específicas**: 23px largura × 161px altura
2. **Fonte ASUL-BOLD Obrigatória**
3. **Rotação 90°** (texto vertical)
4. **Ajuste Automático** do tamanho da fonte

### Número de Registro (Campo Especial)

O número de registro tem uma configuração especial:

- **Fonte**: ASUL-BOLD.TTF (única exceção ao padrão ASUL-REGULAR)
- **Posição**: Horizontal normal (não rotacionado)
- **Destaque**: Fonte bold para dar ênfase ao número de registro
- **Configuração**: `"numero_registro": {"size": 12, "color": (195, 0, 30), "bold": True}`

### Nacionalidade (Campo Fixo)

O campo nacionalidade tem um comportamento especial:

- **Valor**: Sempre exibe "BRASILEIRO(A)" 
- **Ignorar banco**: Ignora completamente o valor vindo do banco de dados
- **Justificativa**: Garante consistência para CNHs brasileiras
- **Implementação**: Hard-coded no gerador

```python
# No método _apply_data_with_coordinates:
nacionalidade = "BRASILEIRO(A)"  # String fixa sempre
draw_field_if_exists("nacionalidade", nacionalidade)
```

Esta abordagem garante que todas as CNHs geradas tenham nacionalidade brasileira, independentemente de inconsistências nos dados de entrada.

#### Algoritmo de Renderização

```python
def _draw_numero_habilitacao_vertical(self, draw, numero_text, position):
    # 1. Configurações iniciais
    x, y = position
    area_width = 23
    area_height = 161
    
    # 2. Carrega fonte bold
    font = self._get_font(font_size, bold=True)
    
    # 3. Mede o texto
    bbox = draw.textbbox((0, 0), numero_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # 4. Ajusta fonte se necessário
    while text_width > area_height - 10 and current_font_size > 6:
        current_font_size -= 1
        font = self._get_font(current_font_size, bold=True)
        # Remede o texto...
    
    # 5. Cria imagem temporária
    temp_img = Image.new('RGBA', (temp_width, temp_height), (255, 255, 255, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    
    # 6. Desenha texto centralizado
    text_x = (temp_width - text_width) // 2
    text_y = (temp_height - text_height) // 2
    temp_draw.text((text_x, text_y), numero_text, font=font, fill=color)
    
    # 7. Rotaciona 90°
    rotated_img = temp_img.rotate(90, expand=True)
    
    # 8. Calcula posição final
    final_x = x - (rotated_img.width - area_width) // 2
    final_y = y + (area_height - rotated_img.height) // 2
    
    # 9. Cola na imagem principal
    draw._image.paste(rotated_img, (final_x, final_y), rotated_img)
```

## 🛠️ Como Adicionar Novos Campos

### 1. Definir Coordenadas

No arquivo `coordinates.py`:

```python
CNH_COORDINATES = {
    # ... campos existentes
    "novo_campo": (x, y),  # Substitua x, y pelas coordenadas desejadas
}
```

### 2. Definir Configuração de Fonte

```python
FONT_CONFIGS = {
    # ... configurações existentes
    "novo_campo": {"size": 12, "color": (0, 0, 0), "bold": False},  # Preto padrão
    "novo_campo_destaque": {"size": 12, "color": (255, 0, 0), "bold": True},  # Vermelho + Bold
}
```

#### Opções de Cores Disponíveis:
- **Preto**: `(0, 0, 0)` - Cor padrão
- **Vermelho**: `(255, 0, 0)` - Para campos de destaque
- **Azul**: `(0, 0, 255)` - Opcional
- **Verde**: `(0, 128, 0)` - Opcional
- **Cinza**: `(128, 128, 128)` - Para informações secundárias

### 3. Implementar no Gerador

No método `_apply_data_with_coordinates`:

```python
# Novo campo normal (usa valor do banco)
novo_valor = cnh_request.novo_campo or "VALOR_PADRÃO"
draw_field_if_exists("novo_campo", novo_valor)

# Campo fixo (sempre o mesmo valor)
campo_fixo = "VALOR_SEMPRE_FIXO"  # Ignora banco de dados
draw_field_if_exists("campo_fixo", campo_fixo)
```

## 🔍 Debugging e Testes

### Logs de Debug

O sistema inclui logs detalhados:

```python
logger.debug(f"Campo '{field_name}' desenhado: '{text}' em {coord}")
logger.debug(f"Número habilitação vertical '{numero_text}' desenhado em {position}")
```

### Teste de Coordenadas

Para testar novas coordenadas:

```python
def test_coordenadas():
    img = Image.new('RGB', (700, 440), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Desenha retângulo na posição de teste
    x, y = (100, 200)  # Coordenadas a testar
    draw.rectangle([x, y, x + 50, y + 20], outline=(255, 0, 0), width=2)
    
    # Desenha texto
    draw.text((x, y), "TESTE", font=font, fill=(0, 0, 0))
    
    img.save("teste_coordenadas.png")
```

### Teste de Fontes ASUL

Para verificar se as fontes ASUL estão funcionando:

```python
def test_asul_fonts():
    generator = CNHImageGenerator()
    
    # Testar ASUL-REGULAR
    font_regular = generator._get_font(14, bold=False)
    print(f"Fonte regular: {font_regular}")
    
    # Testar ASUL-BOLD
    font_bold = generator._get_font(14, bold=True)
    print(f"Fonte bold: {font_bold}")
    
    # Testar caracteres brasileiros
    test_text = "Teste acentos: ção, ão, ú, é, í, ó, á"
    # Desenhar com ambas as fontes para verificar suporte UTF-8
```

### Teste de Cores Vermelhas

Para verificar se os campos vermelhos estão funcionando:

```python
def test_red_fields():
    from static.cnh_matriz.coordinates import FONT_CONFIGS
    
    # Campos que devem estar em vermelho
    red_fields = ["validade", "categoria", "numero_registro"]
    
    for field_name in red_fields:
        if field_name in FONT_CONFIGS:
            color = FONT_CONFIGS[field_name].get("color", (0, 0, 0))
            is_red = color == (255, 0, 0)
            print(f"Campo '{field_name}': cor {color} - {'✅ VERMELHO' if is_red else '❌ NÃO VERMELHO'}")
    
    # Testar renderização visual
    generator = CNHImageGenerator()
    img = Image.new('RGB', (400, 200), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Desenhar campos vermelhos
    y_pos = 50
    for field_name in red_fields:
        config = FONT_CONFIGS[field_name]
        font = generator._get_font(config["size"], bold=config.get("bold", False))
        draw.text((50, y_pos), f"{field_name}: TESTE", font=font, fill=config["color"])
        y_pos += 30
    
    img.save("test_red_colors.png")
```

## 📊 Estrutura de Arquivos

```
claude/
├── static/
│   ├── cnh_matriz/
│   │   ├── coordinates.py      # ← Coordenadas e configurações
│   │   └── front-cnh.png      # ← Template base da CNH
│   ├── fonts/
│   │   ├── ASUL-BOLD.TTF      # ← Fonte principal bold (número registro)
│   │   ├── ASUL-REGULAR.TTF   # ← Fonte principal regular (todos os campos)
│   │   ├── Arvo-Bold.ttf      # ← Fonte fallback bold
│   │   └── Arvo-Regular.ttf   # ← Fonte fallback regular
│   └── generated_cnhs/        # ← CNHs geradas
├── services/
│   └── cnh_generator.py       # ← Gerador principal
└── models/
    └── cnh_request.py         # ← Modelo de dados
```

## 🎓 Conceitos Importantes

### 1. Sistema de Coordenadas PIL

- **Origem (0,0)**: Canto superior esquerdo
- **Eixo X**: Da esquerda para direita
- **Eixo Y**: De cima para baixo

### 2. Transparência RGBA

- **RGB**: Cor (Red, Green, Blue)
- **A**: Alpha (transparência)
- `(255, 255, 255, 0)` = Branco transparente

### 3. Rotação de Imagens

```python
rotated = img.rotate(90, expand=True)
```
- `expand=True`: Expande a imagem para caber o conteúdo rotacionado

### 4. Máscaras de Transparência

```python
main_image.paste(temp_img, (x, y), temp_img)
```
- O terceiro parâmetro usa a própria imagem como máscara

## 🚀 Otimizações e Boas Práticas

### 1. Cache de Fontes

As fontes são carregadas uma vez e reutilizadas:

```python
def _load_fonts(self):
    self.title_font = self._get_font(24)
    self.header_font = self._get_font(32)
    self.data_font = self._get_font(18)
    self.small_font = self._get_font(14)
```

### 2. Fallbacks Robustos

Sempre ter fallbacks para casos de erro:

```python
try:
    # Operação principal
    complex_operation()
except Exception as e:
    logger.error(f"Erro: {e}")
    # Fallback simples
    simple_fallback()
```

### 3. Validação de Dados

```python
def draw_field_if_exists(field_name, text):
    if text and field_name in CNH_COORDINATES and field_name in FONT_CONFIGS:
        # Desenha apenas se tudo estiver válido
        draw_text()
```

## 🔧 Troubleshooting

### Problema: Texto Cortado

**Causa**: Dimensões da imagem temporária insuficientes
**Solução**: Aumentar margem na criação da imagem temporária

### Problema: Fonte Não Encontrada

**Causa**: Arquivo de fonte não existe
**Solução**: Verificar hierarquia de fallbacks

### Problema: Posicionamento Incorreto

**Causa**: Coordenadas não calibradas com template
**Solução**: Usar ferramenta de medição para verificar posições

### Problema: Fontes ASUL Não Carregam

**Causa**: Arquivos ASUL-BOLD.TTF ou ASUL-REGULAR.TTF não encontrados
**Solução**: 
1. Verificar se os arquivos estão em `static/fonts/`
2. Verificar se os nomes dos arquivos estão corretos (maiúsculas)
3. Verificar permissões dos arquivos
4. O sistema fará fallback para fontes Arvo se ASUL não estiver disponível

### Problema: Acentos Não Aparecem

**Causa**: Fonte ASUL não suporta caracteres UTF-8
**Solução**: 
1. Verificar se a fonte ASUL tem suporte completo a UTF-8
2. O sistema testará automaticamente o suporte a acentos
3. Se falhar, usará fontes de fallback que suportam acentos

### Problema: Campos Não Aparecem em Vermelho

**Causa**: Configuração de cor incorreta ou não aplicada
**Solução**:
1. Verificar se o campo está configurado em `FONT_CONFIGS` com `"color": (255, 0, 0)`
2. Confirmar se o campo existe em `CNH_COORDINATES`
3. Verificar se o método `draw_field_if_exists` está sendo chamado
4. Testar com script de verificação de cores

### Problema: Cor Vermelha Muito Escura ou Clara

**Causa**: Configuração RGB incorreta
**Solução**:
- **Vermelho puro**: `(255, 0, 0)`
- **Vermelho atual**: `(195, 0, 30)` - Tom profissional
- **Vermelho escuro**: `(128, 0, 0)`
- **Vermelho claro**: `(255, 128, 128)`
- Ajustar valores RGB conforme necessário

### Problema: Nacionalidade Aparece Incorreta

**Causa**: Expectativa de que o valor do banco seja usado
**Solução**:
1. **Comportamento correto**: O campo nacionalidade SEMPRE exibe "BRASILEIRO(A)"
2. **Não é bug**: O sistema ignora propositalmente o valor do banco
3. **Justificativa**: Garante consistência para CNHs brasileiras
4. **Alteração**: Para mudar, editar o valor hard-coded no gerador

### Problema: Campo Nacionalidade Não Aparece

**Causa**: Configuração incorreta das coordenadas ou fontes
**Solução**:
1. Verificar se `"nacionalidade"` existe em `CNH_COORDINATES`
2. Verificar se `"nacionalidade"` existe em `FONT_CONFIGS`
3. Confirmar que o método `draw_field_if_exists` está sendo chamado
4. Verificar logs para mensagens de debug

---

## 📚 Referências

- [PIL/Pillow Documentation](https://pillow.readthedocs.io/)
- [ImageDraw Reference](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html)
- [Especificações CNH DENATRAN](https://www.gov.br/infraestrutura/pt-br/assuntos/transito/conteudo-denatran)

---

## 🔄 Histórico de Mudanças

### v2.2 - Nacionalidade Fixa + Ajustes de Tamanho e Cor

**Data**: Implementado conforme solicitação

**Mudanças Realizadas**:
- ✅ Campo **nacionalidade** sempre exibe "BRASILEIRO(A)"
- ✅ Valor ignorado do banco de dados para garantir consistência
- ✅ Alteração da cor vermelha para `(195, 0, 30)` (tom mais escuro)
- ✅ Padronização de tamanhos de fonte para 12px em vários campos
- ✅ Documentação atualizada com seção "Campos Fixos"
- ✅ Testes de verificação realizados e aprovados

**Impacto**:
- Garante consistência de nacionalidade em todas as CNHs
- Tom de vermelho mais profissional e legível
- Melhor padronização visual geral

### v2.1 - Implementação de Campos Vermelhos

**Data**: Implementado conforme solicitação

**Mudanças Realizadas**:
- ✅ Campos **validade**, **categoria** e **numero_registro** em cor vermelha
- ✅ Cor vermelha definida como `(255, 0, 0)` nos três campos
- ✅ Manutenção da fonte ASUL-BOLD para número de registro
- ✅ Documentação atualizada com seção "Cores Especiais"
- ✅ Testes de renderização realizados e aprovados

**Impacto**:
- Maior destaque visual para campos críticos da CNH
- Facilita identificação rápida de informações importantes
- Mantém consistência com fontes ASUL

### v2.0 - Migração para Fontes ASUL

**Data**: Implementado conforme solicitação

**Mudanças Realizadas**:
- ✅ Migração completa de fontes Arvo para ASUL
- ✅ **ASUL-REGULAR.TTF** como fonte padrão para todos os campos
- ✅ **ASUL-BOLD.TTF** exclusivamente para número de registro
- ✅ Manutenção das fontes Arvo como fallback
- ✅ Atualização das configurações em `coordinates.py`
- ✅ Atualização do gerador em `cnh_generator.py`
- ✅ Testes de compatibilidade realizados

**Impacto**:
- Melhor consistência visual na CNH
- Destaque especial para número de registro
- Mantém compatibilidade com sistemas antigos (fallback)

---

*Esta documentação foi criada para facilitar o entendimento e manutenção do sistema de geração de CNH. Para dúvidas ou sugestões, consulte o código-fonte ou entre em contato com a equipe de desenvolvimento.* 