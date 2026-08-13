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

// Marca institucional (D1/D2/D4, change marca-visual-despapelize) — símbolo da
// árvore com raízes de circuito da Despapelize, redesenhado à mão a partir de
// docs/images/logo_despapelize.jpeg. Monocromático em `currentColor`: o chip
// circular do Login e da sidebar já provê o fundo, o desenho herda a cor do
// contexto. Mesmas formas em `app/icon.svg` (favicon, D4) — ao editar um,
// editar o outro.
export function IconMarca({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 32 32" fill="currentColor" className={`h-6 w-6 ${className}`} aria-hidden>
      <circle cx="16" cy="12" r="7.5" />
      <path d="M14.3 19.5h3.4v3h-3.4z" />
      <g stroke="currentColor" strokeWidth={1.3} strokeLinecap="round" strokeLinejoin="round" fill="none">
        <path d="M16 22.5 13 24.5 10 26.5" />
        <path d="M16 22.5 14 26.5" />
        <path d="M16 22.5v5" />
        <path d="M16 22.5 18 26.5" />
        <path d="M16 22.5 19 24.5 22 26.5" />
      </g>
      <circle cx="16" cy="22.5" r="0.9" />
      <circle cx="10" cy="26.5" r="1.05" />
      <circle cx="14" cy="26.5" r="1.05" />
      <circle cx="16" cy="27.5" r="1.05" />
      <circle cx="18" cy="26.5" r="1.05" />
      <circle cx="22" cy="26.5" r="1.05" />
    </svg>
  );
}

// Ícones de navegação da sidebar (restyle-apresentacao-v1) — mesmo padrão
// inline, 18–20px, `currentColor`.
const NAV_BASE = "h-5 w-5";

export function IconPainel({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${NAV_BASE} ${className}`} aria-hidden>
      <rect x="3" y="3" width="8" height="8" rx="1.5" />
      <rect x="13" y="3" width="8" height="5" rx="1.5" />
      <rect x="13" y="10" width="8" height="11" rx="1.5" />
      <rect x="3" y="13" width="8" height="8" rx="1.5" />
    </svg>
  );
}

export function IconProcessos({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${NAV_BASE} ${className}`} aria-hidden>
      <path d="M4 6a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconNovoProcesso({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${NAV_BASE} ${className}`} aria-hidden>
      <path d="M4 6a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 10v6M9 13h6" strokeLinecap="round" />
    </svg>
  );
}

export function IconConsultaPublica({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${NAV_BASE} ${className}`} aria-hidden>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3c2.5 2.5 4 6 4 9s-1.5 6.5-4 9c-2.5-2.5-4-6-4-9s1.5-6.5 4-9Z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconRelatorios({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${NAV_BASE} ${className}`} aria-hidden>
      <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconUsuarios({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${NAV_BASE} ${className}`} aria-hidden>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M3 20c0-3.5 2.7-6 6-6s6 2.5 6 6" strokeLinecap="round" />
      <circle cx="17.5" cy="9.5" r="2.5" />
      <path d="M21 20c0-2.8-1.8-5-4.5-5.8" strokeLinecap="round" />
    </svg>
  );
}

export function IconPerfil({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${NAV_BASE} ${className}`} aria-hidden>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 20c0-4.4 3.6-7 8-7s8 2.6 8 7" strokeLinecap="round" />
    </svg>
  );
}

export function IconTiposProcesso({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${NAV_BASE} ${className}`} aria-hidden>
      <path d="M6 4h9l3 3v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 12h6M9 16h6" strokeLinecap="round" />
    </svg>
  );
}

export function IconLgpd({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${NAV_BASE} ${className}`} aria-hidden>
      <path d="M12 3l7 3v6c0 4.5-3 8-7 9-4-1-7-4.5-7-9V6Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 8v4M12 15h.01" strokeLinecap="round" />
    </svg>
  );
}

export function IconDocumentos({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${NAV_BASE} ${className}`} aria-hidden>
      <path d="M7 3h7l4 4v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 12h6M9 16h6M9 8h2" strokeLinecap="round" />
    </svg>
  );
}

export function IconEnvelope({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${NAV_BASE} ${className}`} aria-hidden>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m4 7 8 6 8-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconCadeado({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${NAV_BASE} ${className}`} aria-hidden>
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" strokeLinecap="round" />
    </svg>
  );
}

export function IconMenu({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${NAV_BASE} ${className}`} aria-hidden>
      <path d="M3 6h18M3 12h18M3 18h18" strokeLinecap="round" />
    </svg>
  );
}

export function IconFechar({ className = "" }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={`${NAV_BASE} ${className}`} aria-hidden>
      <path d="M6 6l12 12M18 6 6 18" strokeLinecap="round" />
    </svg>
  );
}
