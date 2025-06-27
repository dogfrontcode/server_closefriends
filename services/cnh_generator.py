# services/cnh_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime, date
import logging
import uuid

logger = logging.getLogger(__name__)

class CNHImageGenerator:
    """
    Gerador de imagem CNH básica.
    Versão inicial: imagem em branco com dados de texto simples.
    """
    
    # Configurações da imagem
    IMAGE_WIDTH = 856  # Formato padrão CNH
    IMAGE_HEIGHT = 540
    BACKGROUND_COLOR = (250, 250, 250)  # Branco suave
    TEXT_COLOR = (33, 37, 41)  # Cinza escuro
    HEADER_COLOR = (13, 110, 253)  # Azul Brasil
    ACCENT_COLOR = (25, 135, 84)  # Verde
    BORDER_COLOR = (108, 117, 125)  # Cinza médio
    
    # Diretórios
    OUTPUT_DIR = "static/generated_cnhs"
    FONTS_DIR = "static/fonts"
    
    def __init__(self):
        """Inicializa gerador e garante que diretórios existem."""
        self._ensure_directories()
        self._load_fonts()
    
    def _ensure_directories(self):
        """Cria diretórios necessários se não existirem."""
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.FONTS_DIR, exist_ok=True)
    
    def _load_fonts(self):
        """Carrega fontes para uso na imagem."""
        try:
            # Tentar carregar fonte personalizada (se existir)
            title_font_path = os.path.join(self.FONTS_DIR, "arial_bold.ttf")
            if os.path.exists(title_font_path):
                self.title_font = ImageFont.truetype(title_font_path, 24)
                self.header_font = ImageFont.truetype(title_font_path, 32)
            else:
                # Usar fonte padrão do sistema
                try:
                    self.title_font = ImageFont.truetype("arial.ttf", 24)
                    self.header_font = ImageFont.truetype("arial.ttf", 32)
                except:
                    # Fallback para fonte padrão do Pillow
                    self.title_font = ImageFont.load_default()
                    self.header_font = ImageFont.load_default()
            
            # Fonte para dados
            try:
                self.data_font = ImageFont.truetype("arial.ttf", 18)
                self.small_font = ImageFont.truetype("arial.ttf", 14)
            except:
                self.data_font = ImageFont.load_default()
                self.small_font = ImageFont.load_default()
                
            logger.info("Fontes carregadas com sucesso")
            
        except Exception as e:
            logger.warning(f"Erro ao carregar fontes: {e}. Usando fonte padrão.")
            # Usar fontes padrão
            self.title_font = ImageFont.load_default()
            self.header_font = ImageFont.load_default()
            self.data_font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()
    
    def generate_basic_cnh(self, cnh_request):
        """
        Gera imagem básica de CNH com dados fornecidos.
        
        Args:
            cnh_request: Objeto CNHRequest com dados
            
        Returns:
            str: Caminho do arquivo gerado
            
        Raises:
            Exception: Se houver erro na geração
        """
        try:
            logger.info(f"Iniciando geração de CNH básica - ID: {cnh_request.id}")
            
            # Criar imagem base
            image = Image.new('RGB', (self.IMAGE_WIDTH, self.IMAGE_HEIGHT), self.BACKGROUND_COLOR)
            draw = ImageDraw.Draw(image)
            
            # Desenhar layout básico
            self._draw_header(draw, cnh_request)
            self._draw_photo_placeholder(draw)
            self._draw_personal_data(draw, cnh_request)
            self._draw_cnh_details(draw, cnh_request)
            self._draw_footer(draw, cnh_request)
            
            # Gerar nome único para arquivo
            filename = self._generate_filename(cnh_request)
            filepath = os.path.join(self.OUTPUT_DIR, filename)
            
            # Salvar imagem
            image.save(filepath, 'PNG', quality=95)
            
            logger.info(f"CNH gerada com sucesso - Arquivo: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Erro ao gerar CNH - ID: {cnh_request.id}, Erro: {str(e)}")
            raise e
    
    def _draw_header(self, draw, cnh_request):
        """Desenha cabeçalho da CNH."""
        # Fundo do cabeçalho com gradiente simulado
        header_height = 100
        
        # Gradiente simulado com múltiplas linhas
        for i in range(header_height):
            opacity = 1.0 - (i / header_height) * 0.3
            color = tuple(int(c * opacity) for c in self.HEADER_COLOR)
            draw.line([(0, i), (self.IMAGE_WIDTH, i)], fill=color, width=1)
        
        # Bordas do cabeçalho
        draw.rectangle([0, 0, self.IMAGE_WIDTH, header_height], outline=self.BORDER_COLOR, width=2)
        
        # Logo simulado (círculo)
        logo_size = 40
        logo_x = 30
        logo_y = 30
        draw.ellipse([logo_x, logo_y, logo_x + logo_size, logo_y + logo_size], 
                    fill=(255, 255, 255), outline=self.BORDER_COLOR, width=2)
        
        # Brasão simulado no logo
        center_x = logo_x + logo_size // 2
        center_y = logo_y + logo_size // 2
        draw.text((center_x - 8, center_y - 8), "BR", fill=self.HEADER_COLOR, font=self.small_font)
        
        # Título principal
        title = "CARTEIRA NACIONAL DE HABILITAÇÃO"
        title_bbox = draw.textbbox((0, 0), title, font=self.header_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.IMAGE_WIDTH - title_width) // 2
        draw.text((title_x, 25), title, fill=(255, 255, 255), font=self.header_font)
        
        # Subtítulo
        subtitle = "REPÚBLICA FEDERATIVA DO BRASIL"
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=self.small_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (self.IMAGE_WIDTH - subtitle_width) // 2
        draw.text((subtitle_x, 65), subtitle, fill=(255, 255, 255), font=self.small_font)
        
        # Número de série no canto superior direito
        serial = f"Série: {cnh_request.id:06d}"
        serial_bbox = draw.textbbox((0, 0), serial, font=self.small_font)
        serial_width = serial_bbox[2] - serial_bbox[0]
        draw.text((self.IMAGE_WIDTH - serial_width - 20, 15), serial, 
                 fill=(255, 255, 255, 200), font=self.small_font)
    
    def _draw_photo_placeholder(self, draw):
        """Desenha placeholder para foto com bordas profissionais."""
        # Posição da foto (canto superior direito)
        photo_x = self.IMAGE_WIDTH - 140
        photo_y = 120
        photo_width = 100
        photo_height = 130
        
        # Sombra da foto
        shadow_offset = 3
        draw.rectangle([photo_x + shadow_offset, photo_y + shadow_offset, 
                       photo_x + photo_width + shadow_offset, photo_y + photo_height + shadow_offset], 
                      fill=(0, 0, 0, 50))
        
        # Fundo da foto
        draw.rectangle([photo_x, photo_y, photo_x + photo_width, photo_y + photo_height], 
                      fill=(245, 245, 245), outline=self.BORDER_COLOR, width=2)
        
        # Borda interna
        draw.rectangle([photo_x + 3, photo_y + 3, photo_x + photo_width - 3, photo_y + photo_height - 3], 
                      outline=self.ACCENT_COLOR, width=1)
        
        # Ícone de pessoa
        person_icon = "👤"  # Emoji como placeholder
        person_bbox = draw.textbbox((0, 0), person_icon, font=self.header_font)
        person_width = person_bbox[2] - person_bbox[0]
        person_height = person_bbox[3] - person_bbox[1]
        
        icon_x = photo_x + (photo_width - person_width) // 2
        icon_y = photo_y + (photo_height - person_height) // 2 - 10
        draw.text((icon_x, icon_y), person_icon, font=self.header_font)
        
        # Texto "FOTO" abaixo do ícone
        photo_text = "FOTO"
        photo_text_bbox = draw.textbbox((0, 0), photo_text, font=self.small_font)
        photo_text_width = photo_text_bbox[2] - photo_text_bbox[0]
        
        text_x = photo_x + (photo_width - photo_text_width) // 2
        text_y = icon_y + 40
        draw.text((text_x, text_y), photo_text, fill=self.TEXT_COLOR, font=self.small_font)
    
    def _draw_personal_data(self, draw, cnh_request):
        """Desenha dados pessoais com layout melhorado."""
        # Seção de dados pessoais
        section_y = 120
        section_height = 200
        section_x = 30
        section_width = 550
        
        # Fundo da seção
        draw.rectangle([section_x, section_y, section_x + section_width, section_y + section_height], 
                      fill=(255, 255, 255), outline=self.BORDER_COLOR, width=1)
        
        # Título da seção
        section_title = "DADOS PESSOAIS"
        draw.text((section_x + 10, section_y + 10), section_title, 
                 fill=self.HEADER_COLOR, font=self.title_font)
        
        # Linha divisória
        draw.line([section_x + 10, section_y + 35, section_x + section_width - 10, section_y + 35], 
                 fill=self.ACCENT_COLOR, width=2)
        
        # Dados em duas colunas
        start_y = section_y + 50
        line_height = 30
        col1_x = section_x + 15
        col2_x = section_x + 280
        
        # Coluna 1
        self._draw_modern_field(draw, "NOME COMPLETO", cnh_request.nome_completo.upper(), 
                               col1_x, start_y, 250)
        
        self._draw_modern_field(draw, "CPF", cnh_request.cpf, 
                               col1_x, start_y + line_height, 120)
        
        self._draw_modern_field(draw, "RG", cnh_request.rg, 
                               col1_x, start_y + line_height * 2, 120)
        
        # Coluna 2 (dados da direita)
        data_nasc_formatada = cnh_request.data_nascimento.strftime("%d/%m/%Y")
        idade = cnh_request.get_idade()
        
        self._draw_modern_field(draw, "DATA NASCIMENTO", data_nasc_formatada, 
                               col2_x, start_y + line_height, 100)
        
        self._draw_modern_field(draw, "IDADE", f"{idade} anos", 
                               col2_x, start_y + line_height * 2, 80)
        
        # Categoria destacada
        cat_y = start_y + line_height * 3.5
        self._draw_category_highlight(draw, cnh_request.categoria, col1_x, cat_y)
    
    def _draw_cnh_details(self, draw, cnh_request):
        """Desenha detalhes específicos da CNH com layout moderno."""
        # Seção de detalhes da CNH
        section_y = 340
        section_height = 120
        section_x = 30
        section_width = 550
        
        # Fundo da seção
        draw.rectangle([section_x, section_y, section_x + section_width, section_y + section_height], 
                      fill=(248, 249, 250), outline=self.BORDER_COLOR, width=1)
        
        # Título da seção
        section_title = "INFORMAÇÕES DA HABILITAÇÃO"
        draw.text((section_x + 10, section_y + 10), section_title, 
                 fill=self.HEADER_COLOR, font=self.title_font)
        
        # Linha divisória
        draw.line([section_x + 10, section_y + 35, section_x + section_width - 10, section_y + 35], 
                 fill=self.ACCENT_COLOR, width=2)
        
        # Dados em layout moderno
        start_y = section_y + 50
        col1_x = section_x + 15
        col2_x = section_x + 200
        col3_x = section_x + 380
        
        # Número da CNH (formatado)
        numero_cnh = f"{cnh_request.id:011d}"
        numero_formatado = f"{numero_cnh[:3]}.{numero_cnh[3:6]}.{numero_cnh[6:9]}-{numero_cnh[9:]}"
        self._draw_modern_field(draw, "Nº REGISTRO", numero_formatado, col1_x, start_y, 150)
        
        # Data de emissão
        data_emissao = cnh_request.created_at.strftime("%d/%m/%Y")
        self._draw_modern_field(draw, "EMISSÃO", data_emissao, col2_x, start_y, 100)
        
        # Data de validade (5 anos após emissão)
        from datetime import timedelta
        data_validade = (cnh_request.created_at + timedelta(days=365*5)).strftime("%d/%m/%Y")
        self._draw_modern_field(draw, "VALIDADE", data_validade, col3_x, start_y, 100)
        
        # Segunda linha
        start_y2 = start_y + 40
        
        # Órgão emissor
        self._draw_modern_field(draw, "ÓRGÃO EMISSOR", "DETRAN/SP", col1_x, start_y2, 150)
        
        # Local de emissão
        self._draw_modern_field(draw, "LOCAL", "SÃO PAULO/SP", col2_x, start_y2, 150)
    
    def _draw_footer(self, draw, cnh_request):
        """Desenha rodapé com informações adicionais e elementos de segurança."""
        footer_y = self.IMAGE_HEIGHT - 70
        
        # Fundo do rodapé
        draw.rectangle([0, footer_y - 5, self.IMAGE_WIDTH, self.IMAGE_HEIGHT], 
                      fill=(240, 240, 240), outline=self.BORDER_COLOR, width=1)
        
        # Linha decorativa
        draw.line([30, footer_y + 5, self.IMAGE_WIDTH - 30, footer_y + 5], 
                 fill=self.ACCENT_COLOR, width=2)
        
        # Elementos de segurança simulados
        security_elements = ["🔒", "🛡️", "✓"]
        for i, element in enumerate(security_elements):
            x = 50 + i * 30
            draw.text((x, footer_y + 15), element, font=self.small_font)
        
        # Texto de rodapé
        footer_text = "DOCUMENTO GERADO ELETRONICAMENTE • VÁLIDO EM TODO TERRITÓRIO NACIONAL"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=self.small_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        footer_x = (self.IMAGE_WIDTH - footer_width) // 2
        draw.text((footer_x, footer_y + 15), footer_text, fill=self.TEXT_COLOR, font=self.small_font)
        
        # Data/hora de geração
        timestamp = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
        timestamp_text = f"Emitido em: {timestamp}"
        timestamp_bbox = draw.textbbox((0, 0), timestamp_text, font=self.small_font)
        timestamp_width = timestamp_bbox[2] - timestamp_bbox[0]
        timestamp_x = (self.IMAGE_WIDTH - timestamp_width) // 2
        draw.text((timestamp_x, footer_y + 35), timestamp_text, fill=self.BORDER_COLOR, font=self.small_font)
        
        # Código de verificação simulado
        verification_code = f"Cód. Verificação: {cnh_request.id:06d}-{hash(cnh_request.cpf) % 10000:04d}"
        verification_bbox = draw.textbbox((0, 0), verification_code, font=self.small_font)
        verification_width = verification_bbox[2] - verification_bbox[0]
        verification_x = (self.IMAGE_WIDTH - verification_width) // 2
        draw.text((verification_x, footer_y + 50), verification_code, fill=self.BORDER_COLOR, font=self.small_font)
    
    def _draw_modern_field(self, draw, label, value, x, y, width):
        """
        Desenha um campo moderno com estilo profissional.
        
        Args:
            draw: Objeto ImageDraw
            label: Rótulo do campo
            value: Valor do campo
            x: Posição X
            y: Posição Y
            width: Largura do campo
        """
        # Label em cinza pequeno
        draw.text((x, y), label, fill=self.BORDER_COLOR, font=self.small_font)
        
        # Valor em negrito
        draw.text((x, y + 12), str(value), fill=self.TEXT_COLOR, font=self.data_font)
        
        # Linha de base
        draw.line([x, y + 32, x + width, y + 32], fill=self.BORDER_COLOR, width=1)
    
    def _draw_category_highlight(self, draw, categoria, x, y):
        """Desenha categoria com destaque especial."""
        # Fundo destacado
        cat_width = 200
        cat_height = 40
        
        draw.rectangle([x, y, x + cat_width, y + cat_height], 
                      fill=self.ACCENT_COLOR, outline=self.ACCENT_COLOR, width=2)
        
        # Texto da categoria
        cat_text = f"CATEGORIA {categoria}"
        cat_bbox = draw.textbbox((0, 0), cat_text, font=self.title_font)
        cat_text_width = cat_bbox[2] - cat_bbox[0]
        
        text_x = x + (cat_width - cat_text_width) // 2
        text_y = y + 12
        draw.text((text_x, text_y), cat_text, fill=(255, 255, 255), font=self.title_font)
    
    def _generate_filename(self, cnh_request):
        """
        Gera nome único para arquivo da CNH.
        
        Args:
            cnh_request: Objeto CNHRequest
            
        Returns:
            str: Nome do arquivo
        """
        # Usar ID da CNH + timestamp para garantir unicidade
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cnh_{cnh_request.id:06d}_{timestamp}.png"
        return filename
    
    def generate_thumbnail(self, image_path, max_size=(200, 150)):
        """
        Gera thumbnail da imagem CNH.
        
        Args:
            image_path: Caminho da imagem original
            max_size: Tamanho máximo do thumbnail
            
        Returns:
            str: Caminho do thumbnail
        """
        try:
            # Abrir imagem original
            with Image.open(image_path) as img:
                # Criar thumbnail
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Gerar nome do thumbnail
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                thumb_filename = f"{base_name}_thumb.png"
                thumb_path = os.path.join(self.OUTPUT_DIR, thumb_filename)
                
                # Salvar thumbnail
                img.save(thumb_path, 'PNG')
                
                logger.info(f"Thumbnail gerado: {thumb_path}")
                return thumb_path
                
        except Exception as e:
            logger.error(f"Erro ao gerar thumbnail: {str(e)}")
            return None
    
    def validate_image(self, image_path):
        """
        Valida se imagem foi gerada corretamente.
        
        Args:
            image_path: Caminho da imagem
            
        Returns:
            bool: True se imagem é válida
        """
        try:
            if not os.path.exists(image_path):
                return False
            
            # Verificar se arquivo não está vazio
            if os.path.getsize(image_path) == 0:
                return False
            
            # Tentar abrir imagem
            with Image.open(image_path) as img:
                # Verificar dimensões
                if img.size != (self.IMAGE_WIDTH, self.IMAGE_HEIGHT):
                    return False
                
                # Verificar formato
                if img.format != 'PNG':
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar imagem: {str(e)}")
            return False

# ==================== FUNÇÃO PRINCIPAL ====================

def gerar_cnh_basica(cnh_request):
    """
    Função principal para gerar CNH básica.
    
    Args:
        cnh_request: Objeto CNHRequest
        
    Returns:
        tuple: (success: bool, image_path: str, error_message: str)
    """
    try:
        generator = CNHImageGenerator()
        
        # Marcar como processando
        cnh_request.marcar_como_processando()
        
        # Gerar imagem
        image_path = generator.generate_basic_cnh(cnh_request)
        
        # Validar imagem gerada
        if not generator.validate_image(image_path):
            error_msg = "Imagem gerada é inválida"
            cnh_request.marcar_como_falha(error_msg)
            return False, None, error_msg
        
        # Gerar thumbnail (opcional)
        generator.generate_thumbnail(image_path)
        
        # Marcar como completa
        cnh_request.marcar_como_completa(image_path)
        
        logger.info(f"CNH gerada com sucesso - ID: {cnh_request.id}, Arquivo: {image_path}")
        return True, image_path, ""
        
    except Exception as e:
        error_msg = f"Erro na geração: {str(e)}"
        cnh_request.marcar_como_falha(error_msg)
        logger.error(f"Erro ao gerar CNH - ID: {cnh_request.id}, Erro: {error_msg}")
        return False, None, error_msg 