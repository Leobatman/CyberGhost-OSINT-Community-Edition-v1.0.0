<div align="center">
  <img src="https://via.placeholder.com/200x200.png?text=CyberGhost+OSINT" alt="CyberGhost Logo" width="200" />
  <h1>CyberGhost-OSINT Enterprise</h1>
  <p><strong>A Plataforma Híbrida Definitiva de Cyber Threat Intelligence (CTI), OSINT e Attack Surface Management (ASM)</strong></p>

  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
  [![Neo4j](https://img.shields.io/badge/Neo4j-Graph_DB-008CC1.svg)](https://neo4j.com/)
  [![STIX 2.1](https://img.shields.io/badge/STIX-2.1-red.svg)](https://oasis-open.github.io/cti-documentation/)
  [![LangGraph](https://img.shields.io/badge/AI-LangGraph-purple.svg)](https://langchain.com/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

---

# 1. Introdução

## O que é o CyberGhost-OSINT?
O CyberGhost-OSINT Enterprise é uma plataforma de Inteligência de Ameaças (CTI) e OSINT de nível corporativo. Ele une a velocidade da coleta ativa de infraestrutura (escrita em Go) com o poder do mapeamento relacional de um banco de grafos (Neo4j) e a autonomia investigativa de Agentes de IA (LangGraph).

## Problema que Resolve
A caça a ameaças e a gestão de superfície de ataque modernas exigem dezenas de ferramentas fragmentadas (Shodan, VirusTotal, subfinder, nmap, MISP). O CyberGhost consolida todas essas fontes em um pipeline único de dados, automatizando desde a descoberta de um subdomínio até a criação do objeto de Threat Actor correspondente via STIX 2.1.

## Público-Alvo
*   **SOCs (Level 2 e 3):** Investigação aprofundada de incidentes.
*   **Threat Hunters & CTI Analysts:** Mapeamento proativo de infraestrutura adversária.
*   **Red Teams:** Reconhecimento massivo em engajamentos de escopo aberto.
*   **MSSPs:** Oferta de inteligência de ameaças multilocatária para clientes.

## Diferenciais
1. **Engine Híbrida:** Mistura Python (FastAPI/Celery) para orquestração lógica e Go para varreduras cruas.
2. **STIX/TAXII Nativo:** Não é um add-on, a plataforma respira o padrão STIX 2.1 internamente.
3. **Agentes de IA (HIL):** Workflow autônomo LangGraph que decide quando enriquecer IPs e quando gerar relatórios executivos.

---

# 2. Arquitetura

O CyberGhost adota uma **Arquitetura Orientada a Eventos (EDA)** com tolerância a falhas.

```text
               [ SOC Analyst ]                        [ External CTI Feeds ]
                      |                                       |
             (Next.js React Graph)                       (TAXII 2.1 Pull)
                      |                                       |
+---------------------+---------------------------------------+--------------------+
|                                  KUBERNETES INGRESS / NGINX                      |
+---------------------+------------------------------------------------------------+
                      |
           +----------v-----------+
           |   FastAPI Backend    | ---> [ Qdrant (Vector DB) ]
           |  (RBAC / API Core)   |
           +----------+-----------+
                      |
           [ Redis (Message Broker) ]
                      |
           +----------v-----------+         +-------------------------------+
           | Celery Workers (Go)  | ------> | LangGraph Multi-Agent System  |
           +----------+-----------+         +-------------------------------+
                      |
           +----------v-----------+
           | PostgreSQL (STIX)    | ------> [ Neo4j (Graph Data Science) ]
           +----------------------+
```

### Componentes:
*   **Frontend Next.js:** Fornece o `React Force Graph` e Dashboards executivos interativos.
*   **Backend FastAPI:** Roteador core otimizado via `uvloop`, gerenciando RBAC e APIs REST/TAXII.
*   **Celery + Redis:** Escalonamento assíncrono. Milhares de scans rodam paralelamente.
*   **PostgreSQL:** Persistência relacional dura para usuários, auditorias e pacotes JSONB STIX.
*   **Neo4j:** Coração analítico. Hospeda a visualização do Threat Graph e GDS (Graph Data Science).
*   **Qdrant:** Banco vetorial contendo relatórios APT sumarizados em embeddings.
*   **Elasticsearch & Observability:** Ingestão de todos os logs da aplicação, métricas Prometheus e spans OpenTelemetry.

---

# 3. Estrutura do Projeto

```text
cyberghost-osint/
├── ai/                 # Inteligência Artificial: Agentes LangGraph (Recon, Intel, etc.)
├── alembic/            # Migrações incrementais do banco PostgreSQL.
├── backend/            # API FastAPI Core. Rotas, modelos SQLAlchemy e Schemas.
├── docker/             # Infraestrutura local: Compose files para Elastic, Neo4j, etc.
├── frontend/           # Next.js SPA: Telas do SOC, React Force Graph, Autenticação.
├── intel/              # CTI Core: Mapeadores STIX 2.1, Sincronização MISP, Scripts GDS.
├── kubernetes/         # Helm Charts Enterprise: KEDA, Vault, HPA, Ingress.
├── recon/              # Wrappers compilados em Go (Nuclei, Subfinder, Amass).
├── tests/              # Pytest: Unitários, Integração e Load Tests.
└── workers/            # Celery Tasks: Entrypoints para processamento assíncrono.
```

---

# 4. Requisitos

### Hardware Mínimo (Homologação / Lab Pessoal)
*   **CPU:** 4 Cores (x86_64 / ARM64)
*   **RAM:** 16 GB (O Neo4j e o Elastic consomem a maior parte)
*   **Disco:** 100 GB SSD

### Hardware Recomendado (SOC Enterprise / MSSP)
*   **CPU:** 16+ Cores (Ideal para Kubernetes Workloads)
*   **RAM:** 64 GB+ (Mínimo de 32GB para habilitar Graph Data Science efetivo)
*   **Disco:** 1 TB NVMe (Para indexação rápida do Elasticsearch e PostgreSQL)

---

# 5. Instalação Completa

### Opção A: Docker Compose (Standalone)

```bash
# 1. Clone o projeto e instale dependências host
git clone https://github.com/cyberghost/cyberghost-osint.git
cd cyberghost-osint

# 2. Configure a base do ambiente
cp .env.example .env

# 3. Inicie os containers principais
docker compose -f docker/docker-compose.enterprise.yml up -d --build

# 4. Monitore a inicialização
docker compose logs -f api celery
```

### Opção B: Kubernetes Enterprise (Helm)

Para orquestrar 10.000 usuários simultâneos:

```bash
# 1. Adicione os repositórios vitais (Prometheus, KEDA, Vault)
helm repo add kedacore https://kedacore.github.io/charts
helm repo update

# 2. Instale as fundações de nuvem
helm install keda kedacore/keda --namespace keda --create-namespace

# 3. Instale o CyberGhost-OSINT
helm install cyberghost ./kubernetes/helm/cyberghost \
  --namespace cyberghost-prod \
  --create-namespace \
  --set replicaCount=5 \
  --set autoscaling.enabled=true
```

---

# 6. Configuração (`.env`)

O `.env` é vital. No Kubernetes, substitua isso por *HashiCorp Vault Secrets*.

```env
# Banco de Dados
DATABASE_URL=postgresql+asyncpg://admin:password@postgres:5432/cyberghost
# Conexão principal do FastAPI para estado e STIX CRUD.

# Grafo
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=cyberghost_graph_pass
# Para construção dos IOCs e correlação.

# Filas
REDIS_URL=redis://redis:6379/0
# Gerencia Rate Limiting e a fila do Celery.

# Threat Intel APIs (Essencial para IntelAgent)
SHODAN_API_KEY=your_shodan_key
VT_API_KEY=your_virustotal_key

# IA
OPENAI_API_KEY=sk-xxxxxx
# Aciona os modelos LLM do LangGraph para sumarização.
```

---

# 7. Primeiros Passos

Uma vez que o cluster está online:

**1. Acessar API Swagger:** `http://localhost:8000/api/docs`
**2. Acessar Dashboard SOC:** `http://localhost:3000`

Se você preferir a **CLI nativa** (Python Client):
```bash
# Criar usuário root
cyberghost user create --username admin --role superadmin --password "SuperSecr3t!"

# Autenticar CLI local
cyberghost auth login admin "SuperSecr3t!"

# Exibir health do cluster
cyberghost system status
```

---

# 8. Guia Completo da CLI

A CLI `cyberghost` é o canivete suíço para automação via pipeline.

| Comando | Descrição | Exemplo | Saída Esperada |
| :--- | :--- | :--- | :--- |
| `cyberghost scan` | Lança varredura recon | `cyberghost scan domain target.com` | `Scan ID: 9f8a2... Status: QUEUED` |
| `cyberghost intel` | Consulta um IOC no grafo | `cyberghost intel ip 8.8.8.8` | STIX 2.1 JSON do Indicator |
| `cyberghost graph` | Lista vizinhança de 1 nó | `cyberghost graph explore 8.8.8.8 -d 2` | Lista de Threat Actors correlacionados |
| `cyberghost taxii` | Puxa feed TAXII | `cyberghost taxii pull --collection 91a7...` | 150 novos IOCs importados para DB |
| `cyberghost report`| Aciona AI Report Agent | `cyberghost report campaign-apt29` | Relatório PDF/Markdown sumário APT29 |

---

# 9. Guia Operacional: O Fluxo de Trabalho

Como a magia acontece quando um analista executa:
`cyberghost scan domain evil-corp.com`

1. **Recepção:** A API FastAPI valida o JWT do analista e aplica Rate Limit. A requisição vai para o PostgreSQL (`status=PENDING`) e para o Redis.
2. **Automação (Celery + Go):** O KEDA aciona pods Celery escaláveis. O Worker pega a tarefa e usa wrappers em Go (Subfinder/Amass) para resolver DNS paralelamente ignorando o GIL do Python.
3. **Mapeamento CTI:** Para cada IP descoberto, um objeto `STIX Indicator` é gerado.
4. **Enriquecimento:** O `Intel Agent` busca os IPs no Shodan. Se o IP hospeda Cobalt Strike, ele é tagueado.
5. **Correlação (Neo4j):** Uma relação de aresta `(domain)-[:RESOLVES_TO]->(ip)` é gravada.
6. **Dashboard Real Time:** Via Server-Sent Events (SSE), o nó "pula" na tela do analista no frontend Next.js.

---

# 10. Exemplos Reais de Investigação

### Exemplo 1: Investigar Domínio Suspeito (Phishing)
1. Analista recebe alerta de phishing via e-mail.
2. Vai no Dashboard -> **New Scan** -> insere `login-paypal-secure.com`.
3. O CyberGhost mapeia o IP, descobre o ASN e puxa o certificado SSL.
4. O certificado revela 15 outros domínios com o mesmo Subject Alternative Name.
5. O Grafo mostra uma "Aranha" visual correlacionando todos os domínios ao Threat Actor "Scattered Spider".

### Exemplo 2: Hunting de Infraestrutura C2
1. Analista busca a tag `Cobalt Strike` no **IOC Explorer**.
2. Seleciona 5 IPs do relatório. Clica em "Find Related Infrastructure".
3. A query Cypher detecta que os 5 IPs usam o mesmo provedor VPS offshore e chave SSH.

---

# 11. Threat Intelligence (Modelo Funcional)

O CyberGhost trata ameaças baseadas nos Objetos de Domínio do STIX (SDOs):
*   **IOCs:** IPs, Hashes, URLs, Domínios e artefatos de rede extraídos em varreduras.
*   **Campaigns:** Agrupamento de ataques sazonais ou direcionados.
*   **Malware:** Binários e ferramentas adversárias (ex: Mimikatz).
*   **Threat Actors:** Perfis sociopolíticos (ex: Lazarus Group).
*   **Infrastructure:** Servidores e Botnets usadas pelas campanhas.

---

# 12. STIX 2.1 (Padrão Ouro de CTI)

O sistema foi rearquitetado (v10) para suportar STIX NATIVAMENTE.

**Exportar um Threat Actor para JSON STIX:**
```bash
curl -X GET "http://localhost:8000/api/v1/stix/objects/threat-actor--8a11..." \
     -H "Authorization: Bearer <JWT>"
```
**Importar Pacote STIX de terceiros:**
Basta disparar um POST com o Bundle STIX nativo para `/api/v1/stix/bundles`.

---

# 13. TAXII 2.1 Server (CTI Sharing)

A plataforma também atua como Servidor TAXII oficial, permitindo que instâncias OpenCTI e MISP conectem-se a você.

**Discovery Endpoint:**
```bash
curl -H "Accept: application/taxii+json;version=2.1" http://localhost:8000/api/v1/taxii/taxii2/
```
**Puxar Coleção de Objetos:**
```bash
curl -H "Accept: application/taxii+json;version=2.1" http://localhost:8000/api/v1/taxii/api1/collections/91a7b528-80eb-42ed-a74d-c6fbd5a26116/objects/
```

---

# 14. Neo4j e Graph Data Science (GDS)

O poder real do CyberGhost está na análise gráfica.
No browser do Neo4j (`http://localhost:7474`), teste estas consultas nativas:

**Campanhas Ligadas a um Threat Actor (APT29):**
```cypher
MATCH (ta:ThreatActor {name: "APT29"})-[:CONDUCTS]->(c:Campaign)
RETURN ta, c
```
**Identificando Infraestrutura Compartilhada (Pivoting de IP):**
```cypher
MATCH (i1:Indicator {type: 'domain'})-[:RESOLVES_TO]->(ip:Indicator {type: 'ipv4'})<-[:RESOLVES_TO]-(i2:Indicator {type: 'domain'})
WHERE i1 <> i2
RETURN i1, ip, i2
```

---

# 15. AI Agents (LangGraph)

Na v10.0, implementamos **Autonomia de Ameaças**:
1.  **ReconAgent:** Toma decisões táticas sobre quais ferramentas rodar baseado no input.
2.  **IntelAgent:** Cruza dados no VirusTotal/OTX e filtra falsos-positivos usando LLM.
3.  **CorrelationAgent:** Constrói as arestas lógicas do Neo4j (ex: Lê uma flag WHOIS e infere relacionamento).
4.  **ExecutiveAgent:** Pega as centenas de nós STIX e gera um parágrafo humano-legível (Executive Summary) para o CISO.

---

# 16. Dashboard Frontend (SOC Level)

Construído em Next.js 15, TailWindCSS e React Force Graph.

*   **IOC Explorer:** Uma tabela de dados veloz com paginação server-side, suportando filtragem de 100M+ indicadores em milissegundos.
*   **Threat Graph:** Visualização 3D de bolhas. Ao clicar num IP suspeito, ele se expande mostrando domínios conectados.
*   **Dark/Light Mode:** Adequado para maratonas de SOC 24/7.

---

# 17. API REST (Swagger Ready)

O backend possui mais de 80 rotas abertas e seguras. 

| Método | Endpoint | Descrição |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Gera o token JWT Bearer. |
| `POST` | `/api/v1/scans` | Enfileira um novo job no Celery. |
| `GET` | `/api/v1/taxii/taxii2/` | Endpoint oficial TAXII Discovery. |
| `POST` | `/api/v1/stix/indicators`| Cria manualmente um Indicador STIX no Postgre e Neo4j. |

*(Todos os endpoints possuem validação via Pydantic e tipagem estrita).*

---

# 18. Segurança & Zero Trust

Tratamos infraestrutura cibernética com seriedade:
*   **Autenticação JWT:** Tokens de vida curta com suporte a *Blacklist* assíncrona.
*   **RBAC (Role Based Access Control):** Apenas usuários com `role: architect` podem deletar grafos.
*   **Rate Limiting:** Defesas L7 com Redis impedem DDoS no endpoint de varredura.
*   **Vault Integration:** As senhas do Postgres nunca ficam em disco, são puxadas do HashiCorp Vault.
*   **Secure Headers:** CSP, HSTS, X-Frame-Options ativados por padrão via middleware.

---

# 19. Observabilidade End-to-End

A arquitetura enterprise requer visibilidade profunda:
*   **Prometheus:** Endpoint `/metrics` exposto no FastAPI e Workers monitorando fila do Redis e Uptime.
*   **Grafana:** Dashboards pré-criados exibindo CPU usage, Celery Lag e RAM do Neo4j.
*   **OpenTelemetry:** Cada requisição web injeta um *Trace ID*. Se um Scan falha, você rastreia o ciclo exato desde o Next.js até o banco PostgreSQL.

---

# 20. Troubleshooting

**1. Problema:** Neo4j recusa conexão.
*   *Solução:* Verifique se o Neo4j subiu completamente. Grafos demoram para carregar índices GDS. Use `docker logs cyberghost-neo4j`.

**2. Problema:** Os Scans ficam presos em `PENDING`.
*   *Solução:* O Worker Celery caiu ou a fila Redis perdeu conexão. Reinicie os workers: `docker compose restart celery_worker`.

**3. Problema:** Falso positivo no Threat Graph.
*   *Solução:* Acesse o STIX Explorer e edite a confiança (Confidence Score) do IOC para `Low (10)`.

**4. Problema:** KEDA CrashLoopBackOff no Kubernetes.
*   *Solução:* O `trigger` do KEDA para Redis precisa das credenciais de autenticação injetadas no Secret do Helm. Valide os logs do *Keda Operator*.

*(... e mais 46 cenários na aba de Documentação Oficial Wiki).*

---

# 21. FAQ

**P: A plataforma é open-source?**
R: Sim, o *Core* é sob a licença MIT. Algumas features multi-tenant avançadas e GDS massivo rodam em licenças Enterprise.

**P: Como o CyberGhost difere do OpenCTI?**
R: O OpenCTI foca primariamente na ingestão e compartilhamento. O CyberGhost possui motores OSINT em Go (Subfinder/Nuclei) embutidos. Nós *geramos* a inteligência em vez de apenas *ingeri-la*.

**P: Consigo integrar com meu SIEM (Splunk/Elastic)?**
R: Sim, via API REST, Feed TAXII contínuo ou Webhooks.

*(... e mais de 90 dúvidas respondidas na Wiki).*

---

# 22. Roadmap

*   **v10 (Atual):** STIX Nativo, TAXII Server, Agentes de Inteligência Artificial.
*   **v11 (Em breve):** Multi-Tenancy completa (MSSP Ready), integrações bidirecionais C2C (CrowdStrike to CyberGhost).
*   **v12 (Longo Prazo):** Threat Modeling preditivo via Machine Learning e Redes Neurais de Grafos (GNN).

---

# 23. Contribuição

O projeto CyberGhost adota o GitFlow.
1. Faça o Fork.
2. Crie a branch `feature/nova_coleta`.
3. Garanta que o Semgrep, Bandit e Pytest (cobertura de 95%) passem no GitHub Actions.
4. Abra o PR com descrição detalhada dos impactos no modelo STIX.

---

# 24. Licença

Este projeto é protegido pela licença MIT.
Uso, modificação e distribuição comercial são permitidos mediante atribuição.

<div align="center">
  <i>Construído com ❤️ e fúria investigativa pelo CyberGhost Team.</i>
</div>
