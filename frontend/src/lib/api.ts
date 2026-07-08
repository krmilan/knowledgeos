import { auth } from "./auth";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = auth.getToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    auth.logout();
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Something went wrong");
  }

  // 204 No Content has no body to parse
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Auth
export const apiAuth = {
  register: (email: string, password: string, full_name: string) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),

  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
};

// Workspaces
export const apiWorkspaces = {
  list: () => request<any[]>("/workspaces"),

  create: (name: string, description: string) =>
    request("/workspaces", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    }),
};

// Files
export const apiFiles = {
  list: (workspaceId: string) =>
    request<any[]>(`/workspaces/${workspaceId}/files`),

  upload: (workspaceId: string, file: globalThis.File) => {
    const token = auth.getToken();
    const formData = new FormData();
    formData.append("file", file);

    return fetch(`${BASE_URL}/workspaces/${workspaceId}/files/`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    }).then((r) => r.json());
  },

  delete: (workspaceId: string, fileId: string) =>
    request<void>(`/workspaces/${workspaceId}/files/${fileId}`, {
      method: "DELETE",
    }),
};

// Chat
export const apiChat = {
  send: (workspaceId: string, message: string) =>
    request<any>(`/workspaces/${workspaceId}/chat`, {
      method: "POST",
      body: JSON.stringify({ question: message }),
    }),
};

// Graph
export const apiGraph = {
  get: (workspaceId: string) =>
    request<any>(`/workspaces/${workspaceId}/graph`),
};

// Research
export const apiResearch = {
  run: (workspaceId: string, query: string) =>
    request<any>(`/workspaces/${workspaceId}/research`, {
      method: "POST",
      body: JSON.stringify({ query }),
    }),
};