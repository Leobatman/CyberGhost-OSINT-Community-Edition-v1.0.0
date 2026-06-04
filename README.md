<div align="center">
  <img src="https://via.placeholder.com/200x200.png?text=CyberGhost+OSINT" alt="CyberGhost Logo" width="200" />
  <h1>CyberGhost-OSINT</h1>
  <p><strong>Plataforma Híbrida de Cyber Threat Intelligence (CTI) e Automação OSINT</strong></p>

  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
  [![Neo4j](https://img.shields.io/badge/Neo4j-Graph_DB-008CC1.svg)](https://neo4j.com/)
  [![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
</div>

---

## Visão Geral

**CyberGhost-OSINT** é uma plataforma de Inteligência de Ameaças em estágio de evolução para arquitetura corporativa (Enterprise). O sistema centraliza fluxos de coleta OSINT assíncrona (via Celery), armazenando artefatos cibernéticos transacionalmente no PostgreSQL e correlacionando indicadores de ataque (IOCs) nativamente em um grafo no Neo4j.

O projeto deixou para trás sua origem como um script monolítico em bash (agora contido em `_legacy_deprecated/`) e adota uma arquitetura em microsserviços usando FastAPI e Next.js.

---

## Principais Recursos

### ✅ Recursos Implementados (Produção)
*   **Autenticação Segura:** Autenticação via JWT (`/api/v1/auth/login`) e RBAC rudimentar.
*   **Orquestração Assíncrona:** Fila Celery / Redis para tarefas longas (`backend/api/v1/scans.py` e `workers/tasks/`).
*   **Suporte Nativo STIX 2.1:** Criação e armazenamento de Indicadores e Relacionamentos no formato STIX via `backend/api/v1/stix.py`.
*   **Servidor TAXII 2.1:** Endpoints de Discovery e Coleção de Inteligência ativos (`/api/v1/taxii/`).
*   **Dashboard SPA:** Frontend Next.js com páginas de Login e Dashboard (`frontend/src/app/`).
*   **Observabilidade Básica:** Instrumentação do FastAPI via OpenTelemetry e Prometheus (`backend/main.py`).

### ⚠️ Recursos Experimentais (Beta)
*   **Deploy Kubernetes:** Arquivos YAML presentes (`kubernetes/hpa.yaml`, `ingress.yaml`), mas ainda carecem de Helm Charts finalizados e integração madura com KEDA.
*   **Knowledge Graph Sync:** As tarefas do Celery (`sync_tasks.py`) inserem nós no Neo4j, mas os endpoints de leitura gráfica rica para o Frontend ainda estão em desenvolvimento.

### 🚀 Roadmap Futuro
*   **Integração MISP:** Bidirecionalidade com instâncias MISP (Push/Pull).
*   **Graph Data Science (GDS):** Algoritmos nativos Neo4j (PageRank, Louvain) para detecção de Botnets.
*   **LangGraph Multi-Agent AI:** Orquestração de agentes LLM (`ReconAgent`, `IntelAgent`) para autonomia investigativa e geração de relatórios.
*   **HashiCorp Vault:** Migração do uso atual de `.env` para gestão de segredos dinâmica.

---

## Arquitetura

O fluxo atual reflete o estado do repositório:

```mermaid
graph TD
    A[Analista SOC] -->|HTTPS| B(Frontend Next.js)
    B -->|REST / JWT| C{FastAPI Backend}
    C -->|Leitura/Escrita| D[(PostgreSQL)]
    C -->|STIX 2.1 / TAXII| E(External Consumers)
    C -->|Enfileira Scan| F[Redis Broker]
    F -->|Consome| G[Celery Workers]
    G -->|Puxa OSINT| H(Recon / Go Wrappers)
    G -->|Sincroniza| I[(Neo4j Graph)]
```

---

## Estrutura do Projeto

```text
cyberghost-osint/
├── alembic/            # Migrações do banco (ex: 002_stix_support.py)
├── backend/            # API FastAPI (Auth, Scans, STIX, TAXII, Models, Schemas)
├── docker/             # Configurações Docker Compose (Neo4j, Redis, Prometheus)
├── frontend/           # Aplicação Next.js 15 com TailwindCSS
├── kubernetes/         # Arquivos Kubernetes (Deployment, Secrets, HPA)
├── recon/              # Scripts de OSINT (ASN Intel, Cert Transparency)
├── tests/              # Testes unitários (Auth, Config, STIX, TAXII)
├── workers/            # Trabalhadores Celery assíncronos
└── _legacy_deprecated/ # Antigo monolito Cyberghost v1 em Bash
```

---

## Tecnologias Utilizadas

| Componente | Tecnologia Atual | Status no Código |
| :--- | :--- | :--- |
| **Linguagem Core** | Python 3.11 | `backend/`, `workers/`, `tests/` |
| **Framework Web** | FastAPI | `backend/main.py` |
| **Mensageria** | Redis & Celery | `workers/celery_app.py` |
| **Banco Relacional** | PostgreSQL (Asyncpg) | `alembic/`, SQLAlchemy Models |
| **Banco de Grafos** | Neo4j | Conectores instanciados |
| **Frontend** | Next.js 15 (React) | `frontend/src/` |
| **Infraestrutura** | Docker Compose / K8s yaml | `docker-compose.enterprise.yml`, `kubernetes/` |

---

## Instalação Completa

### Docker Compose (Recomendado)

O repositório já possui a orquestração `enterprise` preparada.

```bash
# 1. Clonar
git clone https://github.com/Leobatman/Cyberghost-OSINT.git
cd Cyberghost-OSINT

# 2. Configurar variáveis (Crie o arquivo com as credenciais abaixo)
cp .env.example .env

# 3. Subir infraestrutura (Redis, Postgres, Neo4j, Backend)
docker compose -f docker/docker-compose.enterprise.yml up -d --build
```

### Ambiente de Desenvolvimento Local (Kali Linux / Ubuntu)

```bash
# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn backend.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## Configuração (`.env`)

Principais variáveis utilizadas nativamente pelo `backend/core/config.py`:

*   `DATABASE_URL`: URI de conexão com o PostgreSQL (ex: `postgresql+asyncpg://user:pass@localhost:5432/cyberghost`)
*   `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD`: Credenciais para o banco em Grafos.
*   `REDIS_URL`: Conexão do Celery e Rate Limiting (`redis://localhost:6379/0`).

---

## Como Utilizar (Exemplos Reais baseados no Código)

As chamadas abaixo refletem os *endpoints* de fato codificados na aplicação (ver `backend/api/v1/`).

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin_password"
```

### Criação de Indicador STIX 2.1 Nativo
```bash
curl -X POST "http://localhost:8000/api/v1/stix/indicators" \
     -H "Content-Type: application/json" \
     -d '{
           "name": "Malicious IP",
           "pattern": "[ipv4-addr:value = '\''198.51.100.1/32'\'']",
           "pattern_type": "stix"
         }'
```

### Consultar Discovery do Servidor TAXII
```bash
curl -X GET "http://localhost:8000/api/v1/taxii/taxii2/" \
     -H "Accept: application/taxii+json;version=2.1"
```

---

## Fluxo Operacional

1.  O **Frontend Next.js** chama `/api/v1/auth/login` e armazena o token.
2.  O usuário submete um domínio; o FastAPI delega a tarefa para a fila do Redis (`Celery`).
3.  O `Celery Worker` retira a tarefa e executa os módulos em `/recon` (Go wrappers / scripts Python).
4.  O resultado é tratado, salvo no PostgreSQL (transacionalmente) e um nó é inserido no Neo4j para correlação visual.

---

## Segurança

O repositório possui mecanismos defensivos fundamentais estabelecidos:
*   **JWT & Rate Limiting:** Middlewares nativos no FastAPI para evitar ataques de força bruta.
*   **Validação Estrita:** Pydantic models em todas as rotas de entrada (`backend/schemas/`).
*   **Cypher Injection Protected:** As instâncias de interação com Neo4j passaram por sanitização.

*(Obs: A adoção de HashiCorp Vault e isolamento gVisor para processos OSINT estão no Roadmap).*

---

## Observabilidade

*   **Prometheus / OpenTelemetry:** O arquivo `backend/main.py` contém as instrumentações `FastAPIInstrumentor` e `prometheus_fastapi_instrumentator`, expondo o endpoint `/metrics` nativamente.

---

## Testes e CI/CD

O repositório possui uma robusta esteira de testes locais (Pytest) e Actions GitHub (Pipeline DevSecOps).

**Rodando Testes Localmente:**
```bash
# Testes unitários com SQLite em memória
pytest tests/unit/

# Inclui validações essenciais de:
# - test_stix.py (Rotas STIX 2.1)
# - test_taxii.py (Servidor TAXII)
# - test_auth.py (JWT)
```

**CI/CD (GitHub Actions):** O arquivo `.github/workflows/ci.yml` contém etapas ativas para:
*   Linting (Ruff) e Type Checking (MyPy)
*   SAST (Bandit e Semgrep)
*   Testes Unitários (Pytest)

---

## Limitações Atuais (Transparência)

Para uma implementação de nível "Fortune 500", este projeto ainda **não possui**:
*   A integração com Agentes LangGraph (IA Autônoma) ainda não foi codificada no repositório.
*   O Frontend (Next.js) possui apenas páginas estruturais (Login/Dashboard); o React Force Graph dinâmico para leitura visual do Neo4j não está conectado à API.
*   Scanners complexos (Dark Web, Telegram, RaaS Leak sites) estão ausentes no framework atual.
*   A infraestrutura Kubernetes local em `kubernetes/` carece de Helm Charts definitivos; os arquivos YAML presentes são estáticos.

---

## Contribuição

Sinta-se à vontade para enviar PRs (Pull Requests)!
1. Crie uma branch baseada na `main` (`feature/sua-feature`).
2. Garanta que o código passa no `ruff check .` e no `pytest`.
3. Abra o PR descrevendo o problema resolvido.

---

## Licença

Este projeto é distribuído sob a Licença **MIT**. Veja o arquivo `LICENSE` para mais detalhes.
