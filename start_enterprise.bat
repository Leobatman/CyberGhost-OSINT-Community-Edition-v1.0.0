@echo off
echo =========================================================================
echo 💀 INICIANDO CYBERGHOST OSINT - ENTERPRISE MODE 💀
echo =========================================================================
echo.

where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] Docker nao encontrado. Por favor, instale o Docker Desktop primeiro.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [*] Arquivo .env nao encontrado. Copiando de .env.example...
    copy .env.example .env
)

echo [*] Levantando a infraestrutura completa do SOC...
docker-compose -f docker/docker-compose.enterprise.yml up -d --build

echo.
echo [SUCESSO] CyberGhost OSINT Enterprise esta rodando em segundo plano!
echo - Dashboard Web: http://localhost:3000
echo - API Gateway: http://localhost:8000
echo - Celery Flower: http://localhost:5555
echo - Neo4j Graph DB: http://localhost:7474
echo =========================================================================
echo Para ver os logs, rode: docker-compose -f docker/docker-compose.enterprise.yml logs -f
echo.
pause
