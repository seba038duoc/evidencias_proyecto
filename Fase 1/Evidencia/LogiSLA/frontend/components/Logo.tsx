/**
 * Isotipo simple de LogiSLA: un escudo con un check, representando
 * "auditoría / cumplimiento". Es un SVG en línea (sin dependencias) para
 * que quede liviano y fácil de recolorear con currentColor.
 */
export function LogoMark({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <path
        d="M12 2.5l7.5 2.8v5.4c0 4.8-3.2 8.9-7.5 10.3-4.3-1.4-7.5-5.5-7.5-10.3V5.3L12 2.5z"
        fill="currentColor"
        fillOpacity="0.12"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path
        d="M8.3 12.2l2.4 2.4 5-5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function LogoWordmark({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <LogoMark />
      <span className="text-lg font-semibold tracking-tight">
        Logi<span className="font-bold">SLA</span>
      </span>
    </span>
  );
}
