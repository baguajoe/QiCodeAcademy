// Simple SVG illustrations in each division's colors. Every diagram has a wide
// layout (tablets/desktop) and a stacked layout (phones) so text stays readable,
// plus <title>/<desc> so screen readers get the full content.
import { useId } from "react";

function wrap(text, max) {
  const words = String(text).split(/\s+/);
  const lines = [];
  let line = "";
  words.forEach((w) => {
    if ((line + " " + w).trim().length > max && line) {
      lines.push(line);
      line = w;
    } else line = (line + " " + w).trim();
  });
  if (line) lines.push(line);
  return lines;
}

function Lines({ x, y, lines, lineHeight = 22, anchor = "middle", className = "dg-label", ...rest }) {
  return (
    <text x={x} y={y} textAnchor={anchor} className={className} {...rest}>
      {lines.map((l, i) => (
        <tspan key={i} x={x} dy={i === 0 ? 0 : lineHeight}>{l}</tspan>
      ))}
    </text>
  );
}

function Svg({ viewBox, title, desc, children, className = "" }) {
  const id = useId();
  return (
    <svg viewBox={viewBox} role="img" aria-labelledby={`${id}-t ${id}-d`} className={className} preserveAspectRatio="xMidYMid meet">
      <title id={`${id}-t`}>{title}</title>
      <desc id={`${id}-d`}>{desc}</desc>
      {children}
    </svg>
  );
}

function Arrowhead({ id, className = "dg-arrowhead" }) {
  return (
    <defs>
      <marker id={id} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0 0L10 5L0 10z" className={className} />
      </marker>
    </defs>
  );
}

// ---------------------------------------------------------------------------
// Numbered steps: horizontal on wide screens, vertical on phones.
// ---------------------------------------------------------------------------
function StepsWide({ steps, title, desc, startNote }) {
  const arrowId = useId().replace(/:/g, "");
  // Spread steps across ~1000 units so fewer, longer steps get wider label columns.
  const gap = Math.max(150, Math.floor(860 / Math.max(steps.length - 1, 1)));
  const chars = Math.max(13, Math.floor(gap / 10.5));
  const wrapped = steps.map((s) => wrap(s, chars));
  const maxLines = Math.max(...wrapped.map((l) => l.length));
  const pad = Math.max(80, Math.ceil(chars * 5.4));
  const w = pad + gap * (steps.length - 1) + pad;
  const cy = startNote ? 110 : 80;
  const h = cy + 66 + maxLines * 22 + 16;
  return (
    <Svg viewBox={`0 0 ${w} ${h}`} title={title} desc={desc} className="diagram-wide">
      <Arrowhead id={arrowId} />
      {startNote && <Lines x={pad - 40} y={36} lines={[startNote]} anchor="start" className="dg-note" />}
      {startNote && <path d={`M${pad} 46 V${cy - 44}`} className="dg-line" markerEnd={`url(#${arrowId})`} />}
      {steps.slice(0, -1).map((_, i) => (
        <path key={i} d={`M${pad + gap * i + 42} ${cy} H${pad + gap * (i + 1) - 46}`} className="dg-line" markerEnd={`url(#${arrowId})`} />
      ))}
      {steps.map((s, i) => {
        const x = pad + gap * i;
        const last = i === steps.length - 1;
        return (
          <g key={s}>
            <circle cx={x} cy={cy} r="36" className={last ? "dg-node dg-node-final" : "dg-node"} />
            <text x={x} y={cy + 8} textAnchor="middle" className={last ? "dg-num dg-num-final" : "dg-num"}>{i + 1}</text>
            <Lines x={x} y={cy + 66} lines={wrapped[i]} />
          </g>
        );
      })}
    </Svg>
  );
}

function StepsNarrow({ steps, title, desc, startNote }) {
  const arrowId = useId().replace(/:/g, "");
  const step = 92;
  const top = startNote ? 70 : 40;
  const h = top + step * (steps.length - 1) + 60;
  return (
    <Svg viewBox={`0 0 360 ${h}`} title={title} desc={desc} className="diagram-narrow">
      <Arrowhead id={arrowId} />
      {startNote && <Lines x={16} y={30} lines={[startNote]} anchor="start" className="dg-note" />}
      {steps.slice(0, -1).map((_, i) => (
        <path key={i} d={`M44 ${top + step * i + 30} V${top + step * (i + 1) - 34}`} className="dg-line" markerEnd={`url(#${arrowId})`} />
      ))}
      {steps.map((s, i) => {
        const y = top + step * i;
        const last = i === steps.length - 1;
        const lines = wrap(s, 22);
        return (
          <g key={s}>
            <circle cx="44" cy={y} r="28" className={last ? "dg-node dg-node-final" : "dg-node"} />
            <text x="44" y={y + 7} textAnchor="middle" className={last ? "dg-num dg-num-final" : "dg-num"}>{i + 1}</text>
            <Lines x={88} y={y + 7 - ((lines.length - 1) * 11)} lines={lines} anchor="start" className="dg-label dg-label-lg" />
          </g>
        );
      })}
    </Svg>
  );
}

export function StepsDiagram({ steps, title, startNote, motif, division, caption }) {
  const desc = `${startNote ? startNote + ". " : ""}${steps.map((s, i) => `${i + 1}. ${s}`).join(" ")}`;
  return (
    <figure className={`diagram theme-${division}`} style={{ margin: 0 }}>
      <StepsWide steps={steps} title={title} desc={desc} startNote={startNote} />
      <StepsNarrow steps={steps} title={title} desc={desc} startNote={startNote} />
      {caption && <figcaption className="diagram-caption">{caption}</figcaption>}
    </figure>
  );
}

// ---------------------------------------------------------------------------
// Senior session flow: steps around a circle (echoing Bagua circle walking).
// ---------------------------------------------------------------------------
export function SessionFlowDiagram({ steps, title, centerLabel, caption }) {
  const arrowId = useId().replace(/:/g, "");
  const desc = steps.map((s, i) => `${i + 1}. ${s}`).join(" ");
  const cx = 340, cy = 330, R = 225, r = 76;
  const pts = steps.map((_, i) => {
    const a = (-90 + (360 / steps.length) * i) * (Math.PI / 180);
    return [cx + R * Math.cos(a), cy + R * Math.sin(a), a];
  });
  const arc = (a1, a2) => {
    const pad = 0.36; // radians trimmed so arrows don't overlap the nodes
    const s = a1 + pad, e = a2 - pad;
    return `M${cx + R * Math.cos(s)} ${cy + R * Math.sin(s)} A${R} ${R} 0 0 1 ${cx + R * Math.cos(e)} ${cy + R * Math.sin(e)}`;
  };
  return (
    <figure className="diagram theme-senior" style={{ margin: 0 }}>
      <Svg viewBox="0 0 680 660" title={title} desc={desc} className="diagram-wide diagram-square">
        <Arrowhead id={arrowId} />
        <circle cx={cx} cy={cy} r={R} className="dg-orbit" />
        <circle cx={cx} cy={cy} r={R - 34} className="dg-orbit dg-orbit-inner" />
        {pts.map((p, i) => {
          const next = pts[(i + 1) % pts.length];
          const a2 = next[2] + (i === pts.length - 1 ? 2 * Math.PI : 0);
          return <path key={i} d={arc(p[2], a2)} className="dg-line" markerEnd={`url(#${arrowId})`} fill="none" />;
        })}
        <Lines x={cx} y={cy - 4} lines={wrap(centerLabel, 14)} className="dg-center" lineHeight={30} />
        {pts.map(([x, y], i) => {
          const lines = wrap(steps[i], 12);
          return (
            <g key={steps[i]}>
              <circle cx={x} cy={y} r={r} className={i % 2 ? "dg-node dg-node-alt" : "dg-node"} />
              <Lines x={x} y={y + 6 - ((lines.length - 1) * 10)} lines={lines} className="dg-in" lineHeight={20} />
            </g>
          );
        })}
      </Svg>
      <StepsNarrow steps={steps} title={title} desc={desc} />
      {caption && <figcaption className="diagram-caption">{caption}</figcaption>}
    </figure>
  );
}

// ---------------------------------------------------------------------------
// Research partnership: two columns meeting in a shared study.
// ---------------------------------------------------------------------------
function Panel({ x, y, w, title, items, variant, h }) {
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx="18" className={`dg-panel ${variant}`} />
      <rect x={x} y={y} width={w} height="58" rx="18" className={`dg-panel-head ${variant}`} />
      <rect x={x} y={y + 40} width={w} height="18" className={`dg-panel-head ${variant}`} />
      <text x={x + 22} y={y + 38} className="dg-panel-title">{title}</text>
      {items.map((it, i) => (
        <g key={it}>
          <circle cx={x + 30} cy={y + 94 + i * 42} r="6" className={`dg-bullet ${variant}`} />
          <text x={x + 48} y={y + 100 + i * 42} className="dg-label dg-label-lg">{it}</text>
        </g>
      ))}
    </g>
  );
}

export function PartnershipDiagram({ leftTitle, left, rightTitle, right, title, centerLabel, caption }) {
  const desc = `${leftTitle}: ${left.join(", ")}. ${rightTitle}: ${right.join(", ")}.`;
  const rows = Math.max(left.length, right.length);
  const h = 90 + rows * 42 + 20;
  return (
    <figure className="diagram theme-research" style={{ margin: 0 }}>
      <Svg viewBox={`0 0 960 ${h + 20}`} title={title} desc={desc} className="diagram-wide">
        <Panel x={10} y={10} w={380} h={h} title={leftTitle} items={left} variant="dg-qca" />
        <Panel x={570} y={10} w={380} h={h} title={rightTitle} items={right} variant="dg-partner" />
        <circle cx="480" cy={10 + h / 2} r="78" className="dg-study" />
        <circle cx="480" cy={10 + h / 2} r="92" className="dg-orbit" />
        <Lines x={480} y={10 + h / 2 - 6} lines={wrap(centerLabel, 12)} className="dg-in" lineHeight={24} />
      </Svg>
      <Svg viewBox={`0 0 360 ${2 * h + 170}`} title={title} desc={desc} className="diagram-narrow">
        <Panel x={4} y={4} w={352} h={h} title={leftTitle} items={left} variant="dg-qca" />
        <circle cx="180" cy={h + 84} r="62" className="dg-study" />
        <Lines x={180} y={h + 80} lines={wrap(centerLabel, 12)} className="dg-in" lineHeight={22} />
        <Panel x={4} y={h + 162} w={352} h={h} title={rightTitle} items={right} variant="dg-partner" />
      </Svg>
      {caption && <figcaption className="diagram-caption">{caption}</figcaption>}
    </figure>
  );
}
