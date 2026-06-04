<div align="center">
    <h1>💀 CyberGhost-OSINT v14.0 💀<br><em>"ULTIMATE GOD MODE" EDITION</em></h1>
  <p><strong>A Plataforma Híbrida Definitiva de Cyber Threat Intelligence (CTI) e Automação OSINT Passiva</strong></p>

  <img src="https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExODYwbW52OWphdXI2c3J0MDR1OWJjc3pjMmFvN2V2YjdkemZvZHp5cCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/C4NdKtRaQE9m8/giphy.gif" width="10000" alt="Ghost Logo" style="filter: drop-shadow(0 0 1000px #ff0000);">

  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Aiohttp](https://img.shields.io/badge/Aiohttp-Async_Engine-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://docs.aiohttp.org/)
  [![Rich](https://img.shields.io/badge/Rich-Terminal_UI-magenta.svg?style=for-the-badge&logo=python&logoColor=white)](https://rich.readthedocs.io/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![Neo4j](https://img.shields.io/badge/Neo4j-Graph_DB-008CC1.svg?style=for-the-badge&logo=neo4j&logoColor=white)](https://neo4j.com/)
</div>

<p align="center">
  <em>CyberGhost não é um script. É uma arma cibernética. Um ecossistema massivo de reconhecimento focado em extrair a "alma" da infraestrutura do alvo em segundos sem disparar um único alarme.</em>
</p>

---

## 📖 Visão Geral e Arquitetura

O **CyberGhost-OSINT** opera com uma arquitetura híbrida de dois mundos:
1.  **CLI Tático (O Fantasma Autônomo):** Um script central assíncrono (`cyberghost.py`) construído em `asyncio` e `aiohttp`. Ele dispara dezenas de tarefas complexas contra o alvo paralelamente, processando portas, DNS, Segredos e Vulnerabilidades na velocidade da luz (um alvo como o Google é completamente varrido em ~30 segundos). Não depende de bancos de dados locais.
2.  **Enterprise SOC (O Cérebro Central):** Uma infraestrutura pesada baseada em Docker Compose, projetada para Data Centers. Ela pega o poder do CLI e escala isso utilizando o Celery (Workers de Background), RabbitMQ (Mensageria), FastAPI (Servidor Web Central) e o Neo4j (Banco de Dados em Grafo) para cruzar dados (CTI).

### ⚙️ Por debaixo do capô
Ao executar o motor, o loop do `asyncio.run(run_scan())` é acionado. Um único `ClientSession` compartilha as conexões TCP, mantendo-se aberto. As tarefas de I/O bloqueante (como resolução local de DNS via socket) usam `asyncio.to_thread()`, garantindo que o GIL do Python não trave a interface (escrita inteiramente em `rich.progress`).

---

## 🔥 ARSENAL DO "ULTIMATE GOD MODE" (v14.0)

A v14 traz uma postura **100% Passiva e Furtiva**. Ao rodar `--profile godmode`, o robô executa TODOS os seguintes submódulos massivos simultaneamente:

### 1. Infraestrutura Core & Perímetro
*   🌐 **DNS Engine & Zone Routing:** Captura IPv4, IPv6 e roteamento direto.
*   🛡️ **WAF Bypass & Fingerprinting:** Injeção minuciosa de payloads para identificar firewalls corporativos. Avisa imediatamente se a rota morre no Cloudflare, AWS WAF, Akamai ou Imperva.
*   ☁️ **Cloud Enum:** Verificação baseada em domínios para achar infraestrutura atrelada: `s3.amazonaws.com`, `storage.googleapis.com`, `blob.core.windows.net` e `nyc3.digitaloceanspaces.com`.
*   🔌 **Hyper Port Scanner:** Um socket timeout async checa 23 portas letais no lado do servidor: (21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9200, 27017).

### 2. Deep OSINT & Footprinting Furtivo
*   💥 **Subdomain Takeover Scanner:** Captura subdomínios via *Certificate Transparency* (`crt.sh`) e depois resolve seus ponteiros CNAME. Se um S3 Bucket ou Github Pages estiver apontando pro nada, emite um **Alerta Crítico** de Sequestro de Subdomínio.
*   🚀 **High-Speed Stealth Dirbusting:** Fuzzing assíncrono para diretórios que sempre sobram nas implantações (`/admin`, `/login`, `/api`, `/.env`, `/backup.zip`, `/config.php`, `/wp-admin`).
*   🕷️ **Deep JS Spidering & Secrets Harvester:** Abre o HTML do index, varre todas as tags `<script src="X">`, baixa todos os códigos Javascript do frontend do alvo e aplica Regex pesado procurando Tokens da AWS, Chaves do Google API, Tokens do Stripe e JWT vazados!
*   📜 **Wayback Machine Harvester:** Mapeamento do passado do domínio capturando dezenas de URLs arquivadas ao longo dos anos usando a Wayback API.

### 3. Threat Intel Passivo (Sem tocar no alvo)
*   📧 **Domain Email Harvester:** Extração direta via regex de contatos corporativos expostos (para spear-phishing passivo).
*   ⚠️ **IP Reputation & DNSBL:** Mapeia o IP reverso e joga nas listas de spam: `zen.spamhaus.org`, `b.barracudacentral.org`, `bl.spamcop.net`. Acusa na hora se o servidor virou zumbi de botnet.
*   🕵️ **OSINT Dork Generator (Breach Intel):** Gera strings automáticas (ex: `site:pastebin.com "alvo.com"`) prontas para analistas SOC colarem no Google caçando senhas em Plaintext e vazamentos em fóruns.
*   🧿 **Shodan Native Integration:** Ao identificar a variável de sistema `$env:SHODAN_API_KEY`, ele fará uma requisição oficial para a base global do Shodan puxando CVEs (Common Vulnerabilities and Exposures) conhecidos sem tocar no roteador alvo.

### 4. Postura de Segurança (Defense Evasion Analytics)
*   🛡️ **DNS Security Posture & Spoofing:** Varre o TXT DNS. Se faltar `SPF` (`v=spf1`) ou `DMARC`, o sistema alerta que o domínio é suscetível a forja de emails da diretoria.
*   🚨 **Security Headers Analyzer:** Lê as respostas HTTP originais em busca de lacunas defensivas (Falta de `Strict-Transport-Security`, `Content-Security-Policy` e `X-Frame-Options`), validando vulnerabilidades contra Clickjacking.
*   💻 **Tech Detect & CVE Mapper:** Lê Headers customizados (X-Powered-By). Se detectar Apache desatualizado ou versões inseguras (ex: `PHP/5`), emite um alerta deduzindo a vulnerabilidade imediatamente na interface.
*   🤖 **Robots.txt & Sitemap Mapper:** Ao invés de forçar diretórios massivamente, lê silenciosamente caminhos que o administrador "escondeu" do Google no `robots.txt` (`Disallow:`).

---

## 🎛️ CLI: Manual Oficial de Flags e Argumentos

O script `cyberghost.py` aceita uma ampla gama de parâmetros:

```text
Uso: python cyberghost.py [alvo] [opções]

Argumentos Posicionais:
  target                O domínio ou IP alvo a ser dissecado (ex: google.com)

Opções de Perfis de Profundidade:
  --profile {quick, standard, full, mostruoso, godmode}
    quick:       Apenas DNS e tecnologias. (Segundos)
    standard:    Adiciona Scanners de Porta e Enum de Nuvem.
    full:        Adiciona Reputação de IP e Coleta ASN.
    mostruoso:   Adiciona Regex de Segredos no JS e Scan de Misconfigurations.
    godmode:     O arsenal v14 massivo e passivo completo. (Padrão)

Opções de Saída e Ferramentas:
  --export-html         No fim da execução, salva os dados estruturados em um arquivo HTML atraente.
  --plugin NOME         Procura por `plugin_NOME.py` em `~/.cyberghost/plugins/` e anexa ao scan.

Opções Visuais e Temas (powered by Rich):
  --logo {matrix, cyber, red, rainbow, minimal, none, dark, blood, ghost, premium, premium-dark}
    Define o tema da arte ASCII e cores da interface. (O padrão é "matrix").
  --animate             Renderiza a logo sendo desenhada letre por letra no terminal!
  --glow                Aplica uma sombra profunda em texto premium. (Use com logos premium/dark).
  --blood-drip          (Apenas modo dark/blood) Pingos de sangue caem do terminal durante a invocação.
```

### Exemplos de Uso Extremo:

**O Hacker Moderno (Premium UI com Exportação):**
```bash
python cyberghost.py uol.com.br --profile godmode --export-html --logo premium --glow --animate
```

**Modo Furtivo Total (Sem UI visual, limpo e direto):**
```bash
python cyberghost.py example.com --profile godmode --logo minimal
```

**Sessão da Madrugada (Terror Dark com efeito de sangue):**
```bash
python cyberghost.py fbi.gov --profile godmode --logo blood --blood-drip --animate
```

---

## 💻 Instalação & Setup (Ambiente Local - CLI)

**Pré-requisitos:** Python 3.10 ou superior no Windows/Linux/macOS.

1.  **Clone e acesse:**
    ```bash
    git clone https://github.com/Leobatman/Cyberghost-OSINT.git
    cd Cyberghost-OSINT
    ```
2.  **Instale os pacotes poderosos:**
    ```bash
    pip install aiohttp rich beautifulsoup4 colorama requests shodan censys dnspython ipwhois
    ```
    *(Nota de arquitetura: O código força o loop de eventos para `WindowsSelectorEventLoopPolicy` no Windows, garantindo que não ocorra um crash do asyncio).*

3.  **Habilite a API Shodan (Altamente Recomendado):**
    Para receber alertas massivos de CVE de IPs.
    ```powershell
    # Windows
    $env:SHODAN_API_KEY="SUA_CHAVE_SHODAN"
    
    # Linux/MacOS
    export SHODAN_API_KEY="SUA_CHAVE_SHODAN"
    ```

---

## 🔌 Sistema Mestre de Plugins (Write-your-own)

Não quer mexer no coração do `cyberghost.py`? O sistema da V14 aceita a injeção assíncrona de plugins na pasta oculta do usuário (o sistema cria essa pasta automaticamente no primeiro uso).

**Local do Arquivo:** No Windows `C:\Users\SEU_USUARIO\.cyberghost\plugins\plugin_custom.py` (Linux: `~/.cyberghost/plugins/plugin_custom.py`).

**Como criar um plugin:**
Basta criar o arquivo `plugin_meuteste.py` com uma função global `run(target)` assíncrona.
```python
# plugin_meuteste.py
async def run(target):
    return f"Plugin secreto executado com sucesso no alvo: {target}!"
```

Rode passando `--plugin meuteste` e a interface criará uma nova caixa renderizada com seus dados!

---

## 🏗️ O MODO ENTERPRISE (Operações de SOC e Threat Hunting Contínuo)

Além do front end letal no CLI, o diretório `/backend` (Arquitetura reservada no repositório) gerencia um monolito de CTI projetado para processar milhares de domínios.

### Componentes de Rede:
*   **API Gateway (FastAPI):** Lida com os logins JWT das equipes do Red Team e recebe requisições JSON.
*   **Job Broker (RabbitMQ / Redis):** Mantém a fila de trabalhos de OSINT não-bloqueantes.
*   **Celery Workers:** Recebem os jobs da fila e engatilham os mesmos processos do `cyberghost.py` de forma paralela no Data Center.
*   **Knowledge Graph (Neo4j):** Salva relatórios vinculando "Domínio A -> Resolve para -> IP B -> Hospedado em -> AWS". Perfeito para caçar APTs e campanhas contínuas de phishing.

### Implantando Enterprise (Docker Compose):
Copie o ambiente:
```bash
cp .env.example .env
```
Lance o cluster:
```bash
docker compose -f docker/docker-compose.enterprise.yml up -d --build
```
> O Dashboard (Next.js) subirá na porta **3000** e o core API subirá na porta **8000**.

---

## 🗺️ Roadmap de Evolução (V15+)

*   [ ] Integração completa e automatizada nativa com LLM local (Ollama) para a IA do Cyberghost processar as falhas descobertas e descrever relatórios detalhados de invasão e mitigação.
*   [ ] Crawler passivo massivo do LinkedIn para pegar perfis exatos da empresa.
*   [ ] Suporte de execução massiva no CLI lendo de um arquivo `.txt` (Scan de 1000 hosts por vez).

---

## 🤝 Contribuições

Contribuições são sempre bem-vindas e esperadas da comunidade Hacker. Sinta-se livre para clonar, realizar um fork, melhorar os módulos assíncronos no core do código ou lançar novos visuais para o Rich Console. Use `ruff` para linting!

---

## 📜 Licença e Termos Legais (Disclaimer)

O projeto encontra-se inteiramente sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes de distribuição e modificação.

> ⚠️ **Aviso de Responsabilidade Extrema:** A V14 "Ultimate God Mode" do CyberGhost-OSINT foi construída **apenas** e **estritamente** para uso por profissionais de Inteligência de Ameaças, Pesquisadores Acadêmicos, Analistas SOC, Bug Hunters e equipes de Defesa e Red Teaming operando debaixo de autorização. Embora os pacotes da V14 sejam baseados em OSINT passivo e não destrutivo, o mapeamento acelerado de vulnerabilidades pode ser classificado como varredura maliciosa por provedores de nuvem (AWS/GCP/Cloudflare). O autor e os contribuidores **negam qualquer responsabilidade** pelo uso dessa ferramenta para extração de dados sensíveis ou varredura de infraestruturas de terceiros sem permissão prévia por escrito com o intuito de aplicar danos. Você é a única pessoa responsável por suas ações na rede cibernética. Use com sabedoria e responsabilidade.
