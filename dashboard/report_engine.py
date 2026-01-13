from fpdf import FPDF
from datetime import datetime
import pandas as pd
import os

class AuditReport(FPDF):
    def header(self):
        # Cabeçalho Profissional
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'SENTINEL | Relatório de Auditoria de Rede', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
        self.line(10, 30, 200, 30)
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generate_pdf(df):
    pdf = AuditReport()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # 1. Resumo Executivo
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "1. Resumo Executivo", 0, 1)
    pdf.set_font("Arial", size=12)
    
    # Cálculos Básicos
    avg_ping = df['ping_ms'].mean()
    max_jitter = df['jitter_ms'].max()
    packet_loss_events = len(df[df['packet_loss'] > 0])
    uptime = 100 - (packet_loss_events / len(df) * 100) if len(df) > 0 else 0

    resumo = (
        f"Durante o período analisado, a rede apresentou uma disponibilidade estimada de {uptime:.2f}%.\n"
        f"A latência média foi de {avg_ping:.1f}ms, com picos de instabilidade (Jitter) chegando a {max_jitter:.1f}ms.\n"
        f"Foram detectados {packet_loss_events} eventos de perda de pacotes."
    )
    pdf.multi_cell(0, 10, resumo)
    pdf.ln(10)

    # 2. Tabela de Evidências (Últimos 10 registros críticos ou recentes)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "2. Evidências Técnicas (Amostra)", 0, 1)
    pdf.set_font("Arial", size=10)

    # Cabeçalho da Tabela
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(45, 10, "Hora", 1, 0, 'C', 1)
    pdf.cell(30, 10, "Ping (ms)", 1, 0, 'C', 1)
    pdf.cell(30, 10, "Jitter (ms)", 1, 0, 'C', 1)
    pdf.cell(30, 10, "Perda %", 1, 0, 'C', 1)
    pdf.cell(40, 10, "Status", 1, 1, 'C', 1)

    # Dados (Pegando os últimos 15 registros para caber na página)
    recent_data = df.head(15)
    
    for index, row in recent_data.iterrows():
        # Destaque em vermelho se houver problema
        if row['status'] != 'OK':
            pdf.set_text_color(255, 0, 0)
        else:
            pdf.set_text_color(0, 0, 0)
            
        timestamp = pd.to_datetime(row['timestamp']).strftime('%H:%M:%S')
        pdf.cell(45, 10, timestamp, 1)
        pdf.cell(30, 10, str(round(row['ping_ms'], 1)), 1)
        pdf.cell(30, 10, str(round(row['jitter_ms'], 1)), 1)
        pdf.cell(30, 10, str(row['packet_loss']), 1)
        pdf.cell(40, 10, row['status'], 1, 1)

    # Salvar
    filename = "Relatorio_Auditoria_Rede.pdf"
    pdf.output(filename)
    return filename