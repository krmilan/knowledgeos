"use client";

import { useEffect, useState, useRef } from "react";
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

  useEffect(() => {
    if (!auth.isLoggedIn()) { router.push("/login"); return; }

    // Dynamically import — this library only works in browser, not SSR
    import("react-force-graph-2d").then((mod) => {
      setForceGraph(() => mod.default);
    });

    fetchGraph();
  }, [id]);

  async function fetchGraph() {
    try {
      const data = await apiGraph.get(id) as any;

      // Map backend response to force-graph format
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
          </div>
        </div>

        {error && (
          <div className="mx-6 mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        <div className="flex-1 bg-gray-900 mx-6 mb-6 rounded-2xl border border-gray-800 overflow-hidden">
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
              graphData={graphData}
              nodeLabel="label"
              nodeColor="color"
              nodeRelSize={6}
              linkColor={() => "#374151"}
              backgroundColor="#111827"
              nodeCanvasObjectMode={() => "after"}
              nodeCanvasObject={(node: any, ctx: any, globalScale: any) => {
                const label = node.label;
                const fontSize = 12 / globalScale;
                ctx.font = `${fontSize}px Sans-Serif`;
                ctx.fillStyle = "rgba(255,255,255,0.8)";
                ctx.textAlign = "center";
                ctx.fillText(label, node.x, node.y + 10);
              }}
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