"""
Sistema RAG para Agentes de Renegociação de Dívidas

Este módulo implementa RAG usando FAISS para fornecer conhecimento
específico aos agentes sobre renegociação de dívidas.
"""

import faiss
import numpy as np
import json
import os
from sentence_transformers import SentenceTransformer
from typing import List, Dict

class SistemaRAG:
    """
    Sistema RAG simples usando FAISS para busca vetorial
    """
    
    def __init__(self, modelo_embedding="all-MiniLM-L6-v2"):
        """
        Inicializa o sistema RAG
        
        Args:
            modelo_embedding: Modelo para gerar embeddings
        """
        self.modelo = SentenceTransformer(modelo_embedding)
        self.indice = None
        self.chunks = []
        self.embeddings = None
        
    def carregar_documentos(self, arquivo_faq: str):
        """
        Carrega documentos do arquivo FAQ
        
        Args:
            arquivo_faq: Caminho para o arquivo FAQ
        """
        if not os.path.exists(arquivo_faq):
            print(f"Arquivo {arquivo_faq} não encontrado!")
            return
            
        with open(arquivo_faq, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            
        # Dividir em chunks por parágrafos
        self.chunks = [chunk.strip() for chunk in conteudo.split('\n\n') if chunk.strip()]
        print(f"Carregados {len(self.chunks)} chunks do FAQ")
        
    def criar_indice(self):
        """
        Cria o índice FAISS com os embeddings
        """
        if not self.chunks:
            print("Nenhum chunk carregado!")
            return
            
        # Gerar embeddings
        print("Gerando embeddings...")
        self.embeddings = self.modelo.encode(self.chunks)
        
        # Criar índice FAISS
        dimensao = self.embeddings.shape[1]
        self.indice = faiss.IndexFlatL2(dimensao)
        self.indice.add(self.embeddings.astype(np.float32))
        
        print(f"Índice criado com {self.indice.ntotal} vetores")
        
    def buscar_contexto(self, consulta: str, top_k: int = 3) -> List[str]:
        """
        Busca contexto relevante para uma consulta
        
        Args:
            consulta: Pergunta do usuário
            top_k: Número de chunks a retornar
            
        Returns:
            Lista de chunks relevantes
        """
        if self.indice is None:
            return []
            
        # Gerar embedding da consulta
        consulta_embedding = self.modelo.encode([consulta]).astype(np.float32)
        
        # Buscar chunks similares
        distancias, indices = self.indice.search(consulta_embedding, top_k)
        
        # Retornar chunks relevantes
        chunks_relevantes = [self.chunks[i] for i in indices[0]]
        return chunks_relevantes
        
    def salvar_indice(self, caminho_indice: str, caminho_chunks: str):
        """
        Salva o índice e chunks para uso futuro
        
        Args:
            caminho_indice: Caminho para salvar o índice FAISS
            caminho_chunks: Caminho para salvar os chunks
        """
        if self.indice is not None:
            faiss.write_index(self.indice, caminho_indice)
            with open(caminho_chunks, 'w', encoding='utf-8') as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=2)
            print(f"Índice salvo em {caminho_indice}")
            print(f"Chunks salvos em {caminho_chunks}")
            
    def carregar_indice(self, caminho_indice: str, caminho_chunks: str):
        """
        Carrega índice e chunks salvos
        
        Args:
            caminho_indice: Caminho do índice FAISS
            caminho_chunks: Caminho dos chunks
        """
        if os.path.exists(caminho_indice) and os.path.exists(caminho_chunks):
            self.indice = faiss.read_index(caminho_indice)
            with open(caminho_chunks, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            print(f"Índice carregado com {self.indice.ntotal} vetores")
            print(f"Chunks carregados: {len(self.chunks)}")
        else:
            print("Arquivos de índice não encontrados!")

# Instância global do sistema RAG
sistema_rag = SistemaRAG()

def inicializar_rag(arquivo_faq: str = "faq_renegociacao.txt"):
    """
    Inicializa o sistema RAG com o arquivo FAQ
    
    Args:
        arquivo_faq: Caminho para o arquivo FAQ
    """
    print("=== INICIALIZANDO SISTEMA RAG ===")
    
    # Tentar carregar índice existente primeiro
    if os.path.exists("indice_rag.faiss") and os.path.exists("chunks_rag.json"):
        print("Carregando índice existente...")
        sistema_rag.carregar_indice("indice_rag.faiss", "chunks_rag.json")
    else:
        print("Criando novo índice...")
        sistema_rag.carregar_documentos(arquivo_faq)
        sistema_rag.criar_indice()
        sistema_rag.salvar_indice("indice_rag.faiss", "chunks_rag.json")
    
    print("=== SISTEMA RAG INICIALIZADO ===")

def obter_contexto_rag(consulta: str) -> str:
    """
    Obtém contexto relevante para uma consulta
    
    Args:
        consulta: Pergunta do usuário
        
    Returns:
        Contexto relevante formatado
    """
    chunks_relevantes = sistema_rag.buscar_contexto(consulta, top_k=3)
    
    if chunks_relevantes:
        contexto = "\n\n".join(chunks_relevantes)
        return f"**Contexto relevante:**\n{contexto}\n\n"
    else:
        return ""

if __name__ == "__main__":
    # Teste do sistema RAG
    inicializar_rag()
    
    # Teste de busca
    consulta_teste = "Como negociar dívida com banco?"
    contexto = obter_contexto_rag(consulta_teste)
    print(f"Consulta: {consulta_teste}")
    print(f"Contexto encontrado: {contexto[:200]}...")
