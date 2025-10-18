import os
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.chunking.fixed import FixedSizeChunking
from agno.knowledge.reader.text_reader import TextReader
from dotenv import load_dotenv

load_dotenv()

class SistemaKnowledgeAgnos:
    def __init__(self):
        self.nome_base = "FAQ Renegociação"
        self.knowledge = None
        self._criar_knowledge_base()
    
    def _criar_knowledge_base(self):
        vector_db = LanceDb(
            uri="./knowledge_db",
            table_name="faq_knowledge",
            embedder=OpenAIEmbedder(
                id="text-embedding-3-small",
                api_key=os.getenv("OPENAI_API_KEY")
            )
        )
        
        self.knowledge = Knowledge(
            name=self.nome_base,
            vector_db=vector_db,
            max_results=5  # Máximo de resultados por busca
        )
        
        print(f"✓ Knowledge base '{self.nome_base}' criada")
        print(f"✓ Vector DB: LanceDB em ./knowledge_db")
        print(f"✓ Embedder: OpenAI text-embedding-3-small")
    
    def adicionar_faq(self, arquivo_faq):
        if not os.path.exists(arquivo_faq):
            print(f"❌ Arquivo {arquivo_faq} não encontrado!")
            return False
        
        print(f"\n=== ADICIONANDO FAQ À BASE DE CONHECIMENTO ===")
        print(f"Arquivo: {arquivo_faq}")
        
        try:
            # Adicionar conteúdo com chunking fixo
            self.knowledge.add_content(
                path=arquivo_faq,
                reader=TextReader(
                    chunking_strategy=FixedSizeChunking(
                        chunk_size=1000,
                        overlap=100
                    )
                ),
                metadata={
                    "type": "faq",
                    "category": "renegociacao",
                    "source": "manual"
                }
            )
            
            print("✓ FAQ adicionado com sucesso!")
            print("✓ Chunking fixo aplicado")
            print("✓ Metadata configurada")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao adicionar FAQ: {e}")
            return False
    
    def verificar_status(self):
        """
        Verifica o status da base de conhecimento
        """
        print("\n=== STATUS DA BASE DE CONHECIMENTO ===")
        
        try:
            # Obter lista de conteúdo
            content_list, total_count = self.knowledge.get_content()
            
            print(f"✓ Total de conteúdos: {total_count}")
            
            for content in content_list:
                status, message = self.knowledge.get_content_status(content.id)
                print(f"  - {content.name}: {status}")
                if message:
                    print(f"    Mensagem: {message}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao verificar status: {e}")
            return False
    
    def buscar_conhecimento(self, pergunta, max_results=3):
        """
        Busca conhecimento relevante para uma pergunta
        
        Args:
            pergunta: Pergunta do usuário
            max_results: Número máximo de resultados
            
        Returns:
            Lista de resultados relevantes
        """
        try:
            # Buscar com filtros de metadata
            resultados = self.knowledge.search(
                query=pergunta,
                max_results=max_results,
                filters={"type": "faq", "category": "renegociacao"}
            )
            
            return resultados
            
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return []
    
    def obter_contexto_formatado(self, pergunta):
        """
        Obtém contexto formatado para o agente
        
        Args:
            pergunta: Pergunta do usuário
            
        Returns:
            Contexto formatado
        """
        resultados = self.buscar_conhecimento(pergunta)
        
        if not resultados:
            return ""
        
        contexto = "**Conhecimento relevante:**\n"
        for i, resultado in enumerate(resultados, 1):
            contexto += f"{i}. {resultado.content}\n\n"
        
        return contexto
    
    def validar_filtros(self):
        """
        Valida os filtros de metadata
        """
        print("\n=== VALIDANDO FILTROS ===")
        
        try:
            filtros_teste = {
                "type": "faq",
                "category": "renegociacao",
                "source": "manual"
            }
            
            valid_filters, invalid_keys = self.knowledge.validate_filters(filtros_teste)
            
            print(f"✓ Filtros válidos: {valid_filters}")
            if invalid_keys:
                print(f"❌ Chaves inválidas: {invalid_keys}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na validação: {e}")
            return False

# Instância global do sistema Knowledge
sistema_knowledge = SistemaKnowledgeAgnos()

def inicializar_agno_knowledge(arquivo_faq="base_conhecimento_faq_rag_otimizado.txt"):
    print("=== INICIALIZANDO AGNO KNOWLEDGE SYSTEM ===")
    
    # Adicionar FAQ    
    if sistema_knowledge.adicionar_faq(arquivo_faq):
        # Verificar status
        sistema_knowledge.verificar_status()
        
        # Validar filtros
        sistema_knowledge.validar_filtros()
        
        print("\n=== AGNO KNOWLEDGE SYSTEM INICIALIZADO ===")
        return True
    else:
        print("\n❌ Falha na inicialização do Agno Knowledge System")
        return False

def obter_contexto_knowledge(pergunta):
    return sistema_knowledge.obter_contexto_formatado(pergunta)

if __name__ == "__main__":
    # Teste do sistema Agno Knowledge
    print("=== TESTE DO AGNO KNOWLEDGE SYSTEM ===")
    
    # Inicializar
    sucesso = inicializar_agno_knowledge()
    
    if sucesso:
        # Teste de busca
        print("\n=== TESTE DE BUSCA ===")
        pergunta_teste = "Como negociar dívida de cartão de crédito?"
        
        print(f"Pergunta: {pergunta_teste}")
        
        contexto = obter_contexto_knowledge(pergunta_teste)
        
        if contexto:
            print("Contexto encontrado:")
            print("=" * 50)
            print(contexto)
            print("=" * 50)
        else:
            print("❌ Nenhum contexto encontrado")
        
        print("\n✅ Teste concluído com sucesso!")
    else:
        print("\n❌ Teste falhou")
