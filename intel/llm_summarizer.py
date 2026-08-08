"""
CyberGhost OSINT Enterprise — AI/ML Engine
Investigation Summarizer utilizing LLMs (OpenAI, Anthropic, Ollama).
"""
from __future__ import annotations

import json
from typing import Any

import structlog
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama

from backend.core.config import settings

log = structlog.get_logger(__name__)


class InvestigationSummarizer:
    """
    Consumes findings and generates an executive summary using an LLM.
    Dynamically loads the configured AI provider.
    """

    def __init__(self) -> None:
        self.provider = settings.ai.provider
        self.model = self._initialize_model()

    def _initialize_model(self) -> Any:
        """Initialize the correct LangChain chat model based on config."""
        log.info("ai_summarizer_init", provider=self.provider)

        try:
            if self.provider == "openai" and settings.ai.openai_api_key:
                return ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=settings.ai.openai_api_key.get_secret_value(),
                    temperature=0.3,
                )
            elif self.provider == "anthropic" and settings.ai.anthropic_api_key:
                return ChatAnthropic(
                    model="claude-3-haiku-20240307",
                    api_key=settings.ai.anthropic_api_key.get_secret_value(),
                    temperature=0.3,
                )
            else:
                # Default to Ollama (Local)
                return ChatOllama(
                    model=settings.ai.ollama_model,
                    base_url=settings.ai.ollama_base_url,
                    temperature=0.3,
                )
        except Exception as e:
            log.error("ai_summarizer_init_failed", error=str(e))
            return None

    async def summarize(
        self, target: str, scan_results: list[dict[str, Any]], iocs: list[dict[str, Any]]
    ) -> str:
        """
        Generate an executive summary from scan results and extracted IOCs.
        """
        if not self.model:
            log.warning("ai_summarizer_skipped", reason="no_model_configured")
            return "Resumo de IA indisponível: Modelo não configurado."

        system_prompt = """Você é um Analista de CTI (Cyber Threat Intelligence) Sênior.
Sua missão é criar um Resumo Executivo profissional de uma investigação OSINT.

O resumo deve ser em Português do Brasil, formatado em Markdown, e focar em:
1. **Contexto Geral:** O que foi encontrado no alvo.
2. **Riscos e Ameaças:** Se foram detectadas vulnerabilidades, portas perigosas expostas ou indicadores maliciosos.
3. **Mapeamento de Entidades:** Sumário dos subdomínios, IPs e emails relevantes.
4. **Recomendações Práticas:** O que o time de segurança deve fazer a seguir.

Seja objetivo, profissional e direto. Destaque alertas críticos em negrito.
"""

        # Prepare context data (truncated to avoid massive context windows)
        context_data = {
            "target": target,
            "modules_executed": list(set(r.get("module") for r in scan_results)),
            "critical_findings": [r for r in scan_results if r.get("severity") in ("critical", "high")][:10],
            "total_iocs_extracted": len(iocs),
            "malicious_iocs": [i for i in iocs if i.get("malicious")][:10],
            "sample_iocs": [i.get("value") for i in iocs[:20]],
        }

        user_content = f"Dados da Investigação:\n\n{json.dumps(context_data, indent=2, ensure_ascii=False)}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ]

        log.info("ai_summarizer_running", target=target)
        try:
            # Langchain async invocation
            response = await self.model.ainvoke(messages)
            log.info("ai_summarizer_success", target=target)
            return str(response.content)
        except Exception as e:
            log.error("ai_summarizer_failed", target=target, error=str(e))
            return f"Erro ao gerar resumo via IA: {str(e)}"

