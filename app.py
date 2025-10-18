"""
Aplicação Principal - Sistema de Renegociação de Dívidas
Versão Nativa com AgentOS

Este arquivo inicia o servidor usando AgentOS do Agno
que automaticamente cria todos os endpoints FastAPI.
"""

from agents import criar_aplicacao_agno
import os

# Criar a aplicação Agno globalmente
print("=== Sistema de Renegociação de Dívidas ===")
print("Iniciando aplicação com AgentOS...")

agent_os = criar_aplicacao_agno()
print("✓ Endpoints automáticos criados pelo Agno")

# Obter a app FastAPI
app = agent_os.get_app()

def main():
    """
    Função principal que inicia o servidor
    """
    # Configurações do servidor
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"\n🚀 Iniciando servidor em {host}:{port}")
    print("📖 Documentação disponível em: http://localhost:8000/docs")

    # Iniciar o servidor usando AgentOS
    agent_os.serve(
        app="app:app",  # Referência para a app FastAPI
        host=host,
        port=port,
        reload=True  # Para desenvolvimento
    )

if __name__ == "__main__":
    main()
