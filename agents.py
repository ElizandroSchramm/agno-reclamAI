"""
Sistema de Agentes para Renegociação de Dívidas
Versão Nativa com AgentOS

Este arquivo configura os agentes usando AgentOS do Agno
que automaticamente cria os endpoints FastAPI.
"""

from agno.agent import Agent
from agno.os import AgentOS
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb
import os
from agno.guardrails import PromptInjectionGuardrail, OpenAIModerationGuardrail
from agno.team.team import Team
from dotenv import load_dotenv
from agno_knowledge import inicializar_agno_knowledge, sistema_knowledge
from guardrails.spam_length import SpamAndLengthGuardrail
from guardrails.toxicity_hf import ToxicityHFGuardrail

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar sistemas
inicializar_agno_knowledge()
# inicializar_base_historico()

# Configurar banco de dados SQLite para memória e histórico
db = SqliteDb(db_file="agno_memory.db")

def criar_agente_triagem():
    """
    Cria o agente de triagem usando a sintaxe nativa do Agno
    """
    instrucoes = """
    ## Papel
    Você é o **Agente de Triagem** do ReclamAI, responsável por coletar informações sobre dívidas do usuário.

    ## Objetivo
    Construir e atualizar um registro único do caso do usuário, combinando o histórico da conversa (memória do time) com as novas mensagens recebidas.

    ## Instruções de fluxo
    1. Sempre leia as informações já conhecidas na memória da sessão antes de responder.
    2. Atualize apenas os campos que o usuário completou nesta nova mensagem.
    3. **Nunca reinicie** o processo ou repita perguntas que já foram respondidas corretamente.
    4. Se ainda houver campos faltantes, pergunte **somente** os que continuam vazios.
    5. Quando todos os campos obrigatórios estiverem preenchidos, retorne `status:"Pronto"` e o briefing completo para o especialista.

    ## Campos obrigatórios
    1) Número de dívidas  
    2) Empresas/credores envolvidos  
    3) Valores aproximados das dívidas  
    4) Tempo de inadimplência  
    5) Tentativas anteriores de negociação (sim/não)  
    6) Preferência sobre negativação do nome

    ## Como agir
    - Incentive o usuário a contar tudo de uma vez, mas se vier parcial, mantenha o progresso.
    - Use linguagem natural e empática, mas responda sempre em **JSON minificado** (sem markdown).
    - **Fusão de dados:** combine o que o usuário acabou de dizer com o que já está salvo na memória (`case_data` existente).  
    Exemplo: se `credores` já contém `["Nubank"]`, não sobrescreva com vazio.
    - Se a mensagem atual não traz novos dados, apenas repita a pergunta dos `faltantes`.

    ## Saída (JSON minificado)
    {"briefing":{"bullets":["..."]},
    "case_data":{"num_dividas":null,"credores":[],"valores_aprox":[],"inadimplencia":{"meses":null,"desde_texto":""},"negociacao_previa":"desconhecido","aceita_negativacao":"desconhecido"},
    "validation":{"has_num_dividas":false,"has_credores":false,"has_valores":false,"has_inadimplencia":false,"has_negociacao_previa":false,"has_preferencia_negativacao":false,"all_required_present":false},
    "faltantes":["..."],
    "status":"NaoPronto",
    "ui":{"perguntao":"...","followups":["..."]}}

    ## Convenções
    - `negociacao_previa`: "sim" | "nao" | "desconhecido"
    - `aceita_negativacao`: "sim" | "nao" | "indiferente" | "desconhecido"

    ## Importante
    - Use a memória para lembrar o que o usuário já disse nesta sessão.
    - Pergunte só o que falta.
    - Nunca apague dados válidos já coletados.
    """
    
    
    agente = Agent(
        name="Triagem",
        instructions=instrucoes,
        db=db,  # 🎯 Banco de dados 
        add_history_to_context=True,
        num_history_runs=10,
        enable_user_memories=True,  # 🎯 Memória automática habilitada
        add_datetime_to_context=True,
        markdown=True,
    )
    
    return agente

def criar_agente_especialista():
    instrucoes = """
    ## Papel
    Você é um especialista em renegociação de dívidas com acesso a uma base de conhecimento específica.

    ## Objetivo
    Atuar como **especialista em renegociação de dívidas**, usando o briefing estruturado pelo Agente de Triagem.
    Sua missão é:
    - Consultar a base RAG para entender como o consumidor pode atuar para renegociação**.  
    - Identificar quais direitos e estratégias cabem ao perfil do usuário.  
    - Gerar um **playbook personalizado** em 4 seções.  

    ---

    ## Estrutura de Saída Esperada
    ### 1. Resumo do Caso
    - [bullet 1]  
    - [bullet 2]  
    - [bullet 3]  

    ### 2. Rotas de Ação
    - Contato direto com credor.  
    - Feirões ou canais oficiais (Consumidor.gov.br, Procon).  
    - Avaliar descontos x parcelamento.  
    - Impacto no score/nome limpo.  

    ### 3. Mensagem Padrão
    Prezados(as),

    Venho solicitar formalmente a renegociação da dívida referente a [tipo de contrato/dívida] junto à [nome da empresa].  
    Meu objetivo é regularizar a situação de forma justa e viável, por isso peço:  

    - Apresentação detalhada do saldo devedor atualizado (valor principal, juros, encargos e multas).  
    - Proposta de desconto para quitação ou plano de parcelamento acessível.  
    - Registro do acordo de forma clara e documentada.  

    Estou aberto(a) a dialogar e espero uma resposta em até 10 dias.  

    ### 4. Próximos Passos
    - Enviar a mensagem ao canal oficial da empresa (SAC/app).
    - Guardar comprovante do envio.
    - Caso não haja resposta em até 10 dias úteis → registrar em **Consumidor.gov.br**.
    - Se mesmo assim não resolver → procurar **Procon local**.

    ---

    ## Guardrails
    - Não dar aconselhamento jurídico → apenas informações públicas.  
    - Linguagem simples, sem juridiquês.  
    - Sempre recomendar guardar documentos e registros.  

    
    Sua função é:
    1. Analisar as informações coletadas na triagem
    2. Buscar informações relevantes na base de conhecimento automaticamente
    3. Fornecer orientações específicas sobre como proceder
    4. Sugerir estratégias de negociação com o banco
    5. Explicar os passos que o usuário deve seguir
    
    IMPORTANTE: Você tem acesso automático à base de conhecimento sobre renegociação de dívidas.
    O sistema irá automaticamente buscar informações relevantes para suas respostas.
    
    Seja detalhado e prático nas suas orientações.
    Sempre explique o "porquê" de cada recomendação.
    """
    
    agente = Agent(
        name="Especialista",
        instructions=instrucoes,
        db=db,  # 🎯 Banco de dados para memória e histórico
        knowledge=sistema_knowledge.knowledge,  # 🎯 Agno Knowledge nativo!
        search_knowledge=True,  # 🎯 Busca automática!
        knowledge_filters={"type": "faq", "category": "renegociacao"},  # 🎯 Filtros!
        add_history_to_context=True,
        num_history_runs=10,  # 🎯 Últimas 10 interações
        add_datetime_to_context=True,
        enable_user_memories=True,  # 🎯 Memória automática habilitada
        markdown=False,
    )
    
    return agente

def criar_aplicacao_agno():
    """
    Cria a aplicação usando AgentOS - endpoints automáticos!
    """
    # Criar os agentes individuais
    agente_triagem = criar_agente_triagem()
    agente_especialista = criar_agente_especialista()

    team_instructions = [
        # Linguagem e tom
        "Always respond in Brazilian Portuguese with an empathetic, concise tone.",
        
        # Objetivo do líder
        "Coordinate TRIAGEM and ESPECIALISTA to help users negotiate debts. Maintain a single up-to-date case snapshot across the session.",
        
        # Memória & Estado
        "Before delegating, read the session memory/history and extract any debt details already provided by the user.",
        "Update a CASE_SNAPSHOT object (in memory/state) by merging new info with what is already known. Never discard valid fields.",
        
        # Campos do snapshot
        "CASE_SNAPSHOT must include (when known): num_dividas, credores[], valores_aprox[], tipo(s) de dívida, inadimplencia (meses e/ou desde_texto), negociacao_previa, aceita_negativacao, observacoes.",
        
        # Roteamento
        "On greeting or unstructured input, delegate to TRIAGEM to start/continue collection.",
        "If required fields are still missing, delegate to TRIAGEM and ask ONLY for the missing fields.",
        "Once all required fields are present, delegate to ESPECIALISTA for analysis and negotiation draft.",
        
        # Delegação com contexto (IMPORTANTE)
        "When delegating to TRIAGEM, pass along a structured payload with the current CASE_SNAPSHOT and a computed MISSING_FIELDS list.",
        "The TRIAGEM must continue from the CASE_SNAPSHOT, not restart. Ask only about MISSING_FIELDS.",

        # Proteção contra mudança de tópico
        "If the user asks about something unrelated to debt negotiation, politely inform them that you are specialized in debt negotiation and ask them to focus on the topic.",
        "If the user tries to change the topic, politely inform them that you are specialized in debt negotiation and ask them to focus on the topic.",
        "If the user tries to joke or make a joke, politely inform them that you are specialized in debt negotiation and ask them to focus on the topic.",
        
        # Formato do payload de delegação
        "Delegation payload format for TRIAGEM:",
        "{",
        "  \"member_id\": \"TRIAGEM\",",
        "  \"task_description\": \"Continuar coleta de dados de dívida com base no snapshot.\",",
        "  \"input\": {",
        "    \"case_snapshot\": { /* campos já conhecidos, ex.: credores, valores, tempo */ },",
        "    \"missing_fields\": [ /* itens faltantes */ ]",
        "  },",
        "  \"expected_output\": \"JSON minificado com briefing, case_data atualizado, faltantes e status\"",
        "}",
        
        # Compilação de resposta ao usuário
        "Never expose raw JSON to the user. If still collecting, reply with a short greeting + one-liner + a single concise question that covers only the missing fields.",
        "After ESPECIALISTA responds, compile one final answer following expected_output."
        ]

    team_expected_output = """
        Coleta (incompleto):
        - Saudação curta (1 linha)
        - Uma frase dizendo que vamos ajudar na negociação de dívidas
        - Uma pergunta única que peça SOMENTE os campos faltantes (sem reiniciar)

        Final (completo):
        1) 3 bullets (situação, direitos potenciais em alto nível, caminho recomendado)
        2) Passos numerados (canal, prazo, evidências)
        3) Mensagem pronta para copiar/colar ao credor
        """
    
    team = Team(
        id="reclamai_team",
        name="ReclamAI Team",
        members=[agente_triagem, agente_especialista],
        model=OpenAIChat(id="gpt-4o", api_key=os.getenv("OPENAI_API_KEY")),
        pre_hooks=[PromptInjectionGuardrail(), OpenAIModerationGuardrail(), ToxicityHFGuardrail(), SpamAndLengthGuardrail()],
        db=db,
        enable_user_memories=True,
        add_history_to_context=True,
        num_history_runs=10,
        add_datetime_to_context=True,
        description="Team that helps users negotiate debts by coordinating two agents: TRIAGEM collects case details, and ESPECIALISTA creates the negotiation plan and message.",
        instructions=team_instructions,
        expected_output = team_expected_output
    )
    
    # Criar AgentOS que automaticamente expõe os endpoints
    agent_os = AgentOS(
        description="Sistema de Renegociação de Dívidas",
        teams=[team]
    )
    
    return agent_os

if __name__ == "__main__":
    # Teste básico - criar a aplicação
    print("Criando aplicação Agno...")
    app_os = criar_aplicacao_agno()
    print("Aplicação criada com sucesso!")
    
    # Obter a app FastAPI
    # app = app_os.get_app()
