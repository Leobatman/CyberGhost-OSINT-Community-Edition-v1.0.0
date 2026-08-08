import asyncio
from typing import List, Dict, Any
from core.models import OsintResult
from modules.dns_intel import run_dns_module
from modules.cert_intel import run_cert_module
from modules.web_intel import run_web_module
from modules.network_intel import run_network_module

class OsintOrchestrator:
    def __init__(self, target: str):
        self.target = target
        self.results: List[OsintResult] = []

    async def run_all(self):
        """Run all OSINT modules concurrently."""
        tasks = [
            run_dns_module(self.target),
            run_cert_module(self.target),
            run_web_module(self.target),
            run_network_module(self.target),
        ]
        
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res_list in results_lists:
            if isinstance(res_list, Exception):
                self.results.append(OsintResult(
                    source="Orchestrator", category="System", target=self.target,
                    status="failed", data={}, errors=[f"Module crash: {res_list}"]
                ))
            else:
                self.results.extend(res_list)
                
    def calculate_score(self) -> int:
        """Calculate a basic security posture score (0-100)."""
        score = 100
        
        for res in self.results:
            if res.status != "success":
                continue
                
            # DNS Security penalty
            if res.source == "DNS TXT":
                if res.data.get("SPF") == "Missing":
                    score -= 10
                if res.data.get("DMARC") == "Missing":
                    score -= 10
                    
            # Web Security headers penalty
            if res.source == "Security Headers":
                findings = res.data.get("findings", [])
                for f in findings:
                    if "Missing:" in f:
                        score -= 5
                        
            # Reputation penalty
            if res.source == "DNSBL":
                for bl, status in res.data.items():
                    if status == "LISTED":
                        score -= 20
                        
            # Port Scan penalty (too many open ports)
            if res.source == "Port Scan":
                open_ports = res.data.get("open_ports", [])
                if len(open_ports) > 3:
                    score -= (len(open_ports) - 3) * 5
                    
        return max(0, min(100, score))

    def get_summary(self) -> Dict[str, Any]:
        """Return a normalized dictionary of all findings."""
        summary = {
            "target": self.target,
            "security_score": self.calculate_score(),
            "modules_run": len(self.results),
            "findings": [r.to_dict() for r in self.results]
        }
        return summary
