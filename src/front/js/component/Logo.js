// Mark: a circle (Bagua circle walking) with a flowing S-curve — movement + code.
export function Logo({ className }) {
  return (
    <svg className={className} viewBox="0 0 64 64" aria-hidden="true" focusable="false">
      <circle cx="32" cy="32" r="30" fill="#1f4e5f" />
      <circle cx="32" cy="32" r="21" fill="none" stroke="#f3c969" strokeWidth="3" />
      <path d="M32 11a10.5 10.5 0 0 1 0 21 10.5 10.5 0 0 0 0 21" fill="none" stroke="#fff" strokeWidth="3" />
      <circle cx="32" cy="21.5" r="3" fill="#fff" />
      <circle cx="32" cy="42.5" r="3" fill="#f3c969" />
    </svg>
  );
}

// Decorative Bagua motif: the walking circle with eight stations (the eight trigram
// directions) and a flowing path around it. Colors come from `currentColor`.
export function BaguaMotif({ className }) {
  const stations = Array.from({ length: 8 }, (_, i) => {
    const a = (i * Math.PI) / 4;
    return [100 + 72 * Math.cos(a), 100 + 72 * Math.sin(a)];
  });
  return (
    <svg className={className} viewBox="0 0 200 200" aria-hidden="true" focusable="false">
      <circle cx="100" cy="100" r="92" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.5" />
      <circle cx="100" cy="100" r="72" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="3 7" strokeLinecap="round" />
      <circle cx="100" cy="100" r="52" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.5" />
      <path d="M100 48a26 26 0 0 1 0 52 26 26 0 0 0 0 52" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.6" />
      {stations.map(([x, y]) => <circle key={`${x}-${y}`} cx={x} cy={y} r="4" fill="currentColor" />)}
    </svg>
  );
}
