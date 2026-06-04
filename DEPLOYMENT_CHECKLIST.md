# CyberGhost-OSINT - Deployment Checklist

## 1. Pré-requisitos de Infraestrutura
- [ ] Servidor Linux (Ubuntu 22.04 LTS recomendado)
- [ ] Docker Engine (v24.0+) e Docker Compose (v2.x) instalados
- [ ] No mínimo 16GB de RAM (Requisito Neo4j + Qdrant + Postgres)
- [ ] Firewall configurado (Liberar apenas portas 80/443, bloquear portas de BDs externos)
- [ ] Certificados TLS/SSL válidos (Let's Encrypt / Certbot)

## 2. Passos de Instalação (Ordem Exata)
1. **Clonagem e Setup de Diretórios**
   ```bash
   git clone <repo_url> /opt/cyberghost
   cd /opt/cyberghost
   mkdir -p logs data/postgres data/neo4j data/qdrant
   chmod -R 700 data/
   ```
2. **Configuração de Secrets**
   ```bash
   cp .env.example .env
   # Preencher senhas fortes e chaves reais de APIs de OSINT
   ```
3. **Build da Imagem Docker Base**
   ```bash
   docker-compose -f docker/docker-compose.enterprise.yml build
   ```
4. **Subida dos Serviços de Dados (DBs e Cache)**
   ```bash
   docker-compose -f docker/docker-compose.enterprise.yml up -d db redis neo4j qdrant
   # Aguarde 30 segundos para os serviços estabilizarem
   ```
5. **Execução de Migrations (Pendente)**
   ```bash
   docker-compose -f docker/docker-compose.enterprise.yml run --rm api alembic upgrade head
   ```
6. **Subida da Aplicação (API e Workers)**
   ```bash
   docker-compose -f docker/docker-compose.enterprise.yml up -d api celery_worker celery_beat
   ```

## 3. Verificações Pós-instalação
- [ ] `docker ps` mostra todos os containers como "Up" e sem restarts frequentes.
- [ ] Logs da API não apresentam erros de importação ou falhas de conexão de banco (`docker logs cyberghost_api`).
- [ ] Neo4j Browser acessível localmente e protegido por senha.

## 4. Testes de Validação
- [ ] **Login:** Autenticar via `/api/v1/auth/login` retorna HTTP 200 e Token JWT.
- [ ] **RBAC:** Tentar acessar resultados de outro usuário com conta não-admin retorna HTTP 403.
- [ ] **Scan:** Submeter um target via `/api/v1/scans` cria task no Celery e retorna HTTP 201.
- [ ] **Sync Data:** Resultados aparecem no PostgreSQL (tabela `scan_results`) e no Neo4j (nós `IOC`).

## 5. Security Hardening
- [ ] Executar scanner DAST (OWASP ZAP) contra a API em ambiente de homologação.
- [ ] Validar que nenhum container está rodando como usuário `root` (usar `USER appuser` nos Dockerfiles).
- [ ] Configurar proxy reverso (Nginx/Traefik) com rate limiting rígido e terminação SSL/TLS.
