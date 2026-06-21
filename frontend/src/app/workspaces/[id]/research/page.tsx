"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { auth } from "@/lib/auth";
import { apiResearch } from "@/lib/api";

export default function ResearchPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!auth.isLoggedIn()) { router.push("/login"); return; }
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim() || loading) return;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await apiResearch.run(id, query);
      setResult(data);
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
            <button onClick={() => router.push(`/workspaces/${id}/graph`)} className="text-gray-400 hover:text-white transition-colors">Graph</button>
            <span className="text-white font-medium">Research</span>
          </nav>
        </div>
        <button onClick={() => { auth.logout(); router.push("/login"); }} className="text-gray-400 hover:text-white text-sm transition-colors">
          Sign out
        </button>
      </div>

      <div className="max-w-4xl mx-auto w-full p-6 flex flex-col gap-6">
        <div>
          <h2 className="text-2xl font-semibold">Research Agent</h2>
          <p className="text-gray-400 text-sm mt-1">
            The agent searches your documents, knowledge graph, and the web to produce a structured report.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. What are Milan's key technical skills?"
            className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-600 text-white px-6 py-3 rounded-xl transition-colors font-medium whitespace-nowrap"
          >
            {loading ? "Researching..." : "Run Research"}
          </button>
        </form>

        {loading && (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
            <div className="flex items-center gap-3 text-gray-400">
              <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              Agent is working — searching documents, graph, and web...
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-4">
            {/* Report */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
              <h3 className="text-lg font-medium mb-4 text-blue-400">Report</h3>
              <div className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">
                {result.report}
              </div>
            </div>

            {/* Steps */}
           {result.steps && result.steps.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
                <h3 className="text-lg font-medium mb-4 text-emerald-400">
                    Agent Steps · {result.iterations} iterations
                </h3>
                <div className="space-y-2">
                    {result.steps.map((step: any, i: number) => (
                        <div key={i} className="flex gap-3 text-sm">
                            <span className="text-gray-600 w-5 shrink-0">{i + 1}.</span>
                            <span className="text-gray-400">
                                <span className="text-blue-400">{step.tool || step}</span>
                                {step.args && (
                                    <span className="text-gray-500 ml-2">— {JSON.stringify(step.args)}</span>
                                )}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}