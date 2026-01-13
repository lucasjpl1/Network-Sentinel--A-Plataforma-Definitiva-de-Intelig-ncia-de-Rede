import pandas as pd
import sqlite3
import os

class NetworkBrain:
    def __init__(self, db_path):
        self.db_path = db_path

    def load_history(self):
        if not os.path.exists(self.db_path):
            return pd.DataFrame()
        
        conn = sqlite3.connect(self.db_path)
        # Carrega muito mais dados para "aprender" o padrão (últimos 2000 registros)
        df = pd.read_sql_query("SELECT * FROM metrics ORDER BY id DESC LIMIT 2000", conn)
        conn.close()
        return df

    def detect_anomalies(self):
        df = self.load_history()
        if df.empty or len(df) < 50:
            return [] # Precisa de dados para aprender

        # IA Estatística: Calcula a Média e o Desvio Padrão
        ping_mean = df['ping_ms'].mean()
        ping_std = df['ping_ms'].std()
        
        jitter_mean = df['jitter_ms'].mean()
        jitter_std = df['jitter_ms'].std()

        # Definição de "Anomalia": Algo que foge 3x do padrão normal (Z-Score > 3)
        # Isso se adapta: se sua rede é sempre instável, a IA "acostuma" e só avisa se piorar muito.
        ping_threshold = ping_mean + (3 * ping_std)
        jitter_threshold = jitter_mean + (3 * jitter_std)

        # Analisa apenas os últimos 10 minutos de dados
        recent = df.head(60) 
        anomalies = []

        for index, row in recent.iterrows():
            reasons = []
            if row['ping_ms'] > ping_threshold:
                reasons.append(f"Ping Anormal ({row['ping_ms']:.1f}ms vs Média {ping_mean:.1f}ms)")
            
            if row['jitter_ms'] > jitter_threshold:
                reasons.append(f"Instabilidade Crítica ({row['jitter_ms']:.1f}ms)")

            if reasons:
                anomalies.append({
                    "timestamp": row['timestamp'],
                    "reason": ", ".join(reasons)
                })

        return anomalies