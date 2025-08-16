#!/usr/bin/env python3
"""
Script para executar o DuckTickets localmente
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    print(f"\n🔄 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erro: {result.stderr}")
        return False
    print(f"✅ {description} concluído")
    return True

def main():
    print("🦆 Iniciando DuckTickets localmente...")
    
    # 1. Instalar dependências
    pip_cmd = "pip3" if subprocess.run("which pip3", shell=True, capture_output=True).returncode == 0 else "python3 -m pip"
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Instalando dependências"):
        print("⚠️  Continuando sem instalar dependências...")
    
    # 2. Executar migrations
    if not run_command("python3 -m alembic upgrade head", "Executando migrations"):
        print("⚠️  Continuando sem migrations...")
    
    # 3. Popular dados de exemplo
    if not run_command("python3 scripts/seed.py", "Populando dados de exemplo"):
        print("⚠️  Continuando sem dados de exemplo...")
    
    # 4. Iniciar servidor
    print("\n🚀 Iniciando servidor FastAPI...")
    print("📍 Acesse: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("🛒 Checkout: http://localhost:8000/checkout?event_id=1")
    print("👨💼 Admin: http://localhost:8000/admin/status")
    print("\n⏹️  Pressione Ctrl+C para parar")
    
    try:
        subprocess.run([
            "python3", "-m", "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Servidor parado!")

if __name__ == "__main__":
    main()