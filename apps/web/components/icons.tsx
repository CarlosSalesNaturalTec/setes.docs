// Ícones inline (sem dependência externa) para as ações das tabelas de admin
// (task 10.2) — 18x18, `currentColor`, para herdar a cor do botão.
type IconProps = { className?: string };

const BASE = "h-[18px] w-[18px]";

export function IconEdit({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${BASE} ${className}`} aria-hidden>
      <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconPowerOff({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${BASE} ${className}`} aria-hidden>
      <path d="M12 3v7" strokeLinecap="round" />
      <path d="M6.3 6.3a9 9 0 1 0 11.4 0" strokeLinecap="round" />
    </svg>
  );
}

export function IconPowerOn({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${BASE} ${className}`} aria-hidden>
      <circle cx="12" cy="12" r="9" />
      <path d="M9 12l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconTransfer({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${BASE} ${className}`} aria-hidden>
      <path d="M4 7h13l-3-3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M20 17H7l3 3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconBuildings({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${BASE} ${className}`} aria-hidden>
      <path d="M4 21V6l6-3v18" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M14 21V10l6 2v9" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M4 21h16" strokeLinecap="round" />
    </svg>
  );
}

export function IconKey({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${BASE} ${className}`} aria-hidden>
      <circle cx="8" cy="15" r="4" />
      <path d="M11 12l8-8" strokeLinecap="round" />
      <path d="M16 7l2 2M18.5 4.5l2 2" strokeLinecap="round" />
    </svg>
  );
}

export function IconShield({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${BASE} ${className}`} aria-hidden>
      <path d="M12 3l7 3v6c0 4.5-3 8-7 9-4-1-7-4.5-7-9V6Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 12l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconUserMinus({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${BASE} ${className}`} aria-hidden>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M3 20c0-3.5 2.7-6 6-6s6 2.5 6 6" strokeLinecap="round" />
      <path d="M17 11h5" strokeLinecap="round" />
    </svg>
  );
}
