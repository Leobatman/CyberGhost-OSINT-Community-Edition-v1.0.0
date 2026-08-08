"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Dynamically import force-graph to avoid SSR issues
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
  loading: () => <div className="w-full h-[600px] flex items-center justify-center glow-text text-[var(--color-cyber-accent)] font-mono">Initializing Attack Graph Engine...</div>
});

const MOCK_GRAPH_DATA = {
  nodes: [
    { id: "Domain:example.com", group: "Domain", val: 5 },
    { id: "Subdomain:api.example.com", group: "Subdomain", val: 3 },
    { id: "IP:192.168.1.50", group: "IP", val: 3 },
    { id: "Vuln:CVE-2023-456", group: "Vulnerability", val: 8 },
    { id: "Actor:APT29", group: "ThreatActor", val: 6 },
  ],
  links: [
    { source: "Subdomain:api.example.com", target: "Domain:example.com", label: "PART_OF" },
    { source: "Domain:example.com", target: "IP:192.168.1.50", label: "RESOLVES_TO" },
    { source: "IP:192.168.1.50", target: "Vuln:CVE-2023-456", label: "AFFECTS" },
    { source: "Actor:APT29", target: "Vuln:CVE-2023-456", label: "EXPLOITS" },
  ]
};

export default function AttackGraphPage() {
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [selectedNode, setSelectedNode] = useState<any>(null);

  useEffect(() => {
    // Basic responsive resize
    const updateDimensions = () => {
      const container = document.getElementById("graph-container");
      if (container) {
        setDimensions({
          width: container.offsetWidth,
          height: 600
        });
      }
    };
    
    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  // Node coloring strategy based on type
  const getNodeColor = (node: any) => {
    switch(node.group) {
      case "Domain": return "var(--color-cyber-accent)"; // Cyan
      case "Subdomain": return "#0ea5e9";
      case "IP": return "#3b82f6";
      case "Vulnerability": return "var(--color-cyber-danger)"; // Red
      case "ThreatActor": return "#a855f7"; // Purple
      default: return "#8b92a5";
    }
  };

  return (
    <div className="flex flex-col h-full min-h-screen">
      <header className="p-6 border-b border-[var(--color-cyber-border)] bg-[var(--color-cyber-card)]/50 backdrop-blur-sm sticky top-0 z-10 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight glow-text text-transparent bg-clip-text bg-gradient-to-r from-[var(--color-cyber-accent)] to-[var(--color-cyber-neon)]">Attack Graph</h1>
          <p className="text-[var(--color-cyber-muted)] font-mono text-sm mt-1">Interactive Attack Surface Visualization Engine</p>
        </div>
        <div className="flex gap-2">
           <Badge variant="outline">Nodes: {MOCK_GRAPH_DATA.nodes.length}</Badge>
           <Badge variant="outline">Edges: {MOCK_GRAPH_DATA.links.length}</Badge>
           <Badge variant="destructive">Critical Paths: 1</Badge>
        </div>
      </header>

      <main className="flex-1 flex flex-col md:flex-row p-6 gap-6 relative z-0">
        
        {/* Graph Canvas */}
        <Card className="flex-1 overflow-hidden flex flex-col border-[var(--color-cyber-border)] bg-[var(--color-cyber-dark)]/90" id="graph-container">
           <CardContent className="p-0 flex-1 relative bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-[rgba(0,240,255,0.05)] to-transparent">
              <ForceGraph2D
                width={dimensions.width}
                height={dimensions.height}
                graphData={MOCK_GRAPH_DATA}
                nodeColor={getNodeColor}
                nodeRelSize={6}
                linkColor={() => 'rgba(139, 146, 165, 0.4)'}
                linkWidth={1.5}
                linkDirectionalArrowLength={3.5}
                linkDirectionalArrowRelPos={1}
                onNodeClick={(node) => setSelectedNode(node)}
                backgroundColor="transparent"
                nodeCanvasObject={(node: any, ctx, globalScale) => {
                  const label = node.id;
                  const fontSize = 12/globalScale;
                  ctx.font = `${fontSize}px Sans-Serif`;
                  const textWidth = ctx.measureText(label).width;
                  const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2); 

                  ctx.fillStyle = 'rgba(7, 7, 11, 0.8)';
                  ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1]);

                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillStyle = getNodeColor(node);
                  ctx.fillText(label, node.x, node.y);

                  node.__bckgDimensions = bckgDimensions;
                }}
              />
           </CardContent>
        </Card>

        {/* Sidebar / Inspector */}
        <div className="w-full md:w-80 flex flex-col gap-4">
          <Card className="flex-1">
            <CardHeader>
              <CardTitle>Node Inspector</CardTitle>
              <CardDescription>Select a node to view properties</CardDescription>
            </CardHeader>
            <CardContent>
              {selectedNode ? (
                <div className="space-y-4">
                  <div>
                    <p className="text-xs text-[var(--color-cyber-muted)] uppercase tracking-wider mb-1">Entity Type</p>
                    <Badge variant={selectedNode.group === "Vulnerability" ? "destructive" : "default"}>{selectedNode.group}</Badge>
                  </div>
                  <div>
                    <p className="text-xs text-[var(--color-cyber-muted)] uppercase tracking-wider mb-1">Identity</p>
                    <p className="font-mono text-sm break-all">{selectedNode.id}</p>
                  </div>
                  <div>
                     <p className="text-xs text-[var(--color-cyber-muted)] uppercase tracking-wider mb-1">Risk Score</p>
                     <div className="h-2 w-full bg-[var(--color-cyber-border)] rounded overflow-hidden">
                       <div 
                         className="h-full bg-[var(--color-cyber-danger)]" 
                         style={{width: `${(selectedNode.val / 10) * 100}%`}}
                       />
                     </div>
                  </div>
                </div>
              ) : (
                <div className="h-40 flex items-center justify-center border border-dashed border-[var(--color-cyber-border)] rounded text-[var(--color-cyber-muted)] text-sm font-mono">
                  No node selected
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
