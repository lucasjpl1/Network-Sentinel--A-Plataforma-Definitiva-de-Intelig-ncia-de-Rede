import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import os
import sys

# Adiciona o caminho para importar a IA (ajuste se necessário)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Tenta importar a IA, se falhar, define como None para não quebrar o app
try:
    from core_ai.anomaly import NetworkBrain
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

from report_engine import generate_pdf

# --- CONFIGURAÇÃO DA PÁGINA E CSS ---
st.set_page_config(
    page_title="Sentinel Enterprise",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS PERSONALIZADO PARA VISUAL "ENTERPRISE"
st.markdown("""
<style>
    /* Fonte mais técnica */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Títulos principais */
    h1, h2, h3 {
        letter-spacing: -0.5px;
    }

    /* Estilo dos Cards de Métricas (Hack CSS para Streamlit) */
    [data-testid="stMetric"] {
        background-color: #1E2130; /* Cor de fundo do card */
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #2B2F42;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }

    /* Ajuste de espaçamento geral */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Cor do sucesso (SLA OK) */
    .metric-success {
        color: #00CC96;
    }
    
    /* Cor do erro (SLA Ruim) */
    .metric-error {
        color: #EF553B;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---

def load_data():
    # Caminho relativo para encontrar o DB
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'agent', 'sentinel_data.db')
    
    if not os.path.exists(db_path):
        st.error(f"🔌 Erro: Banco de dados não encontrado em {db_path}.")
        return pd.DataFrame(), db_path

    try:
        conn = sqlite3.connect(db_path)
        # Carrega mais dados para os gráficos de histórico
        df = pd.read_sql_query("SELECT * FROM metrics ORDER BY id DESC LIMIT 1000", conn)
        conn.close()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df, db_path
    except Exception as e:
        st.error(f"Erro BD: {e}")
        return pd.DataFrame(), db_path

# Função para estilizar gráficos Plotly
def style_plotly(fig):
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',    # Fundo transparente
        paper_bgcolor='rgba(0,0,0,0)',   # Fundo transparente
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified", # Tooltip moderno
        xaxis=dict(showgrid=False, zeroline=False), # Remove grades feias
        yaxis=dict(showgrid=True, gridcolor='#2B2F42', zeroline=False), # Grade sutil apenas horizontal
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# --- CARREGAMENTO DE DADOS ---
df, db_path_for_ai = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Sentinel")
    st.markdown("---")
    
    # --- SEÇÃO 1: AUDITORIA ---
    st.subheader("🖨️ Auditoria")
    st.caption("Gere documentação legal da performance de rede.")
    
    if not df.empty:
        if st.button("📄 Gerar Dossiê PDF", type="primary", use_container_width=True):
            with st.spinner("Compilando evidências..."):
                pdf_file = generate_pdf(df) # Usa sua engine atual
                time.sleep(1) # Simula processamento
            
            with open(pdf_file, "rb") as f:
                st.download_button(
                    label="⬇️ Baixar Relatório Final",
                    data=f,
                    file_name=f"Sentinel_Auditoria_{int(time.time())}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            st.success("Dossiê gerado!")
    else:
        st.warning("Aguardando dados para gerar relatórios.")

    # --- SEÇÃO 2: CALCULADORA SLA (NOVO) ---
    st.markdown("---")
    st.subheader("💰 Calculadora Financeira")
    st.caption("Auditoria de contrato e cálculo de multas.")

    # Inputs de Contrato
    contract_value = st.number_input("Valor Mensal (R$)", value=500.0, step=50.0, format="%.2f")
    sla_target = st.slider("Meta de SLA (%)", 90.0, 99.9, 99.0, step=0.1)

    if not df.empty:
        # Lógica de Cálculo (Baseado na janela de dados carregada - aprox. últimas horas)
        # Cada registro ~ 10 segundos
        total_minutes = len(df) * (10 / 60)
        
        # Define o que é "Downtime" (Perda > 0 ou Status != OK)
        downtime_count = len(df[(df['packet_loss'] > 0) | (df['status'] != 'OK')])
        downtime_minutes = downtime_count * (10 / 60)
        
        # Uptime Real
        real_uptime = 100 - ((downtime_minutes / total_minutes) * 100) if total_minutes > 0 else 100
        
        st.divider()
        st.write(f"**Uptime (Janela):** {real_uptime:.2f}%")
        
        if real_uptime < sla_target:
            st.error("❌ SLA Violado")
            # Multa Estimada: (Valor Mensal / Minutos no Mes) * Minutos Offline * 10 (Penalidade)
            minutes_in_month = 30 * 24 * 60
            refund = (contract_value / minutes_in_month) * downtime_minutes * 10
            st.metric("Reembolso Estimado", f"R$ {refund:.2f}")
        else:
            st.success("✅ SLA Cumprido")
            st.caption("Nenhum desconto aplicável no período atual.")
            
    st.markdown("---")
    st.info("**Status do Agente:**\n\nMonitoramento ativo em background.")


# ---CORPO PRINCIPAL ---

# Cabeçalho com Logo e Título
col_header1, col_header2 = st.columns([1, 5])
with col_header1:
    st.markdown("# 🛡️")
with col_header2:
    st.title("Network Sentinel Enterprise")
    st.caption("Plataforma de Observabilidade e Auditoria de SLA em Tempo Real")

st.markdown("---")

if not df.empty:
    latest = df.iloc[0]

    # --- SEÇÃO 1: INTELIGÊNCIA ARTIFICIAL ---
    if AI_AVAILABLE:
        brain = NetworkBrain(db_path_for_ai)
        anomalies = brain.detect_anomalies()

        if anomalies:
            with st.status("🧠 Análise de IA: Anomalias Detectadas", expanded=True, state="error"):
                st.write(f"O motor neural identificou **{len(anomalies)} comportamentos** fora do padrão histórico.")
                for a in anomalies:
                    ts_obj = pd.to_datetime(a['timestamp'])
                    fmt_time = ts_obj.strftime('%H:%M:%S')
                    st.error(f"**[{fmt_time}]** {a['reason']}", icon="⚠️")
                st.caption("ℹ️ Estes alertas baseiam-se no desvio padrão (Z-Score) da sua conexão.")
        else:
            with st.status("🧠 Análise de IA: Comportamento Padrão", expanded=False, state="complete"):
                st.write("Nenhuma anomalia estatística detectada nos últimos ciclos.")
                st.caption("O comportamento da rede está dentro da normalidade aprendida.")
    else:
        st.warning("Módulo de IA não encontrado. Verifique a instalação.")
    
    st.markdown("###")

    # --- SEÇÃO 2: KPIs PRINCIPAIS (CARDS VISUAIS) ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        delta_ping = latest['ping_ms'] - df.iloc[1]['ping_ms'] if len(df) > 1 else 0
        st.metric("📡 Ping (Latência)", f"{latest['ping_ms']:.1f} ms", 
                  delta=f"{delta_ping:.1f} ms", delta_color="inverse")
        
    with kpi2:
        st.metric("⚡ Jitter (Instabilidade)", f"{latest['jitter_ms']:.1f} ms")
        
    with kpi3:
        loss = latest['packet_loss']
        loss_color = "metric-error" if loss > 0 else "metric-success"
        st.markdown(f"""
            <div data-testid="stMetricValue" class="css-1xarl3l e1i5pmia1">
                <div class="css-1wivap2 e1i5pmia3">📦 Perda</div>
                <div class="css-1xarl3l e1i5pmia1 {loss_color}" style="font-size: 32px; font-weight: 600;">
                {loss}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    with kpi4:
        status = latest['status']
        icon = "🟢" if status == 'OK' else "🔴"
        st.metric("Status SLA", f"{icon} {status}")

    st.markdown("---")

    # --- SEÇÃO 3: GRÁFICOS PROFISSIONAIS ---
    
    # Gráfico 1: Latência e Jitter
    st.subheader("📉 Auditoria de Estabilidade")
    
    fig_main = go.Figure()
    
    # Ping
    fig_main.add_trace(go.Scatter(
        x=df['timestamp'], y=df['ping_ms'],
        mode='lines', name='Ping (ms)',
        line=dict(color='#00CC96', width=2, shape='spline'),
        fill='tozeroy', fillcolor='rgba(0, 204, 150, 0.1)'
    ))

    # Jitter
    fig_main.add_trace(go.Scatter(
        x=df['timestamp'], y=df['jitter_ms'],
        mode='lines', name='Jitter (ms)',
        line=dict(color='#EF553B', width=2, shape='spline'),
        fill='tozeroy', fillcolor='rgba(239, 85, 59, 0.2)'
    ))

    fig_main = style_plotly(fig_main)
    fig_main.update_layout(height=350, title_text="Latência vs Instabilidade (Últimos registros)")
    st.plotly_chart(fig_main, use_container_width=True)

    # --- GRÁFICO DE CAUSA RAIZ (INTERNO vs EXTERNO) ---
    st.subheader("🕵️ Diagnóstico de Causa Raiz (Interno vs Operadora)")
    
    # Verifica se a coluna nova existe no DF antes de plotar
    if 'gateway_ping_ms' in df.columns:
        fig_rca = go.Figure()

        # Linha do Gateway (Rede Local) - Laranja Pontilhado
        fig_rca.add_trace(go.Scatter(
            x=df['timestamp'], y=df['gateway_ping_ms'],
            mode='lines', name='Rede Local (Gateway)',
            line=dict(color='#FFA15A', width=2, dash='dot') 
        ))

        # Linha da Internet (Google) - Verde Sólido
        fig_rca.add_trace(go.Scatter(
            x=df['timestamp'], y=df['ping_ms'],
            mode='lines', name='Internet (Operadora)',
            line=dict(color='#00CC96', width=2) 
        ))

        fig_rca = style_plotly(fig_rca)
        fig_rca.update_layout(
            height=350, 
            title_text="Comparativo: A lentidão está no Wi-Fi/Switch ou na Fibra?",
            yaxis_title="Latência (ms)"
        )
        st.plotly_chart(fig_rca, use_container_width=True)
        
        # --- VISUALIZADOR DE TRACEROUTE (EVIDÊNCIA FORENSE) ---
        if 'trace_log' in df.columns:
            trace_events = df[df['trace_log'] != ""]
            trace_events = trace_events.dropna(subset=['trace_log'])
            
            if not trace_events.empty:
                st.subheader("🔍 Evidências Forenses (Traceroute)")
                last_trace = trace_events.iloc[0]
                with st.expander(f"⚠️ Ver Rota da Falha ({last_trace['timestamp'].strftime('%H:%M:%S')})", expanded=True):
                    st.code(last_trace['trace_log'], language="text")
                    st.caption("Este log prova exatamente em qual salto (hop) a conexão foi interrompida ou degradada.")
    else:
        st.warning("⚠️ Atualize o banco de dados rodando o novo Agente Sentinel V2 para ver o gráfico de Causa Raiz.")

    # --- SEÇÃO 4: GRID INFERIOR (DNS e TABELA) ---
    col_dns, col_events = st.columns([3, 2])

    with col_dns:
        st.subheader("🌐 Performance DNS")
        fig_dns = px.area(df, x='timestamp', y='dns_response_ms', 
                          line_shape='spline', color_discrete_sequence=['#636EFA'])
        fig_dns = style_plotly(fig_dns)
        fig_dns.update_layout(height=300, title_text="Tempo de Resolução (ms)", showlegend=False)
        st.plotly_chart(fig_dns, use_container_width=True)

    with col_events:
        st.subheader("⚠️ Log de Eventos Críticos")
        critical_df = df[(df['packet_loss'] > 0) | (df['status'] != 'OK')]
        
        if not critical_df.empty:
            display_df = critical_df[['timestamp', 'packet_loss', 'jitter_ms', 'status']].copy()
            display_df['timestamp'] = display_df['timestamp'].dt.strftime('%H:%M:%S')
            
            st.dataframe(
                display_df.head(10),
                hide_index=True,
                use_container_width=True,
                height=250,
                column_config={
                    "timestamp": st.column_config.TextColumn("Hora"),
                    "packet_loss": st.column_config.ProgressColumn("Perda %", format="%.1f%%", min_value=0, max_value=5),
                    "jitter_ms": st.column_config.NumberColumn("Jitter", format="%.1f ms"),
                    "status": "Status",
                }
            )
        else:
            st.container(border=True).success("✅ Nenhum evento crítico de infraestrutura registrado no período recente.")

else:
    st.info("📡 Aguardando primeira conexão do Agente Sentinela...")
    st.progress(10)
    time.sleep(2)
    st.rerun()

# Auto-refresh suave
time.sleep(5)
st.rerun()