#!/bin/bash
echo "========================================================================="
echo "💀 INICIANDO CYBERGHOST OSINT - ENTERPRISE MODE 💀"
echo "========================================================================="
echo ""

if ! command -v docker &> /dev/null
then
    echo "[ERRO] Docker nao encontrado. Por favor, instale o Docker primeiro."
    exit 1
fi

if [ ! -f .env ]; then
    echo "[*] Arquivo .env nao encontrado. Copiando de .env.example..."
    cp .env.example .env
fi

echo "[*] Levantando a infraestrutura completa do SOC..."
docker-compose -f docker/docker-compose.enterprise.yml up -d --build

echo ""
echo "[SUCESSO] CyberGhost OSINT Enterprise esta rodando em segundo plano!"
echo "- Dashboard Web: http://localhost:3000"
echo "- API Gateway: http://localhost:8000"
echo "- Celery Flower: http://localhost:5555"
echo "- Neo4j Graph DB: http://localhost:7474"
echo "========================================================================="
echo "Para ver os logs, rode: docker-compose -f docker/docker-compose.enterprise.yml logs -f"

