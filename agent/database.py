import sqlite3
from datetime import datetime

class SentinelDB:
    def __init__(self, db_name="sentinel_data.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_table()

    def create_table(self):
        # Adicionamos colunas novas: gateway_ping_ms e trace_log
        query = """
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            ping_ms REAL,
            jitter_ms REAL,
            packet_loss REAL,
            download_mbps REAL,
            upload_mbps REAL,
            dns_response_ms REAL,
            gateway_ping_ms REAL, 
            trace_log TEXT,
            target_host TEXT,
            status TEXT
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def save_metric(self, data):
        query = """
        INSERT INTO metrics 
        (timestamp, ping_ms, jitter_ms, packet_loss, download_mbps, upload_mbps, 
         dns_response_ms, gateway_ping_ms, trace_log, target_host, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (
            datetime.now(),
            data.get('ping'),
            data.get('jitter'),
            data.get('packet_loss'),
            data.get('download'),
            data.get('upload'),
            data.get('dns'),
            data.get('gateway_ping'),  # Novo
            data.get('trace_log'),     # Novo (Evidência Forense)
            data.get('host'),
            data.get('status')
        ))
        self.conn.commit()
        print(f"💾 [DB] Dados salvos com RCA às {datetime.now().strftime('%H:%M:%S')}")

    def get_recent_data(self, limit=10):
        cursor = self.conn.execute(f"SELECT * FROM metrics ORDER BY id DESC LIMIT {limit}")
        return cursor.fetchall()