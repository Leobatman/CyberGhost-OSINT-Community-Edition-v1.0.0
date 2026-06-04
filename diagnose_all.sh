#!/bin/bash
# Diagnose script

echo "Running diagnostics..."

# 1. Código legado ainda existe?
[ -f "src/ui/web_dashboard.py" ] && echo "❌ S-05, S-14: Flask legado presente" || echo "✅ Legado ausente"
[ -f "cyberghost-v1.sh" ] && echo "❌ S-04, S-03: Script monolito presente" || echo "✅ Monolito ausente"
[ -f "src/core/database.sh" ] && echo "❌ S-01, S-20: SQL injection presente" || echo "✅ DB legado ausente"

# 2. Secrets hardcoded no histórico?
git log --all --full-history --source --pretty=oneline | grep -i "secret\|key\|password\|token" > /dev/null && echo "❌ S-02, S-13: Secrets no histórico" || echo "✅ Sem secrets óbvios no histórico (git log filter)"

# 3. Cypher Injection (S-21)
grep -n 'f".*MERGE.*\[r:{' intel/knowledge_graph.py 2>/dev/null && echo "❌ S-21: Cypher injection vulnerability" || echo "✅ Cypher Injection tratada"

# 4. Ownership check missing (S-22)
grep -A 10 'def get_scan_results' backend/api/v1/scans.py 2>/dev/null | grep -q 'scan.user_id != current_user.id' || echo "❌ S-22: Missing ownership check" && echo "✅ Ownership check OK"

# 5. asyncio.get_event_loop() (S-24)
grep -n 'asyncio.get_event_loop()' workers/tasks/scan_tasks.py 2>/dev/null && echo "❌ S-24: Deprecated event loop" || echo "✅ Event loop asyncio atualizado"

# 6. Late imports (E-01)
LATE_IMPORTS=$(grep -n 'from.*import.*$' backend/api/v1/scans.py 2>/dev/null | grep -v '^[[:space:]]*#' | head -20)
HAS_LATE=0
while read line; do
  line_num=$(echo "$line" | cut -d: -f1)
  if [ -n "$line_num" ] && [ "$line_num" -gt 50 ]; then
      echo "⚠️ E-01: Late import at line $line_num (should be at top)"
      HAS_LATE=1
  fi
done <<< "$LATE_IMPORTS"
if [ "$HAS_LATE" -eq 0 ]; then echo "✅ Sem late imports"; fi

# 7. Missing pagination (S-25)
grep -A 5 'def get_scan_results' backend/api/v1/scans.py 2>/dev/null | grep -q 'limit\|offset\|page' || echo "❌ S-25: No pagination"

# 8. Sem cache Redis (G-01)
grep -r 'redis\|Redis' backend/ --include="*.py" 2>/dev/null | grep -q 'get\|set' || echo "⚠️ G-01: Redis cache not implemented"

# 9. Sem migrations (Alembic)
[ -d "alembic/versions" ] && [ "$(ls -A alembic/versions 2>/dev/null)" ] || echo "❌ DB-01: No Alembic migrations"

# 10. CI/CD sem DAST (G-CI-01)
grep -q 'zap\|dast\|nuclei' .github/workflows/ci.yml 2>/dev/null || echo "⚠️ CI-01: No DAST in pipeline"

# 11. Sem testes unitários
[ -d "tests/unit" ] && [ "$(find tests/unit -name 'test_*.py' 2>/dev/null | wc -l)" -gt 3 ] || echo "⚠️ TEST-01: Insufficient unit tests"

# 12. Neo4j sync com PostgreSQL (E-03 do relatório)
grep -q 'sync.*postgres\|celery.*neo4j' workers/tasks/ 2>/dev/null || echo "⚠️ DATA-01: No Neo4j/PostgreSQL sync"

echo "Diagnostics complete."
