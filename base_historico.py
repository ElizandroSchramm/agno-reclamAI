"""
Sistema de Base de Dados para Histórico de Conversas

Este módulo implementa uma base SQLite simples para armazenar
o histórico das conversas dos agentes.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class BaseHistorico:
    """
    Classe para gerenciar histórico de conversas em SQLite
    """
    
    def __init__(self, caminho_db: str = "historico_conversas.db"):
        """
        Inicializa a base de dados
        
        Args:
            caminho_db: Caminho para o arquivo SQLite
        """
        self.caminho_db = caminho_db
        self.criar_tabelas()
    
    def criar_tabelas(self):
        """
        Cria as tabelas necessárias
        """
        conn = sqlite3.connect(self.caminho_db)
        cursor = conn.cursor()
        
        # Tabela de sessões
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                agente_nome TEXT NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de mensagens
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mensagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                agente_nome TEXT NOT NULL,
                tipo TEXT NOT NULL, -- 'user' ou 'assistant'
                conteudo TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessoes (session_id)
            )
        ''')
        
        # Índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON mensagens(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agente ON mensagens(agente_nome)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON mensagens(timestamp)')
        
        conn.commit()
        conn.close()
    
    def adicionar_mensagem(self, session_id: str, agente_nome: str, tipo: str, conteudo: str):
        """
        Adiciona uma mensagem ao histórico
        
        Args:
            session_id: ID da sessão
            agente_nome: Nome do agente
            tipo: 'user' ou 'assistant'
            conteudo: Conteúdo da mensagem
        """
        conn = sqlite3.connect(self.caminho_db)
        cursor = conn.cursor()
        
        # Criar sessão se não existir
        cursor.execute('''
            INSERT OR IGNORE INTO sessoes (session_id, agente_nome)
            VALUES (?, ?)
        ''', (session_id, agente_nome))
        
        # Adicionar mensagem
        cursor.execute('''
            INSERT INTO mensagens (session_id, agente_nome, tipo, conteudo)
            VALUES (?, ?, ?, ?)
        ''', (session_id, agente_nome, tipo, conteudo))
        
        # Atualizar timestamp da sessão
        cursor.execute('''
            UPDATE sessoes 
            SET data_ultima_atualizacao = CURRENT_TIMESTAMP
            WHERE session_id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
    
    def obter_historico(self, session_id: str, agente_nome: str, limite: int = 10) -> List[Dict]:
        """
        Obtém o histórico de uma sessão
        
        Args:
            session_id: ID da sessão
            agente_nome: Nome do agente
            limite: Número máximo de mensagens a retornar
            
        Returns:
            Lista de mensagens ordenadas por timestamp
        """
        conn = sqlite3.connect(self.caminho_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT tipo, conteudo, timestamp
            FROM mensagens
            WHERE session_id = ? AND agente_nome = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (session_id, agente_nome, limite))
        
        mensagens = []
        for row in cursor.fetchall():
            mensagens.append({
                'tipo': row[0],
                'conteudo': row[1],
                'timestamp': row[2]
            })
        
        conn.close()
        return list(reversed(mensagens))  # Ordem cronológica
    
    def obter_contexto_historico(self, session_id: str, agente_nome: str, limite: int = 5) -> str:
        """
        Obtém o contexto do histórico formatado para o agente
        
        Args:
            session_id: ID da sessão
            agente_nome: Nome do agente
            limite: Número máximo de mensagens a incluir
            
        Returns:
            Contexto formatado
        """
        historico = self.obter_historico(session_id, agente_nome, limite)
        
        if not historico:
            return ""
        
        contexto = "**Histórico da conversa:**\n"
        for msg in historico:
            if msg['tipo'] == 'user':
                contexto += f"👤 Usuário: {msg['conteudo']}\n"
            else:
                contexto += f"🤖 {agente_nome}: {msg['conteudo']}\n"
        
        contexto += "\n"
        return contexto
    
    def limpar_historico(self, session_id: str = None):
        """
        Limpa o histórico (tudo ou de uma sessão específica)
        
        Args:
            session_id: Se fornecido, limpa apenas essa sessão
        """
        conn = sqlite3.connect(self.caminho_db)
        cursor = conn.cursor()
        
        if session_id:
            cursor.execute('DELETE FROM mensagens WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM sessoes WHERE session_id = ?', (session_id,))
        else:
            cursor.execute('DELETE FROM mensagens')
            cursor.execute('DELETE FROM sessoes')
        
        conn.commit()
        conn.close()
    
    def obter_estatisticas(self) -> Dict:
        """
        Obtém estatísticas da base de dados
        
        Returns:
            Dicionário com estatísticas
        """
        conn = sqlite3.connect(self.caminho_db)
        cursor = conn.cursor()
        
        # Total de sessões
        cursor.execute('SELECT COUNT(*) FROM sessoes')
        total_sessoes = cursor.fetchone()[0]
        
        # Total de mensagens
        cursor.execute('SELECT COUNT(*) FROM mensagens')
        total_mensagens = cursor.fetchone()[0]
        
        # Mensagens por agente
        cursor.execute('''
            SELECT agente_nome, COUNT(*) 
            FROM mensagens 
            GROUP BY agente_nome
        ''')
        mensagens_por_agente = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_sessoes': total_sessoes,
            'total_mensagens': total_mensagens,
            'mensagens_por_agente': mensagens_por_agente
        }

# Instância global da base de dados
base_historico = BaseHistorico()

def inicializar_base_historico():
    """
    Inicializa a base de dados de histórico
    """
    print("=== INICIALIZANDO BASE DE HISTÓRICO ===")
    print(f"✓ Base SQLite criada: {base_historico.caminho_db}")
    
    # Mostrar estatísticas
    stats = base_historico.obter_estatisticas()
    print(f"✓ Sessões existentes: {stats['total_sessoes']}")
    print(f"✓ Mensagens existentes: {stats['total_mensagens']}")
    print("=== BASE DE HISTÓRICO INICIALIZADA ===")

if __name__ == "__main__":
    # Teste da base de dados
    inicializar_base_historico()
    
    # Teste de adicionar mensagens
    print("\n--- TESTE DE ADIÇÃO DE MENSAGENS ---")
    base_historico.adicionar_mensagem("teste_123", "Triagem", "user", "Olá, preciso de ajuda")
    base_historico.adicionar_mensagem("teste_123", "Triagem", "assistant", "Olá! Como posso ajudar?")
    
    # Teste de obter histórico
    print("\n--- TESTE DE HISTÓRICO ---")
    historico = base_historico.obter_historico("teste_123", "Triagem")
    for msg in historico:
        print(f"{msg['tipo']}: {msg['conteudo']}")
    
    # Teste de contexto
    print("\n--- TESTE DE CONTEXTO ---")
    contexto = base_historico.obter_contexto_historico("teste_123", "Triagem")
    print(contexto)
    
    # Estatísticas finais
    print("\n--- ESTATÍSTICAS FINAIS ---")
    stats = base_historico.obter_estatisticas()
    print(f"Total de sessões: {stats['total_sessoes']}")
    print(f"Total de mensagens: {stats['total_mensagens']}")
    print(f"Mensagens por agente: {stats['mensagens_por_agente']}")
