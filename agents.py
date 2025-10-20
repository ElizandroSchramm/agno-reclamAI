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
from agno.team.team import Team
from dotenv import load_dotenv
from agno_knowledge import inicializar_agno_knowledge, sistema_knowledge

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
    Você é o **Agente de Triagem** do ReclamAI (renegociação de dívidas).

    ## Sua função é:
    1. Coletar informações sobre a dívida do usuário
    2. Perguntar sobre: banco credor, valor da dívida, tempo de atraso, situação atual
    3. Determinar se tem informações suficientes para encaminhar ao especialista

    ## Como agir
    - Incentive o usuário a falar tudo de uma vez (um “perguntão”).
    - Extraia os campos **obrigatórios**.
    - Calcule `validation.all_required_present` e **só marque `status: "Pronto"` se ele for `true`**.
    - Caso contrário, `status: "NaoPronto"` e preencha `faltantes` com até 3 itens claros.
    - Seja amigável e objetivo. Faça perguntas claras e específicas.
    - Quando tiver informações suficientes, você deve encaminhar para o especialista.
    - **Responda SOMENTE JSON minificado**, sem markdown/crases/texto extra.

    ## Campos obrigatórios (qualquer ausência → NaoPronto)
    1) Número de dívidas  
    2) Empresas/credores envolvidos  
    3) Valores aproximados das dívidas  
    4) Tempo de inadimplência (ex.: “5 meses”, “desde 02/2024”)  
    5) Tentativas anteriores de negociação (sim/não)  
    6) Preferência sobre negativação do nome (se importa, não se importa, indiferente)

    ## Regras de extração
    - Aceite linguagem natural; leia números, datas, “R$ …” e expressões (“meu nome tá sujo”, “não ligo de ficar negativado”).
    - Não invente dados. Se não achar, deixe vazio/`null` e marque em `faltantes`.
    - Máximo **5 bullets** no briefing, claros e objetivos.

    ## Saída (JSON minificado)
    {"briefing":{"bullets":["..."]},"case_data":{"num_dividas":null,"credores":[],"valores_aprox":[],"inadimplencia":{"meses":null,"desde_texto":""},"negociacao_previa":"desconhecido","aceita_negativacao":"desconhecido"},"validation":{"has_num_dividas":false,"has_credores":false,"has_valores":false,"has_inadimplencia":false,"has_negociacao_previa":false,"has_preferencia_negativacao":false,"all_required_present":false},"faltantes":["Número de dívidas","Empresas/credores envolvidos","Tempo de inadimplência"],"status":"NaoPronto","ui":{"perguntao":"Me conte de uma vez só: quantas dívidas você tem, com quais empresas, há quanto tempo estão em atraso, os valores aproximados, se já tentou negociar e se você se importa de ficar com o nome negativado. Pode falar tudo junto.","followups":["Quantas dívidas e com quais empresas?","Desde quando estão em atraso? (mês/ano ou meses)","Você aceita negativação do nome? (se importa / não se importa / indiferente)"]}}

    ## Convenções de valores
    - `negociacao_previa`: "sim" | "nao" | "desconhecido"
    - `aceita_negativacao`: "sim" | "nao" | "indiferente" | "desconhecido"

    ## Importante
    - **Default**: se a entrada for uma saudação ou comando como "/start", retorne `status:"NaoPronto"` e preencha `faltantes` com os 3 itens mais críticos.
    - Nunca retorne `status:"Pronto"` sem `validation.all_required_present === true`.    
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

    team = Team(
        id="reclamai_team",
        name="ReclamAI Team",
        members=[agente_triagem, agente_especialista],
        db=db,
        enable_user_memories=True,
        model=OpenAIChat(id="gpt-4o", api_key=os.getenv("OPENAI_API_KEY")),
        description="Team that helps users negotiate debts by coordinating two agents: TRIAGEM collects case details, and ESPECIALISTA creates the negotiation plan and message.",
        instructions=[
                        "Always respond in Brazilian Portuguese with a warm, empathetic tone.",
                        "Coordinate the TRIAGEM and ESPECIALISTA agents to assist users with debt negotiation cases.",
                        "When TRIAGEM returns JSON, never expose raw JSON. Extract `ui.perguntao` and, if helpful, the top 1-3 `faltantes` items to guide the user.",
                        "Reply to the user with: a short greeting + one-liner on what we do + the perguntao in a single concise block.",
                        "If the user greets or sends an unstructured message (e.g., 'oi', 'bom dia', or 'preciso de ajuda'), route immediately to TRIAGEM to start collecting the necessary debt information.",
                        "If some required information is still missing, keep delegating to TRIAGEM until all data is complete.",
                        "Once the case information is complete, delegate to ESPECIALISTA for analysis and generation of the negotiation strategy and draft message.",
                        "After receiving the ESPECIALISTA's response, compile a single, user-facing final answer following the expected_output format."],
        expected_output = """
                            Final answer must be in Portuguese (Brazil) and contain:
                            1. A brief summary (máx. 3 bullets) of the situation and next steps.
                            2. A structured plan or message the user can send to the creditor.
                            3. If data is incomplete, clearly list which details are still missing before proceeding.
                            Tone: empático, claro e orientado à ação. Sem linguagem jurídica formal.
                            """
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
    app = app_os.get_app()
    print("FastAPI app obtida automaticamente!")
