# Sistema de Renegociação de Dívidas com Agno Knowledge

Sistema inteligente para ajudar usuários com renegociação de dívidas usando agentes de IA com **Agno Knowledge nativo** integrado.

## 🚀 Início Rápido

### 1. Configuração do Ambiente

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configuração do OpenAI

```bash
# Copiar arquivo de exemplo
cp .env_example .env

# Editar .env e adicionar sua chave OpenAI
OPENAI_API_KEY=sua_chave_aqui
```

### 3. Iniciar Servidor

```bash
# Iniciar servidor
python app.py
```
