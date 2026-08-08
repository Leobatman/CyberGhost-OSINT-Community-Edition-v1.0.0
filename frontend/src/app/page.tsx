import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen relative overflow-hidden">
      
      {/* Background Decor */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-full pointer-events-none">
        <div className="absolute top-20 left-20 w-96 h-96 bg-[var(--color-cyber-accent)] rounded-full mix-blend-multiply filter blur-[128px] opacity-10 animate-pulse"></div>
        <div className="absolute top-40 right-20 w-96 h-96 bg-[var(--color-cyber-neon)] rounded-full mix-blend-multiply filter blur-[128px] opacity-10"></div>
      </div>

      <header className="w-full glass-panel border-b-0 border-x-0 sticky top-0 z-50 py-4 px-8 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-[var(--color-cyber-accent)]/20 border border-[var(--color-cyber-accent)] flex items-center justify-center">
            <span className="text-[var(--color-cyber-accent)] font-bold">CG</span>
          </div>
          <h1 className="text-xl font-bold tracking-wider glow-text">CYBERGHOST <span className="text-[var(--color-cyber-muted)] font-mono text-sm ml-2">v15.0</span></h1>
        </div>
        
        <nav className="hidden md:flex gap-8 text-sm font-mono tracking-widest text-[var(--color-cyber-muted)]">
          <Link href="/dashboard" className="hover:text-[var(--color-cyber-accent)] transition-colors">DASHBOARD</Link>
          <Link href="/intelligence" className="hover:text-[var(--color-cyber-accent)] transition-colors">THREAT INTEL</Link>
          <Link href="/attack-graph" className="hover:text-[var(--color-cyber-accent)] transition-colors">ATTACK GRAPH</Link>
          <Link href="/settings" className="hover:text-[var(--color-cyber-accent)] transition-colors">SETTINGS</Link>
        </nav>
        
        <div>
          <button className="cyber-button px-6 py-2 rounded text-sm font-mono tracking-widest">
            LOGOUT
          </button>
        </div>
      </header>

      <main className="flex-grow container mx-auto px-6 py-12 flex flex-col items-center justify-center relative z-10 text-center">
        <div className="inline-block px-4 py-1 rounded-full border border-[var(--color-cyber-accent)]/30 bg-[var(--color-cyber-accent)]/10 text-[var(--color-cyber-accent)] text-xs font-mono mb-8 uppercase tracking-widest">
          Enterprise Security Active
        </div>
        
        <h2 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight leading-tight">
          Attack Surface <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--color-cyber-accent)] to-[var(--color-cyber-neon)]">Management</span>
        </h2>
        
        <p className="text-[var(--color-cyber-muted)] max-w-2xl mx-auto text-lg mb-12">
          Discover, map, and secure your digital footprint with advanced OSINT and continuous Threat Intelligence correlation powered by Neo4j Attack Graphs.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-5xl text-left">
          {/* Card 1 */}
          <div className="glass-panel rounded-xl p-6 group hover:border-[var(--color-cyber-accent)]/50 transition-colors cursor-pointer">
            <div className="w-12 h-12 rounded-lg bg-[var(--color-cyber-accent)]/10 flex items-center justify-center mb-4 text-[var(--color-cyber-accent)] font-mono text-xl">
              01
            </div>
            <h3 className="text-xl font-bold mb-2">Global Scans</h3>
            <p className="text-[var(--color-cyber-muted)] text-sm mb-4">
              Initialize deep recon tasks across domains, IP blocks, and ASN networks.
            </p>
            <div className="h-1 w-0 bg-[var(--color-cyber-accent)] group-hover:w-full transition-all duration-300"></div>
          </div>
          
          {/* Card 2 */}
          <div className="glass-panel rounded-xl p-6 group hover:border-[var(--color-cyber-neon)]/50 transition-colors cursor-pointer">
            <div className="w-12 h-12 rounded-lg bg-[var(--color-cyber-neon)]/10 flex items-center justify-center mb-4 text-[var(--color-cyber-neon)] font-mono text-xl">
              02
            </div>
            <h3 className="text-xl font-bold mb-2">Attack Graph</h3>
            <p className="text-[var(--color-cyber-muted)] text-sm mb-4">
              Explore critical exposure paths visually using the Cypher-powered engine.
            </p>
            <div className="h-1 w-0 bg-[var(--color-cyber-neon)] group-hover:w-full transition-all duration-300"></div>
          </div>

          {/* Card 3 */}
          <div className="glass-panel rounded-xl p-6 group hover:border-[var(--color-cyber-danger)]/50 transition-colors cursor-pointer">
            <div className="w-12 h-12 rounded-lg bg-[var(--color-cyber-danger)]/10 flex items-center justify-center mb-4 text-[var(--color-cyber-danger)] font-mono text-xl">
              03
            </div>
            <h3 className="text-xl font-bold mb-2">CTI Feeds (TAXII)</h3>
            <p className="text-[var(--color-cyber-muted)] text-sm mb-4">
              Ingest or export STIX 2.1 collections and integrate with your SOC tooling.
            </p>
            <div className="h-1 w-0 bg-[var(--color-cyber-danger)] group-hover:w-full transition-all duration-300"></div>
          </div>
        </div>
      </main>

      <footer className="w-full py-6 border-t border-[var(--color-cyber-border)]/50 text-center text-sm font-mono text-[var(--color-cyber-muted)]">
        CyberGhost OSINT Enterprise © 2026. SECURE BY DESIGN.
      </footer>
    </div>
  );
}
