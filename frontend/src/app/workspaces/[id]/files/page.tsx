"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { auth } from "@/lib/auth";
import { apiFiles } from "@/lib/api";
import { File as KFile } from "@/types";

export default function FilesPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [files, setFiles] = useState<KFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [notification, setNotification] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!auth.isLoggedIn()) { router.push("/login"); return; }
    fetchFiles();

    // WebSocket for real-time file processing notifications
    const ws = new WebSocket(`ws://localhost:8000/ws/${id}`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "file_processed") {
        setNotification("File processed successfully!");
        fetchFiles();
        setTimeout(() => setNotification(""), 3000);
      }
    };
    return () => ws.close();
  }, [id]);

  async function fetchFiles() {
    try {
      const data = await apiFiles.list(id) as KFile[];
      setFiles(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await apiFiles.upload(id, file);
      setNotification("File uploaded! Processing...");
      fetchFiles();
    } catch (err: any) {
      setNotification("Upload failed: " + err.message);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  const statusColor: Record<string, string> = {
    pending: "text-yellow-400",
    processing: "text-blue-400",
    completed: "text-green-400",
    failed: "text-red-400",
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Navbar */}
      <div className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push("/dashboard")} className="text-gray-400 hover:text-white text-sm transition-colors">
            ← Dashboard
          </button>
          <span className="text-gray-600">|</span>
          <nav className="flex gap-4 text-sm">
            <span className="text-white font-medium">Files</span>
            <button onClick={() => router.push(`/workspaces/${id}/chat`)} className="text-gray-400 hover:text-white transition-colors">Chat</button>
            <button onClick={() => router.push(`/workspaces/${id}/graph`)} className="text-gray-400 hover:text-white transition-colors">Graph</button>
            <button onClick={() => router.push(`/workspaces/${id}/research`)} className="text-gray-400 hover:text-white transition-colors">Research</button>
          </nav>
        </div>
        <button onClick={() => { auth.logout(); router.push("/login"); }} className="text-gray-400 hover:text-white text-sm transition-colors">
          Sign out
        </button>
      </div>

      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold">Files</h2>
          <div>
            <input ref={fileInputRef} type="file" accept=".pdf" onChange={handleUpload} className="hidden" id="file-upload" />
            <label htmlFor="file-upload" className={`cursor-pointer bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm transition-colors ${uploading ? "opacity-50 pointer-events-none" : ""}`}>
              {uploading ? "Uploading..." : "+ Upload PDF"}
            </label>
          </div>
        </div>

        {notification && (
          <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-400 text-sm">
            {notification}
          </div>
        )}

        {loading ? (
          <div className="text-gray-400 text-center py-12">Loading...</div>
        ) : files.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No files yet. Upload a PDF to get started.</div>
        ) : (
          <div className="space-y-3">
            {files.map((file) => (
              <div key={file.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center justify-between">
                <div>
                  <p className="text-white font-medium">{file.original_name}</p>
                  <p className="text-gray-500 text-xs mt-1">{new Date(file.created_at).toLocaleDateString()}</p>
                </div>
                <span className={`text-sm font-medium ${file.is_processed ? "text-green-400" : "text-yellow-400"}`}>
                    {file.is_processed ? "completed" : "processing"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}