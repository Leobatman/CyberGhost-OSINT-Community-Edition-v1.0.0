<div align="center">
  <img src="https://via.placeholder.com/200x200.png?text=CyberGhost+OSINT" alt="CyberGhost Logo" width="200" />
  <h1>CyberGhost-OSINT</h1>
  <p><strong>Plataforma Híbrida de Cyber Threat Intelligence (CTI) e Automação OSINT para Ambientes Corporativos</strong></p>

  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![Neo4j](https://img.shields.io/badge/Neo4j-Graph_DB-008CC1.svg?style=for-the-badge&logo=neo4j&logoColor=white)](https://neo4j.com/)
  [![Next.js](https://img.shields.io/badge/Next.js-15-black.svg?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
  [![Celery](https://img.shields.io/badge/Celery-Async-37814A.svg?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-DB-4169E1.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
  [![Docker](https://img.shields.io/badge/Docker-Containers-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
</div>

---

## 📖 Visão Geral

**CyberGhost-OSINT** é uma plataforma de Inteligência de Ameaças (CTI) projetada para orquestrar coletas de Inteligência de Fontes Abertas (OSINT) em larga escala. Centralizando a coleta assíncrona, a plataforma transforma dados de reconhecimento (como ASN, Transparência de Certificados) em artefatos rastreáveis e os correlaciona em um **Knowledge Graph**, permitindo que equipes de SOC descubram relações não-triviais entre vetores de ataque.

Anteriormente concebido como um simples utilitário monolítico de script Bash (agora em `_legacy_deprecated/`), o CyberGhost-OSINT evoluiu para uma arquitetura baseada em **microsserviços** orientada a eventos, com suporte nativo ao ecossistema STIX/TAXII.

---

## ⚡ Principais Recursos

### ✅ Produção (Implementado)
* **API Centralizada e Segura (FastAPI):** JWT Auth, CORS, Proteção HSTS, Rate Limiting baseado em IP (via Redis), tudo sob a arquitetura de microsserviços.
* **Coleta OSINT Assíncrona:** Gerenciada através do Celery e Redis, escalável para longos mapeamentos de infraestrutura ofensiva.
* **Módulos Nativos de Reconhecimento:** Inclui inteligência BGP/ASN (`recon/asn_intel.py`) e Certificate Transparency (`recon/cert_transparency.py`).
* **Ecossistema CTI (STIX & TAXII 2.1):** Endpoints nativos para geração de Indicadores STIX 2.1 e um Servidor de Descoberta/Coleção TAXII ativo (`/api/v1/taxii/`).
* **Frontend Interativo (Next.js 15):** Autenticação em SPA, Dashboard moderno para relatórios e gestão.
* **Observabilidade:** Monitoramento via Prometheus e OpenTelemetry nativamente acoplados (expostos via endpoint `/metrics`).
* **Orquestração Docker (Enterprise):** Arquitetura pronta com banco de dados em grafos (Neo4j) e relacional (PostgreSQL + Asyncpg).

### ⚠️ Beta (Em Validação)
* **Kubernetes Deploy:** Arquivos essenciais como HPA (`hpa.yaml`) e Ingress (`ingress.yaml`) presentes, prontos para a transição para Helm Charts maduros.
* **Knowledge Graph Syncing:** Nós e correlações populados dinamicamente no Neo4j com base nos resultados das tasks do Celery. A UI gráfica avançada do Frontend ainda se encontra em desenvolvimento.

### 🚀 Roadmap Futuro
* **Multi-Agent AI (LangGraph):** Orquestração de Agentes Inteligentes (ReconAgent e IntelAgent) para conduzir investigações e gerar relatórios complexos com LLMs.
* **Graph Data Science (GDS):** Algoritmos automáticos no Neo4j (ex: PageRank, Louvain) aplicados à infraestrutura de atacantes para detecção de botnets e C2.
* **Gestão Dinâmica de Segredos:** Implementação do HashiCorp Vault.
* **Integração MISP:** Comunicação Bidirecional (Push/Pull) com MISP, consolidando a plataforma como um hub robusto de CTI.

---

## 🏗️ Arquitetura

```mermaid
graph TD
    A[Analista SOC / Usuário] -->|HTTPS (Next.js)| B(Frontend React SPA)
    B -->|REST / JWT| C{API Gateway / FastAPI}
    C -->|Transações ACID| D[(PostgreSQL)]
    C -->|Feed STIX 2.1 / TAXII| E(External Consumers & MISP)
    C -->|Agendamento de Task| F[Redis Message Broker]
    F -->|Consome a fila| G[Celery Workers]
    G -->|Executa Módulos| H(Reconhecimento Ativo/Passivo)
    H -->|Coleta de Dados| I[ASN Intel, Cert Transparency, etc]
    G -->|Correlação e Grafos| J[(Neo4j Knowledge Graph)]
```

### Estrutura de Diretórios
```text
cyberghost-osint/
├── alembic/            # Gerenciamento de Migrações do banco (ex: stix_support)
├── backend/            # API Core FastAPI (Auth, Scans, STIX, TAXII, Models)
├── docker/             # Ambientes e containers (Neo4j, Redis, Prometheus)
├── frontend/           # Interface Next.js 15 focada em Experiência do Usuário (UX)
├── kubernetes/         # Definições Manifestos YAML para orquestração (Deploy, HPA)
├── recon/              # Scripts Especializados de OSINT (asn_intel.py, cert_transparency.py)
├── tests/              # BDD/TDD: Testes unitários focados na qualidade de código
├── workers/            # Processamento em Background Assíncrono via Celery
└── _legacy_deprecated/ # Antigo monolito V1 em Bash (para consultas históricas)
```

---

## 💻 Instalação & Setup

### Opção 1: Infraestrutura Corporativa Completa (Docker Compose) - Recomendado

A forma mais rápida de subir todo o ecossistema (PostgreSQL, Neo4j, Redis, Backend, Frontend e Workers).

```bash
# 1. Clonar o repositório
git clone https://github.com/Leobatman/Cyberghost-OSINT.git
cd Cyberghost-OSINT

# 2. Configuração de Variáveis (Ajuste o `.env` conforme necessário)
cp .env.example .env

# 3. Subir e Orquestrar
docker compose -f docker/docker-compose.enterprise.yml up -d --build
```
> Após o processo, a API estará acessível via `http://localhost:8000`, e o frontend em `http://localhost:3000`.

### Opção 2: Ambiente de Desenvolvimento Local (Linux/WSL)

Ideal para engenheiros testando partes separadas ou desenvolvendo novas ferramentas de Recon.

**A. Subindo o Backend & Worker**
```bash
# Criar Ambiente Virtual e instalar dependências
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Aplicar Migrations (Necessário PostgreSQL rodando)
alembic upgrade head

# Iniciar Servidor da API FastAPI
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Em outro terminal, iniciar o Celery Worker
celery -A workers.celery_app worker --loglevel=info
```

**B. Subindo o Frontend**
```bash
cd frontend
npm install
npm run dev
```

---

## 🛠️ Configuração Básica (`.env`)

As configurações da aplicação são orquestradas via `backend/core/config.py`. As chaves críticas no `.env` incluem:

* `DATABASE_URL`: String de conexão (ex: `postgresql+asyncpg://user:pass@localhost:5432/cyberghost`).
* `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD`: Chaves de acesso do banco de grafos Neo4j.
* `REDIS_URL`: Broker de mensagens (`redis://localhost:6379/0`).
* `SECRET_KEY`: String robusta para assinatura JWT (gere uma com `openssl rand -hex 32`).

---

## 💡 Como Utilizar (Exemplos de API)

### 1. Autenticação (Login)
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=your_secure_password"
```

### 2. Disparar uma Coleta OSINT
*(Nota: As tarefas requerem Autenticação Bearer gerada no passo 1)*
```bash
curl -X POST "http://localhost:8000/api/v1/scans/start" \
     -H "Authorization: Bearer <SEU_TOKEN_JWT>" \
     -H "Content-Type: application/json" \
     -d '{
           "target": "example.com",
           "scan_type": "full_recon"
         }'
```

### 3. Integração com Ecossistema CTI (Criar Indicador STIX 2.1)
```bash
curl -X POST "http://localhost:8000/api/v1/stix/indicators" \
     -H "Content-Type: application/json" \
     -d '{
           "name": "C2 Server Detectado",
           "pattern": "[ipv4-addr:value = '\''198.51.100.4/32'\'']",
           "pattern_type": "stix",
           "valid_from": "2024-01-01T00:00:00Z"
         }'
```

---

## 🛡️ Defesas e Segurança Nativas

* **Rate Limiting Distribuído:** Camada de middleware em FastAPI suportada por Redis limitando abuso por IP.
* **Autenticação e Sessão:** Transações restritas via Tokens JWT robustos; RBAC em consolidação.
* **Proteção Cibernética no Código:** Cypher Injections validados em Neo4j, e Modelos Estritos via `Pydantic` que impedem mass assignment ou payload parsing abusivo.
* **Sanitização de Headers Web:** HSTS, XSS Protection, e prevenção de Host-Header Injections ativados por default via `TrustedHostMiddleware`.

---

## 📊 Observabilidade e Métricas

Totalmente instrumentada para a suíte *Cloud Native*.
* O endpoint `/metrics` serve um formato amigável para **Prometheus** extraído pelas bibliotecas do FastAPI e OpenTelemetry.
* **Health Checks Dinâmicos:** `/api/health` para visualização profunda do estado de conexões (ex: DB Status) e `/api/ready` exclusivo para orquestrações Kubernetes (Probes).

---

## 🧪 CI/CD e Garantia de Qualidade

Este projeto emprega um modelo rigoroso DevSecOps com testes unificados no GitHub Actions (`.github/workflows/ci.yml`).

* **Execução dos Testes Locais:**
  ```bash
  # Testes isolados de banco relacional e lógicas
  pytest tests/unit/
  
  # Cobertura abrangente nas lógicas CTI (Auth, TAXII, STIX)
  ```
* **Linting / Security / Type Checking:** 
  Validação estrita rodando via `Ruff`, verificação estática de tipos no `MyPy` e auditoria de SAST via ferramentas como `Bandit` e `Semgrep`.

---

## 🤝 Contribuições e Políticas

Contribuições para o projeto são amplamente encorajadas! O repositório segue regras rigorosas, portanto:

1. Dê um **Fork** no projeto e crie sua Branch: `git checkout -b feature/SuaInovacao`
2. Escreva o código (Assegure testes para novos recursos, preferencialmente `TDD`).
3. Formate e inspecione os Padrões:
   ```bash
   ruff check . --fix
   pytest
   ```
4. Submeta seu **Pull Request** descrevendo os benefícios da sua alteração.
5. Siga o nosso [Código de Conduta](CODE_OF_CONDUCT.md) e [Políticas de Contribuição](CONTRIBUTING.md).

---

## 📜 Licença e Termos Legais

O código é distribuído sob a Licença **MIT** - você tem liberdade para usar, alterar e distribuir sob o seu próprio risco. Veja o arquivo [LICENSE](LICENSE) para maiores detalhes jurídicos.

> ⚠️ **Aviso de Responsabilidade:** Esta plataforma e suas ferramentas de Reconhecimento foram criadas estritamente para **Inteligência de Ameaças, Pesquisa Acadêmica e Avaliações de Defesa**. O uso malicioso para ataques contra infraestruturas não autorizadas é estritamente proibido. Os desenvolvedores e mantenedores não se responsabilizam por danos resultantes da manipulação indevida ou irresponsável deste software.
