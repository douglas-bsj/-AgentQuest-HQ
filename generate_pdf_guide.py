import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Header banner (pages > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#6366f1"))
            self.drawString(40, 760, "AGENTQUEST HQ — GUIA DE TESTES BETA")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(40, 752, 572, 752)
        
        # Footer
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#94a3b8"))
        self.drawString(40, 30, "AgentQuest HQ • Sistema Operacional de Agentes de IA")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(572, 30, page_text)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(40, 42, 572, 42)
        
        self.restoreState()

def build_pdf():
    pdf_filename = "GUIA_DE_TESTES_AGENTQUEST.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    primary_color = colors.HexColor("#4f46e5")
    dark_text = colors.HexColor("#0f172a")
    gray_text = colors.HexColor("#475569")
    accent_green = colors.HexColor("#059669")
    accent_red = colors.HexColor("#dc2626")

    title_style = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=gray_text,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=dark_text,
        spaceAfter=6
    )

    bold_body_style = ParagraphStyle(
        'BoldBody_Custom',
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=14,
        textColor=dark_text,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'Callout_Text',
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b")
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        fontName='Courier-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#312e81")
    )

    story = []

    # Title & Header
    story.append(Paragraph("🧪 Guia de Testes — AgentQuest HQ", title_style))
    story.append(Paragraph("Manual de Instalação e Roteiro de Validação Local (Via Pen Drive) • <strong>Versão Beta 1.0</strong>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=0, spaceAfter=12))

    # Box: Passo a Passo Inicial
    steps_content = [
        [Paragraph("<b>💾 PASSO 1: Copiar os Arquivos</b><br/>"
                   "Conecte o Pen Drive no computador e copie a pasta <b>agentquest-hq</b> para a sua Área de Trabalho (ou C:\\).", body_style)],
        [Paragraph("<b>🚀 PASSO 2: Iniciar o Sistema (1 Clique)</b><br/>"
                   "Abra a pasta copiada e dê <b>dois cliques</b> no arquivo: <b><code>INSTALAR_E_RODAR.bat</code></b>.<br/>"
                   "• O script configura o ambiente e abre o painel web no navegador em <b>http://127.0.0.1:8000</b>.<br/>"
                   "• Se o computador não tiver Python, o próprio script inicia o instalador incluso (<b>python-installer.exe</b>).", body_style)],
        [Paragraph("<b>🔑 PASSO 3: Configurar sua Chave de IA</b><br/>"
                   "No painel web, clique no ícone <b>⚙️ (Configurações)</b> no topo da tela.<br/>"
                   "Na aba <b>Contas & Provedores IA</b>, insira sua chave (Gemini ou OpenRouter) e clique em <b>Salvar Configurações</b>.", body_style)]
    ]
    
    steps_table = Table(steps_content, colWidths=[532])
    steps_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(steps_table)
    story.append(Spacer(1, 12))

    # Section: Informações sobre Obsidian
    story.append(Paragraph("📂 Sobre o Obsidian (Base de Conhecimento Visual)", h1_style))
    obsidian_box = [
        [Paragraph("<b>💡 O sistema funciona 100% mesmo sem o Obsidian instalado!</b><br/>"
                   "Os agentes salvam automaticamente regras de aprendizado e relatórios na pasta <code>vault/</code>.<br/>"
                   "Caso queira navegar visualmente por essas notas com interface de grafo e mapas mentais:<br/>"
                   "1. Instale o <b>obsidian-installer.exe</b> que está incluso na pasta.<br/>"
                   "2. Abra o Obsidian e escolha: <i>'Abrir pasta como cofre' (Open folder as vault)</i>.<br/>"
                   "3. Selecione a pasta <b>vault</b> do AgentQuest.", callout_style)]
    ]
    obsidian_table = Table(obsidian_box, colWidths=[532])
    obsidian_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ede9fe")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#a78bfa")),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(obsidian_table)
    story.append(Spacer(1, 14))

    # Section: Roteiro de Testes
    story.append(Paragraph("📋 Roteiro de Cenários de Teste", h1_style))
    story.append(Paragraph("Teste as funcionalidades abaixo e observe o comportamento em tempo real do sistema:", body_style))

    scenarios = [
        ["Cenário", "O que fazer", "Resultado esperado"],
        [
            Paragraph("<b>1. Aprovação Direta</b>", body_style),
            Paragraph("Clique em <b>'✅ Aprovar & Executar'</b> em um card pendente.", body_style),
            Paragraph("O card é removido da fila, registrado no histórico do Obsidian e o contador de aprovadas sobe.", body_style)
        ],
        [
            Paragraph("<b>2. Edição de Rascunho</b>", body_style),
            Paragraph("Clique em <b>'✏️ Editar'</b> em um card, altere o texto da IA e clique em <b>'Salvar'</b>.", body_style),
            Paragraph("O texto é atualizado na hora e você pode aprovar a sua versão personalizada.", body_style)
        ],
        [
            Paragraph("<b>3. Rejeição e Aprendizado</b>", body_style),
            Paragraph("Clique em <b>'❌ Rejeitar'</b>. Teste rejeitar direto ou digite uma instrução de melhoria.", body_style),
            Paragraph("Ao ensinar, a IA gera uma nova regra na Base de Conhecimento para não repetir o erro.", body_style)
        ],
        [
            Paragraph("<b>4. Resgate de Rejeitadas</b>", body_style),
            Paragraph("Clique no card de métrica <b>'Rejeitadas ↩️'</b> no topo do painel.", body_style),
            Paragraph("Abre o histórico completo. Você pode <b>Restaurar</b> a mensagem para a fila ou <b>Editar & Aprovar</b>.", body_style)
        ],
        [
            Paragraph("<b>5. Relatórios & BI Hermes</b>", body_style),
            Paragraph("Clique no botão <b>'📊 Relatório'</b> na barra superior e selecione uma visão.", body_style),
            Paragraph("O modal exclusivo de BI carrega sínteses executivas, KPIs e gráficos do negócio.", body_style)
        ],
        [
            Paragraph("<b>6. Configurações Globais</b>", body_style),
            Paragraph("Clique na <b>engrenagem ⚙️</b> e navegue pelas 4 abas.", body_style),
            Paragraph("Permite configurar canais (WhatsApp/Telegram/Email), autonomia dos agentes e diretórios.", body_style)
        ]
    ]

    scenarios_table = Table(scenarios, colWidths=[110, 210, 212])
    scenarios_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(scenarios_table)
    story.append(Spacer(1, 14))

    # Section: Encerramento
    story.append(Paragraph("🛑 Como Finalizar a Sessão de Uso", h1_style))
    story.append(Paragraph(
        "Para encerrar o sistema com segurança, basta <b>fechar a janela preta do terminal</b> que foi aberta pelo arquivo <code>INSTALAR_E_RODAR.bat</code> e fechar a aba no navegador. Nenhum dado ou configuração é perdido.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF gerado com sucesso!")

if __name__ == "__main__":
    build_pdf()
