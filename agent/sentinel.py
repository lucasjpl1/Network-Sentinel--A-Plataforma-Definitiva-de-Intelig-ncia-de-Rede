import time
import statistics
import speedtest
import dns.resolver
import subprocess
import re
import platform
from ping3 import ping
from database import SentinelDB

# Configurações
TARGET_HOST = "8.8.8.8"
DNS_TARGET = "google.com"
PING_COUNT = 15

db = SentinelDB()

def get_default_gateway():
    """Descobre o IP do Roteador Local (Gateway) no Windows"""
    try:
        # Executa ipconfig e busca a linha do Gateway Padrão
        result = subprocess.check_output("ipconfig", shell=True).decode('cp850', errors='ignore') # cp850 é comum no CMD pt-br
        # Regex simples para pegar o IP
        for line in result.split('\n'):
            if "Gateway" in line or "Padrão" in line:
                ip_search = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line)
                if ip_search:
                    return ip_search.group(0)
    except:
        pass
    return None

def run_forensic_traceroute(target):
    """Roda um tracert real para anexar como prova no relatório"""
    print("🕵️ EXECUTANDO TRACEROUTE FORENSE (Isso pode levar 15s)...")
    try:
        # -d: Não resolve nomes (mais rápido)
        # -h 10: Máximo 10 saltos (suficiente para ver se saiu da operadora)
        # -w 100: Timeout rápido
        cmd = ["tracert", "-d", "-h", "10", "-w", "100", target]
        output = subprocess.check_output(cmd, shell=True).decode('cp850', errors='ignore')
        return output
    except Exception as e:
        return f"Erro no traceroute: {e}"

def get_network_health(host=TARGET_HOST, count=PING_COUNT):
    """Coleta Ping Internet + Ping Gateway para Causa Raiz"""
    latencies = []
    lost = 0
    
    # 1. Identificar Gateway
    gateway_ip = get_default_gateway()
    gateway_ping = 0
    
    # 2. Medir Latência Interna (Gateway)
    if gateway_ip:
        try:
            g_res = ping(gateway_ip, unit='ms', timeout=0.5)
            gateway_ping = round(g_res, 2) if g_res else 999
        except:
            gateway_ping = 999
    
    # 3. Medir Latência Externa (Internet)
    print(f"📡 Medindo estabilidade externa & interna ({gateway_ip})...")
    for _ in range(count):
        try:
            res = ping(host, unit='ms', timeout=1)
            if res is None:
                lost += 1
            else:
                latencies.append(res)
        except:
            lost += 1
        time.sleep(0.1)

    if not latencies:
        return None

    avg_ping = statistics.mean(latencies)
    jitter = statistics.stdev(latencies) if len(latencies) > 1 else 0
    packet_loss_pct = (lost / count) * 100

    return {
        "ping": round(avg_ping, 2),
        "jitter": round(jitter, 2),
        "packet_loss": round(packet_loss_pct, 2),
        "gateway_ping": gateway_ping,
        "gateway_ip": gateway_ip,
        "host": host
    }

def check_dns_speed():
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ['8.8.8.8']
    start = time.time()
    try:
        resolver.resolve(DNS_TARGET, 'A')
        return round((time.time() - start) * 1000, 2)
    except:
        return 0

def job():
    health = get_network_health()
    if not health:
        print("❌ Rede Inacessível")
        return

    dns_time = check_dns_speed()
    
    data = {
        "ping": health['ping'],
        "jitter": health['jitter'],
        "packet_loss": health['packet_loss'],
        "dns": dns_time,
        "gateway_ping": health['gateway_ping'],
        "trace_log": "", # Vazio por padrão
        "host": health['host'],
        "download": 0,
        "upload": 0,
        "status": "OK"
    }

    # --- LÓGICA DE CAUSA RAIZ (RCA) ---
    is_problem = False
    
    # Regra 1: Perda de Pacotes
    if health['packet_loss'] > 2.0:
        data['status'] = "PACKET_LOSS"
        is_problem = True
    
    # Regra 2: Latência Alta
    elif health['ping'] > 100:
        # Aqui entra a inteligência: É interno ou externo?
        if health['gateway_ping'] > 50:
            data['status'] = "INTERNAL_WIFI_ISSUE" # O Gateway também está lento
            print("⚠️ DIAGNÓSTICO: Problema na Rede Interna (Wi-Fi/Cabo)!")
        else:
            data['status'] = "ISP_LATENCY" # Gateway rápido, Internet lenta
            print("⚠️ DIAGNÓSTICO: Problema na Operadora!")
        is_problem = True

    # Se detectou problema, roda a "Perícia" (Traceroute)
    if is_problem:
        trace = run_forensic_traceroute(TARGET_HOST)
        data['trace_log'] = trace
        print("🕵️ Evidência de Traceroute capturada.")

    db.save_metric(data)
    print(f"✅ [{data['status']}] Ext: {data['ping']}ms | Int: {data['gateway_ping']}ms | Jitter: {data['jitter']}ms")

if __name__ == "__main__":
    print("🛡️ SENTINEL V2 - MÓDULO DE CAUSA RAIZ ATIVO")
    print("🕵️ Monitorando Gateway e Rota Externa...")
    try:
        while True:
            job()
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n🛑 Parado.")