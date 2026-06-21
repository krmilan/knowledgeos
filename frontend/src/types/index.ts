export interface User {
  id: string;
  email: string;
  full_name: string;
}

export interface Workspace {
  id: string;
  name: string;
  description: string;
  role: string;
}

export interface File {
  id: string;
  original_name: string;
  file_type: string;
  size_bytes: string;
  is_processed: boolean;
  created_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

export interface Source {
  file_id: string;
  filename: string;
  score: number;
  text: string;
}

export interface Entity {
  id: string;
  name: string;
  type: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: "document" | "entity";
}

export interface GraphEdge {
  source: string;
  target: string;
}

export interface ResearchResult {
  query: string;
  report: string;
  steps: string[];
  iterations: number;
}