#!/bin/bash
# CyberGhost OSINT - Emergency Diagnostics Script

GREEN="\e[32m"
RED="\e[31m"
YELLOW="\e[33m"
RESET="\e[0m"

EXIT_CODE=0

echo -e "${YELLOW}Iniciando varredura de problemas criticos residuais...${RESET}\n"

# 1. Detectar Código Legado
if [ -f "cyberghost-v1.sh" ] || [ -f "src/ui/web_dashboard.py" ] || [ -d "src/core" ]; then
    echo -e "${RED}[FALHA] Código legado altamente vulnerável (cyberghost-v1.sh ou src/ui/web_dashboard.py) ainda detectado no repositório.${RESET}"
    EXIT_CODE=1
else
    echo -e "${GREEN}[OK] Sistema legado não encontrado.${RESET}"
fi

# 2. Detectar Cypher Injection
if grep -q "MERGE (a)-\[r:{relationship_type}\]->(b)" "intel/knowledge_graph.py" 2>/dev/null; then
    if ! grep -q "ALLOWED_RELATIONSHIP_TYPES" "intel/knowledge_graph.py"; then
        echo -e "${RED}[FALHA] Cypher Injection detectada em intel/knowledge_graph.py (interpolação sem allowlist).${RESET}"
        EXIT_CODE=1
    else
        echo -e "${GREEN}[OK] Cypher Injection mitigada via Allowlist.${RESET}"
    fi
else
    echo -e "${GREEN}[OK] Cypher Injection pattern não encontrado ou já corrigido.${RESET}"
fi

# 3. Detectar Secrets Hardcoded
if grep -qE "(PRIVATE KEY|API_KEY=|password=)" "kubernetes/secrets.yaml" "cyberghost-v1.sh" 2>/dev/null; then
    echo -e "${RED}[FALHA] Secrets em texto claro encontrados no projeto.${RESET}"
    EXIT_CODE=1
else
    echo -e "${GREEN}[OK] Sem evidências claras de secrets hardcoded nos locais legados principais.${RESET}"
fi

echo -e "\n----------------------------------------"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}Verificação de emergência concluída com SUCESSO. Sistema pronto para deploy seguro.${RESET}"
else
    echo -e "${RED}Verificação falhou. Corrija os problemas críticos acima imediatamente!${RESET}"
fi

exit $EXIT_CODE
