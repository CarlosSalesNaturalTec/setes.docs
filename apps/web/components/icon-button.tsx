// Botão de ação com ícone acessível (task 10.2) — `aria-label`/`title`
// preservam o rótulo textual anterior como nome acessível, então os testes
// RTL que localizam por `getByRole("button", { name: ... })` continuam
// funcionando sem alteração.
export function IconButton({
  label,
  onClick,
  disabled,
  className = "",
  children,
}: {
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className={`inline-flex items-center justify-center rounded p-1.5 hover:bg-gray-100 disabled:opacity-50 disabled:hover:bg-transparent ${className}`}
    >
      {children}
    </button>
  );
}
