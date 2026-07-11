// Client for the FastAPI backend. SSE goes direct to the API origin
// (not through the Next proxy) so streaming is never buffered.

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Person = {
  id: string;
  name: string;
  role: string;
  team: string;
};

export type GraphNode = {
  id: string;
  label: "Team" | "Person" | "Process" | "System" | "Regulation" | "Document";
  caption: string;
  classification: string | null;
  props: Record<string, unknown>;
  accessible: boolean | null; // only set for Document nodes
};

export type GraphRel = {
  id: string;
  source: string;
  target: string;
  type: string;
  props: Record<string, unknown>;
};

// Permission-checked read: either content, or an access-denied shape.
export type DocumentDetails = {
  id: string;
  title: string;
  type?: string;
  classification?: string;
  owner_team?: string;
  content?: string;
  access?: "DENIED";
  reason?: string;
  contact?: string;
  error?: string;
};

export async function fetchDocument(
  docId: string,
  personId: string,
): Promise<DocumentDetails> {
  const res = await fetch(`${API_URL}/document/${docId}?person=${personId}`);
  if (!res.ok) throw new Error(`GET /document ${res.status}`);
  return res.json();
}

export type GraphPayload = { nodes: GraphNode[]; relationships: GraphRel[] };

export type ToolCall = { tool: string; input: Record<string, unknown> };

export type Citation = { id: string; accessible: boolean };

export type StreamEvent =
  | { type: "text"; text: string }
  | { type: "tool_call"; tool: string; input: Record<string, unknown> }
  | { type: "citations"; docs: Citation[] }
  | { type: "done"; answer: string }
  | { type: "error"; message: string };

export async function fetchPeople(): Promise<Person[]> {
  const res = await fetch(`${API_URL}/people`);
  if (!res.ok) throw new Error(`GET /people ${res.status}`);
  return res.json();
}

export async function fetchGraph(personId: string): Promise<GraphPayload> {
  const res = await fetch(`${API_URL}/graph?person=${personId}`);
  if (!res.ok) throw new Error(`GET /graph ${res.status}`);
  return res.json();
}

export async function* streamChat(
  sessionId: string,
  personId: string,
  message: string,
  signal?: AbortSignal,
): AsyncGenerator<StreamEvent> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, person_id: personId, message }),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`POST /chat ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        yield JSON.parse(line.slice(6)) as StreamEvent;
      }
    }
  }
}
