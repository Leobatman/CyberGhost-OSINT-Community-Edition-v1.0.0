import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function IntelligencePage() {
  const mockIocs = [
    { id: 1, type: "IP", value: "192.168.1.50", malicious: true, confidence: 95, date: "2026-07-21" },
    { id: 2, type: "Domain", value: "malicious-actor.net", malicious: true, confidence: 88, date: "2026-07-21" },
    { id: 3, type: "Hash", value: "a1b2c3d4e5f6...", malicious: false, confidence: 10, date: "2026-07-20" },
    { id: 4, type: "CVE", value: "CVE-2023-456", malicious: true, confidence: 100, date: "2026-07-20" },
  ];

  return (
    <div className="flex flex-col h-full min-h-screen p-8 gap-8">
      <header>
        <h1 className="text-3xl font-bold tracking-tight glow-text text-[var(--color-cyber-danger)]">Threat Intelligence</h1>
        <p className="text-[var(--color-cyber-muted)] font-mono text-sm mt-1">TAXII 2.1 Collections & OSINT Indicators</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Active Feeds</CardDescription>
            <CardTitle className="text-3xl text-[var(--color-cyber-accent)]">4</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total IOCs</CardDescription>
            <CardTitle className="text-3xl text-[var(--color-cyber-accent)]">14,239</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Malicious Entities</CardDescription>
            <CardTitle className="text-3xl text-[var(--color-cyber-danger)] glow-text">1,402</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>TAXII Server Status</CardDescription>
            <CardTitle className="text-xl text-[var(--color-cyber-neon)] flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-[var(--color-cyber-neon)] animate-pulse shadow-[0_0_8px_var(--color-cyber-neon)]"></span>
              ONLINE
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card className="flex-1">
        <CardHeader>
          <CardTitle>Recent Indicators of Compromise (IOCs)</CardTitle>
          <CardDescription>Latest threats identified across all connected feeds.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border border-[var(--color-cyber-border)] overflow-hidden">
            <table className="w-full text-sm text-left">
              <thead className="bg-[var(--color-cyber-border)]/50 text-[var(--color-cyber-muted)] uppercase font-mono text-xs">
                <tr>
                  <th className="px-6 py-3 font-medium">Type</th>
                  <th className="px-6 py-3 font-medium">Value</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium">Confidence</th>
                  <th className="px-6 py-3 font-medium text-right">Discovered</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-cyber-border)]/50">
                {mockIocs.map((ioc) => (
                  <tr key={ioc.id} className="hover:bg-[var(--color-cyber-border)]/20 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium">{ioc.type}</td>
                    <td className="px-6 py-4 font-mono">{ioc.value}</td>
                    <td className="px-6 py-4">
                      {ioc.malicious ? (
                        <Badge variant="destructive">Malicious</Badge>
                      ) : (
                        <Badge variant="secondary">Unknown</Badge>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-[var(--color-cyber-border)] rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${ioc.confidence > 80 ? 'bg-[var(--color-cyber-danger)]' : 'bg-[var(--color-cyber-accent)]'}`} 
                            style={{width: `${ioc.confidence}%`}}
                          />
                        </div>
                        <span className="text-xs font-mono">{ioc.confidence}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right text-[var(--color-cyber-muted)]">{ioc.date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
