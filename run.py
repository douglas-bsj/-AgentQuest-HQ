"""
AgentQuest HQ - Script de inicialização
Execute: python run.py
"""
import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Garantir que as pastas existem
for folder in ["inbox", "processed", "outputs"]:
    Path(folder).mkdir(exist_ok=True)

if __name__ == "__main__":
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 8000))
    print(f"🤖 AgentQuest HQ iniciando em http://{host}:{port}")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
