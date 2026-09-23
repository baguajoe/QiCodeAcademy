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
