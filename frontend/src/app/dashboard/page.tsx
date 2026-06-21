"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/auth";
import { apiWorkspaces } from "@/lib/api";
import { Workspace } from "@/types";

export default function DashboardPage() {
  const router = useRouter();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!auth.isLoggedIn()) {
      router.push("/login");
      return;
    }
    fetchWorkspaces();
  }, []);

  async function fetchWorkspaces() {
    try {
      const data = await apiWorkspaces.list() as Workspace[];
      setWorkspaces(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    try {
      await apiWorkspaces.create(name, description);
      setName("");
      setDescription("");
      setShowCreate(false);
      fetchWorkspaces();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Navbar */}
      <div className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">KnowledgeOS</h1>
        <button
          onClick={() => { auth.logout(); router.push("/login"); }}
          className="text-gray-400 hover:text-white text-sm transition-colors"
        >
          Sign out
        </button>
      </div>

      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold">Your Workspaces</h2>
          <button
            onClick={() => setShowCreate(true)}
            className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm transition-colors"
          >
            + New Workspace
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Create workspace form */}
        {showCreate && (
          <div className="mb-6 bg-gray-900 rounded-2xl p-6 border border-gray-800">
            <h3 className="text-lg font-medium mb-4">New Workspace</h3>
            <form onSubmit={handleCreate} className="space-y-3">
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Workspace name"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
                required
              />
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Description (optional)"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
              />
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={creating}
                  className="bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                >
                  {creating ? "Creating..." : "Create"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Workspace list */}
        {loading ? (
          <div className="text-gray-400 text-center py-12">Loading...</div>
        ) : workspaces.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No workspaces yet. Create one to get started.
          </div>
        ) : (
          <div className="grid gap-4">
            {workspaces.map((ws) => (
              <div
                key={ws.id}
                onClick={() => router.push(`/workspaces/${ws.id}/files`)}
                className="bg-gray-900 border border-gray-800 rounded-2xl p-6 cursor-pointer hover:border-blue-500/50 hover:bg-gray-800/50 transition-all"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-medium">{ws.name}</h3>
                    {ws.description && (
                      <p className="text-gray-400 text-sm mt-1">{ws.description}</p>
                    )}
                  </div>
                  <span className="text-gray-600 text-sm">{ws.role}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}