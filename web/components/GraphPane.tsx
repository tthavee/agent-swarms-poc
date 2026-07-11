"use client";

import { useEffect, useMemo, useRef } from "react";
import { InteractiveNvlWrapper } from "@neo4j-nvl/react";
import type NVL from "@neo4j-nvl/base";
import type { Node, Relationship } from "@neo4j-nvl/base";
import type { GraphPayload } from "@/lib/api";

const LABEL_COLORS: Record<string, string> = {
  Team: "#f59e0b",
  Person: "#38bdf8",
  Process: "#a78bfa",
  System: "#64748b",
  Regulation: "#f472b6",
};

const LABEL_SIZES: Record<string, number> = {
  Team: 42,
  Person: 26,
  Process: 34,
  System: 22,
  Regulation: 30,
  Document: 20,
};

const DOC_ACCESSIBLE = "#34d399";
const DOC_DENIED = "#7f1d1d";

const LEGEND = [
  ["Team", LABEL_COLORS.Team],
  ["Person", LABEL_COLORS.Person],
  ["Process", LABEL_COLORS.Process],
  ["Regulation", LABEL_COLORS.Regulation],
  ["System", LABEL_COLORS.System],
  ["Doc · readable", DOC_ACCESSIBLE],
  ["Doc · no access", DOC_DENIED],
] as const;

export default function GraphPane({
  graph,
  highlighted,
  personName,
}: {
  graph: GraphPayload | null;
  highlighted: Set<string>;
  personName: string;
}) {
  const { nodes, rels } = useMemo(() => {
    if (!graph) return { nodes: [] as Node[], rels: [] as Relationship[] };
    const nodes: Node[] = graph.nodes.map((n) => {
      const isDoc = n.label === "Document";
      const cited = highlighted.has(n.id);
      return {
        id: n.id,
        captions: [{ value: n.caption }],
        color: isDoc
          ? n.accessible
            ? DOC_ACCESSIBLE
            : DOC_DENIED
          : LABEL_COLORS[n.label] ?? "#94a3b8",
        size: (LABEL_SIZES[n.label] ?? 24) * (cited ? 1.7 : 1),
        selected: cited,
      };
    });
    const rels: Relationship[] = graph.relationships.map((r) => ({
      id: r.id,
      from: r.source,
      to: r.target,
      captions: [{ value: r.type }],
      color: "#3f3f46",
    }));
    return { nodes, rels };
  }, [graph, highlighted]);

  const nvlRef = useRef<NVL>(null);
  const nodeCount = graph?.nodes.length ?? 0;

  // Fit the viewport once the force layout has spread the nodes.
  useEffect(() => {
    if (!nodeCount) return;
    const ids = graph!.nodes.map((n) => n.id);
    const timers = [800, 2000].map((ms) =>
      setTimeout(() => nvlRef.current?.fit?.(ids, {}), ms),
    );
    return () => timers.forEach(clearTimeout);
  }, [nodeCount]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="relative h-full w-full">
      {graph ? (
        <InteractiveNvlWrapper
          ref={nvlRef}
          nodes={nodes}
          rels={rels}
          layout="d3Force"
          nvlOptions={{
            renderer: "canvas",
            layout: "d3Force",
          }}
          mouseEventCallbacks={{ onZoom: true, onDrag: true, onPan: true }}
        />
      ) : (
        <div className="flex h-full items-center justify-center text-zinc-500">
          loading graph…
        </div>
      )}

      {/* legend */}
      <div className="pointer-events-none absolute bottom-4 left-4 hidden rounded-xl border border-zinc-800 bg-zinc-950/80 px-4 py-3 text-xs backdrop-blur lg:block">
        <div className="mb-2 font-medium text-zinc-300">
          Access view · {personName}
        </div>
        <div className="grid grid-cols-2 gap-x-5 gap-y-1.5">
          {LEGEND.map(([label, color]) => (
            <div key={label} className="flex items-center gap-2 text-zinc-400">
              <span
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: color }}
              />
              {label}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
