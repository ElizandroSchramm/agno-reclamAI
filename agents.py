"""
Sistema de Agentes para Renegociação de Dívidas
Versão Nativa com AgentOS

Este arquivo configura os agentes usando AgentOS do Agno
que automaticamente cria os endpoints FastAPI.
"""

from agno.agent import Agent
from agno.os import AgentOS
from agno.models.openai import OpenAIChat
import os
from dotenv import load_dotenv
from rag_system import inicializar_rag, obter_contexto_rag
from base_historico import inicializar_base_historico, base_historico

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar sistemas
inicializar_rag()
inicializar_base_historico()

def criar_agente_triagem():
    """
    Cria o agente de triagem usando a sintaxe nativa do Agno
    """
    instrucoes = """
    Você é um assistente especializado em triagem de casos de renegociação de dívidas.
    
    Sua função é:
    1. Coletar informações básicas sobre a dívida do usuário
    2. Perguntar sobre: banco credor, valor da dívida, tempo de atraso, situação atual
    3. Determinar se tem informações suficientes para encaminhar ao especialista
    
    Seja amigável e objetivo. Faça perguntas claras e específicas.
    Quando tiver informações suficientes, informe que vai encaminhar para o especialista.
    """
    
    agente = Agent(
        name="Triagem",
        instructions=instrucoes,
        model=OpenAIChat(id="gpt-4o", api_key=os.getenv("OPENAI_API_KEY")),
        add_history_to_context=True,
        num_history_runs=10,
        add_datetime_to_context=True,
        markdown=True,
    )
    
    return agente

def criar_agente_especialista():
    """
    Cria o agente especialista usando a sintaxe nativa do Agno
    """
    instrucoes = """
    Você é um especialista em renegociação de dívidas com acesso a uma base de conhecimento específica.
    
    Sua função é:
    1. Analisar as informações coletadas na triagem
    2. Buscar informações relevantes na base de conhecimento
    3. Fornecer orientações específicas sobre como proceder
    4. Sugerir estratégias de negociação com o banco
    5. Explicar os passos que o usuário deve seguir
    
    Seja detalhado e prático nas suas orientações.
    Sempre explique o "porquê" de cada recomendação.
    """
    
    agente = Agent(
        name="Especialista",
        instructions=instrucoes,
        model=OpenAIChat(id="gpt-4o", api_key=os.getenv("OPENAI_API_KEY")),
        add_history_to_context=True,
        num_history_runs=3,
        add_datetime_to_context=True,
        markdown=True,
    )
    
    return agente

def executar_especialista_com_rag(pergunta, session_id=None):
    """
    Executa o agente especialista com contexto RAG
    """
    # Obter contexto relevante
    contexto_rag = obter_contexto_rag(pergunta)
    
    # Preparar input com contexto
    input_com_contexto = f"{contexto_rag}{pergunta}"
    
    # Criar agente especialista
    agente_especialista = criar_agente_especialista()
    
    # Executar agente
    return agente_especialista.run(input=input_com_contexto, session_id=session_id)

def executar_agente_com_historico_e_rag(agente, pergunta, session_id=None):
    """
    Executa um agente com histórico e RAG integrados
    
    Args:
        agente: Instância do agente
        pergunta: Pergunta do usuário
        session_id: ID da sessão para histórico
        
    Returns:
        Resposta do agente
    """
    # Obter contexto do histórico
    contexto_historico = ""
    if session_id:
        contexto_historico = base_historico.obter_contexto_historico(
            session_id, agente.name, limite=5
        )
    
    # Obter contexto RAG (apenas para especialista)
    contexto_rag = ""
    if agente.name == "Especialista":
        contexto_rag = obter_contexto_rag(pergunta)
    
    # Preparar input com todos os contextos
    input_com_contexto = f"{contexto_historico}{contexto_rag}{pergunta}"
    
    # Executar agente
    resposta = agente.run(input=input_com_contexto, session_id=session_id)
    
    # Salvar no histórico
    if session_id:
        base_historico.adicionar_mensagem(session_id, agente.name, "user", pergunta)
        base_historico.adicionar_mensagem(session_id, agente.name, "assistant", resposta.content)
    
    return resposta

def criar_aplicacao_agno():
    """
    Cria a aplicação usando AgentOS - endpoints automáticos!
    """
    # Criar os agentes individuais
    agente_triagem = criar_agente_triagem()
    agente_especialista = criar_agente_especialista()
    
    # Criar AgentOS que automaticamente expõe os endpoints
    agent_os = AgentOS(
        description="Sistema de Renegociação de Dívidas",
        agents=[agente_triagem, agente_especialista],
    )
    
    return agent_os

if __name__ == "__main__":
    # Teste básico - criar a aplicação
    print("Criando aplicação Agno...")
    app_os = criar_aplicacao_agno()
    print("Aplicação criada com sucesso!")
    print(f"Agentes configurados: {[agent.name for agent in app_os.agents]}")
    
    # Obter a app FastAPI
    app = app_os.get_app()
    print("FastAPI app obtida automaticamente!")
