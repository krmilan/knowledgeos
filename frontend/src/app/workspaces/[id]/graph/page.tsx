"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { auth } from "@/lib/auth";
import { apiGraph } from "@/lib/api";

export default function GraphPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [graphData, setGraphData] = useState<{ nodes: any[]; links: any[] }>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [ForceGraph, setForceGraph] = useState<any>(null);
  const [hoveredNode, setHoveredNode] = useState<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const fgRef = useRef<any>(null);

  useEffect(() => {
    if (!auth.isLoggedIn()) { router.push("/login"); return; }

    import("react-force-graph-2d").then((mod) => {
      setForceGraph(() => mod.default);
    });

    fetchGraph();
  }, [id]);

  // Measure container size for the graph canvas
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // After graph loads, apply force tuning
  useEffect(() => {
    if (!fgRef.current || graphData.nodes.length === 0) return;
    const fg = fgRef.current;
    // Strong repulsion pushes nodes apart
    fg.d3Force("charge").strength(-300);
    // Longer link distance spreads connected nodes out
    fg.d3Force("link").distance(120);
    // Weak centering so graph doesn't drift too far
    fg.d3Force("center").strength(0.05);
    fg.d3ReheatSimulation();
  }, [graphData, ForceGraph]);

  async function fetchGraph() {
    try {
      const data = await apiGraph.get(id) as any;

      const nodes = data.nodes?.map((n: any) => ({
        id: n.id,
        label: n.label || n.name || n.id,
        type: n.type,
        color: n.type === "document" ? "#3b82f6" : "#10b981",
      })) || [];

      const links = data.edges?.map((e: any) => ({
        source: e.source,
        target: e.target,
      })) || [];

      setGraphData({ nodes, links });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const nodeCanvasObject = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const isHovered = hoveredNode && hoveredNode.id === node.id;
    const isConnectedToHovered = hoveredNode && graphData.links.some(
      (l: any) =>
        (l.source?.id === hoveredNode.id && l.target?.id === node.id) ||
        (l.target?.id === hoveredNode.id && l.source?.id === node.id)
    );

    // Draw node circle
    const radius = node.type === "document" ? 8 : 5;
    ctx.beginPath();
    ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
    ctx.fillStyle = isHovered
      ? "#ffffff"
      : isConnectedToHovered
      ? node.color
      : node.color;
    ctx.globalAlpha = hoveredNode && !isHovered && !isConnectedToHovered ? 0.2 : 1;
    ctx.fill();
    ctx.globalAlpha = 1;

    // Always show label for document nodes or hovered/connected nodes
    const showLabel = node.type === "document" || isHovered || isConnectedToHovered || globalScale > 1.5;
    if (showLabel) {
      const label = node.label;
      const fontSize = Math.max(10, 14 / globalScale);
      ctx.font = `${node.type === "document" ? "bold " : ""}${fontSize}px Sans-Serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      // Background pill for readability
      const textWidth = ctx.measureText(label).width;
      const padding = 3;
      ctx.fillStyle = "rgba(17, 24, 39, 0.85)";
      ctx.fillRect(
        node.x - textWidth / 2 - padding,
        node.y + radius + 2,
        textWidth + padding * 2,
        fontSize + padding * 2
      );

      ctx.fillStyle = isHovered ? "#ffffff" : isConnectedToHovered ? "#d1fae5" : "rgba(255,255,255,0.75)";
      ctx.fillText(label, node.x, node.y + radius + fontSize / 2 + padding + 2);
    }
  }, [hoveredNode, graphData.links]);

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      {/* Navbar */}
      <div className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push("/dashboard")} className="text-gray-400 hover:text-white text-sm transition-colors">
            ← Dashboard
          </button>
          <span className="text-gray-600">|</span>
          <nav className="flex gap-4 text-sm">
            <button onClick={() => router.push(`/workspaces/${id}/files`)} className="text-gray-400 hover:text-white transition-colors">Files</button>
            <button onClick={() => router.push(`/workspaces/${id}/chat`)} className="text-gray-400 hover:text-white transition-colors">Chat</button>
            <span className="text-white font-medium">Graph</span>
            <button onClick={() => router.push(`/workspaces/${id}/research`)} className="text-gray-400 hover:text-white transition-colors">Research</button>
          </nav>
        </div>
        <button onClick={() => { auth.logout(); router.push("/login"); }} className="text-gray-400 hover:text-white text-sm transition-colors">
          Sign out
        </button>
      </div>

      <div className="flex-1 flex flex-col">
        <div className="px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold">Knowledge Graph</h2>
            <p className="text-gray-400 text-sm mt-1">
              {graphData.nodes.length} nodes · {graphData.links.length} edges
              {hoveredNode && (
                <span className="ml-3 text-emerald-400">
                  {hoveredNode.label} ({hoveredNode.type})
                </span>
              )}
            </p>
          </div>
          <div className="flex gap-4 text-sm">
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-500 inline-block" />
              <span className="text-gray-400">Document</span>
            </span>
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" />
              <span className="text-gray-400">Entity</span>
            </span>
            <span className="text-gray-600 text-xs self-center">Hover a node to explore</span>
          </div>
        </div>

        {error && (
          <div className="mx-6 mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        <div
          ref={containerRef}
          className="flex-1 bg-gray-900 mx-6 mb-6 rounded-2xl border border-gray-800 overflow-hidden"
        >
          {loading ? (
            <div className="flex items-center justify-center h-full text-gray-400">
              Loading graph...
            </div>
          ) : graphData.nodes.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              No graph data yet. Upload and process documents first.
            </div>
          ) : ForceGraph ? (
            <ForceGraph
              ref={fgRef}
              graphData={graphData}
              width={dimensions.width}
              height={dimensions.height}
              nodeLabel=""
              nodeColor="color"
              nodeRelSize={6}
              linkColor={() => "#374151"}
              linkWidth={1.5}
              backgroundColor="#111827"
              nodeCanvasObjectMode={() => "replace"}
              nodeCanvasObject={nodeCanvasObject}
              onNodeHover={(node: any) => setHoveredNode(node || null)}
              onNodeClick={(node: any) => {
                if (fgRef.current) {
                  fgRef.current.centerAt(node.x, node.y, 500);
                  fgRef.current.zoom(2.5, 500);
                }
              }}
              cooldownTicks={100}
              d3AlphaDecay={0.02}
              d3VelocityDecay={0.3}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              Loading renderer...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}