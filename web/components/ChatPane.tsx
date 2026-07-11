"use client";

import { useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import { streamChat, type Citation, type ToolCall } from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  text: string;
  tools: ToolCall[];
  error?: string;
};

const TOOL_LABELS: Record<string, string> = {
  whoami: "checked identity & team",
  search_documents: "searched documents",
  read_document: "read document (access-checked)",
  explore_process: "explored process",
  documents_owned_by_team: "listed team-owned docs",
  regulation_impact: "traced regulation impact",
};

function toolLabel(call: ToolCall): string {
  const arg = Object.values(call.input)[0];
  const base = TOOL_LABELS[call.tool] ?? call.tool;
  return arg ? `${base}: “${String(arg)}”` : base;
}

const SUGGESTIONS = [
  "What can I read about the KYC process?",
  "Which documents does the settlement team own?",
  "Who takes over after client onboarding?",
  "What's impacted if the AML Directive changes?",
];

export default function ChatPane({
  sessionId,
  personId,
  personName,
  onCitations,
}: {
  sessionId: string;
  personId: string;
  personName: string;
  onCitations: (docs: Citation[]) => void;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // fresh conversation when the persona changes
  useEffect(() => {
    setMessages([]);
  }, [personId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  async function send(question: string) {
    if (!question.trim() || busy) return;
    setInput("");
    setBusy(true);
    setMessages((m) => [
      ...m,
      { role: "user", text: question, tools: [] },
      { role: "assistant", text: "", tools: [] },
    ]);

    const patchLast = (fn: (msg: Message) => Message) =>
      setMessages((m) => [...m.slice(0, -1), fn(m[m.length - 1])]);

    try {
      for await (const ev of streamChat(sessionId, personId, question)) {
        if (ev.type === "text") {
          patchLast((msg) => ({ ...msg, text: msg.text + ev.text }));
        } else if (ev.type === "tool_call") {
          patchLast((msg) => ({
            ...msg,
            tools: [...msg.tools, { tool: ev.tool, input: ev.input }],
          }));
        } else if (ev.type === "citations") {
          onCitations(ev.docs);
        } else if (ev.type === "error") {
          patchLast((msg) => ({ ...msg, error: ev.message }));
        }
      }
    } catch (e) {
      patchLast((msg) => ({ ...msg, error: String(e) }));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="mt-8 space-y-3">
            <p className="text-sm text-zinc-500">
              You're asking as <span className="text-zinc-300">{personName}</span>.
              The agent only sees what this person is permitted to see. Try:
            </p>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="block w-full rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-left text-sm text-zinc-400 transition hover:border-zinc-600 hover:text-zinc-200"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {messages.map((msg, i) =>
          msg.role === "user" ? (
            <div key={i} className="flex justify-end">
              <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-sky-600/90 px-4 py-2 text-sm text-white">
                {msg.text}
              </div>
            </div>
          ) : (
            <div key={i} className="space-y-2">
              {msg.tools.map((t, j) => (
                <div
                  key={j}
                  className="flex items-center gap-2 text-xs text-zinc-500"
                >
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-violet-400" />
                  {toolLabel(t)}
                </div>
              ))}
              {(msg.text || (!busy && !msg.error)) && (
                <div className="chat-md max-w-[95%] rounded-2xl rounded-bl-sm border border-zinc-800 bg-zinc-900/70 px-4 py-3 text-sm leading-relaxed text-zinc-200">
                  <Markdown>{msg.text || "…"}</Markdown>
                </div>
              )}
              {msg.error && (
                <div className="rounded-lg border border-red-900 bg-red-950/50 px-3 py-2 text-xs text-red-400">
                  {msg.error}
                </div>
              )}
              {busy && i === messages.length - 1 && !msg.text && (
                <div className="px-1 text-xs text-zinc-500">thinking…</div>
              )}
            </div>
          ),
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="border-t border-zinc-800 p-3"
      >
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask as ${personName}…`}
            className="flex-1 rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-600 outline-none focus:border-sky-700"
          />
          <button
            type="submit"
            disabled={busy || !input.trim()}
            className="rounded-xl bg-sky-600 px-4 py-2.5 text-sm font-medium text-white transition disabled:opacity-40"
          >
            {busy ? "…" : "Send"}
          </button>
        </div>
      </form>
    </div>
  );
}
