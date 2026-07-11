"use client";

import { useEffect, useState } from "react";
import {
  fetchDocument,
  type DocumentDetails,
  type GraphNode,
  type GraphRel,
} from "@/lib/api";

export type Selection =
  | { kind: "node"; node: GraphNode }
  | { kind: "rel"; rel: GraphRel; from?: GraphNode; to?: GraphNode };

const LABEL_BADGES: Record<string, string> = {
  Team: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  Person: "bg-sky-500/15 text-sky-400 border-sky-500/30",
  Process: "bg-violet-500/15 text-violet-400 border-violet-500/30",
  System: "bg-slate-500/15 text-slate-400 border-slate-500/30",
  Regulation: "bg-pink-500/15 text-pink-400 border-pink-500/30",
  Document: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
};

const PROP_LABELS: Record<string, string> = {
  role: "Role",
  email: "Email",
  department: "Department",
  sla_hours: "SLA (hours)",
  regulatory_flag: "Regulatory",
  vendor: "Vendor",
  tier: "Tier",
  criticality: "Criticality",
  jurisdiction: "Jurisdiction",
  summary: "Summary",
  type: "Type",
  classification: "Classification",
  process: "Process",
  trigger: "Trigger",
};

function PropRows({ props }: { props: Record<string, unknown> }) {
  const entries = Object.entries(props).filter(
    ([k, v]) => v !== null && v !== undefined && k !== "name" && k !== "title",
  );
  if (!entries.length) return null;
  return (
    <dl className="space-y-1.5">
      {entries.map(([k, v]) => (
        <div key={k} className="flex gap-2 text-xs">
          <dt className="w-24 shrink-0 text-zinc-500">{PROP_LABELS[k] ?? k}</dt>
          <dd className="text-zinc-300">
            {typeof v === "boolean" ? (v ? "yes" : "no") : String(v)}
          </dd>
        </div>
      ))}
    </dl>
  );
}

function DocumentBody({
  docId,
  personId,
}: {
  docId: string;
  personId: string;
}) {
  const [doc, setDoc] = useState<DocumentDetails | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setDoc(null);
    setFailed(false);
    fetchDocument(docId, personId)
      .then(setDoc)
      .catch(() => setFailed(true));
  }, [docId, personId]);

  if (failed)
    return <p className="text-xs text-red-400">Could not load document.</p>;
  if (!doc) return <p className="text-xs text-zinc-500">loading…</p>;

  if (doc.access === "DENIED") {
    return (
      <div className="rounded-lg border border-red-900/60 bg-red-950/40 p-3">
        <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-red-400">
          Access denied
        </div>
        <p className="text-xs text-zinc-400">{doc.reason}</p>
        {doc.contact && (
          <p className="mt-2 text-xs text-zinc-300">
            Request access from <span className="font-medium">{doc.contact}</span>
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2 text-[11px]">
        {doc.classification && (
          <span className="rounded-full border border-zinc-700 px-2 py-0.5 text-zinc-400">
            {doc.classification}
          </span>
        )}
        {doc.owner_team && (
          <span className="rounded-full border border-zinc-700 px-2 py-0.5 text-zinc-400">
            owned by {doc.owner_team}
          </span>
        )}
      </div>
      <p className="text-xs leading-relaxed text-zinc-300">{doc.content}</p>
    </div>
  );
}

export default function DetailsCard({
  selection,
  personId,
  onClose,
}: {
  selection: Selection;
  personId: string;
  onClose: () => void;
}) {
  const isNode = selection.kind === "node";
  const title = isNode
    ? selection.node.caption
    : selection.rel.type.replace(/_/g, " ");
  const badge = isNode ? selection.node.label : "Relationship";
  const badgeClass = isNode
    ? LABEL_BADGES[selection.node.label]
    : "bg-zinc-500/15 text-zinc-400 border-zinc-500/30";

  return (
    <div className="absolute right-4 top-4 z-10 w-80 rounded-xl border border-zinc-800 bg-zinc-950/95 shadow-2xl backdrop-blur">
      <div className="flex items-start justify-between gap-3 border-b border-zinc-800/80 px-4 py-3">
        <div>
          <span
            className={`mb-1.5 inline-block rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${badgeClass}`}
          >
            {badge}
          </span>
          <h3 className="text-sm font-semibold leading-snug text-zinc-100">
            {title}
          </h3>
        </div>
        <button
          onClick={onClose}
          aria-label="Close details"
          className="rounded-md px-1.5 text-lg leading-none text-zinc-500 transition hover:text-zinc-200"
        >
          ×
        </button>
      </div>

      <div className="max-h-72 space-y-3 overflow-y-auto px-4 py-3">
        {isNode ? (
          <>
            <PropRows props={selection.node.props} />
            {selection.node.label === "Document" && (
              <DocumentBody docId={selection.node.id} personId={personId} />
            )}
          </>
        ) : (
          <>
            <div className="text-xs text-zinc-400">
              <span className="text-zinc-200">{selection.from?.caption ?? selection.rel.source}</span>
              <span className="mx-1.5 text-zinc-600">→</span>
              <span className="text-zinc-200">{selection.to?.caption ?? selection.rel.target}</span>
            </div>
            <PropRows props={selection.rel.props} />
          </>
        )}
      </div>
    </div>
  );
}
