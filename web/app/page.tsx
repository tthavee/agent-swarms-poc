"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import ChatPane from "@/components/ChatPane";
import {
  fetchGraph,
  fetchPeople,
  type Citation,
  type GraphPayload,
  type Person,
} from "@/lib/api";

// NVL renders to canvas and touches window — client-only.
const GraphPane = dynamic(() => import("@/components/GraphPane"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center text-zinc-500">
      loading graph…
    </div>
  ),
});

export default function Home() {
  const sessionId = useMemo(() => crypto.randomUUID(), []);
  const [people, setPeople] = useState<Person[]>([]);
  const [personId, setPersonId] = useState<string>("p02"); // Marcus Webb
  const [graph, setGraph] = useState<GraphPayload | null>(null);
  const [highlighted, setHighlighted] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPeople().then(setPeople).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    setHighlighted(new Set());
    fetchGraph(personId).then(setGraph).catch((e) => setError(String(e)));
  }, [personId]);

  const person = people.find((p) => p.id === personId);

  return (
    <div className="flex h-screen flex-col bg-zinc-950 text-zinc-200">
      <header className="flex items-center justify-between border-b border-zinc-800 px-5 py-3">
        <div className="flex items-baseline gap-3">
          <h1 className="text-base font-semibold tracking-tight">
            Banking Context Graph
          </h1>
          <span className="text-xs text-zinc-500">
            permission-aware graph agent
          </span>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <span className="text-zinc-500">Asking as</span>
          <select
            value={personId}
            onChange={(e) => setPersonId(e.target.value)}
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-sm outline-none focus:border-sky-700"
          >
            {people.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} — {p.role} ({p.team})
              </option>
            ))}
          </select>
        </label>
      </header>

      {error && (
        <div className="border-b border-red-900 bg-red-950/60 px-5 py-2 text-xs text-red-400">
          {error} — is the API running? <code>uvicorn api.main:app --port 8000</code>
        </div>
      )}

      <main className="flex min-h-0 flex-1 flex-col lg:flex-row">
        <section className="min-h-[40%] min-w-0 flex-1 border-b border-zinc-800 lg:border-b-0 lg:border-r">
          <GraphPane
            graph={graph}
            highlighted={highlighted}
            personId={personId}
            personName={person?.name ?? "…"}
          />
        </section>
        <aside className="flex min-h-0 w-full shrink-0 flex-col lg:h-auto lg:w-[440px]">
          <ChatPane
            sessionId={sessionId}
            personId={personId}
            personName={person?.name ?? "…"}
            onCitations={(docs: Citation[]) =>
              setHighlighted(new Set(docs.map((d) => d.id)))
            }
          />
        </aside>
      </main>
    </div>
  );
}
