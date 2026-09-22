import { LogoWordmark } from "@/components/Logo";

/**
 * Cabecera fija del sitio. Deliberadamente simple y seria — una franja
 * azul marino con la marca y una línea de contexto, sin navegación (el
 * Sprint 1 solo tiene esta pantalla).
 */
export function SiteHeader() {
  return (
    <header className="border-b border-brand-950/10 bg-brand-950 text-white">
      <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
        <LogoWordmark />
        <span className="hidden text-xs font-medium uppercase tracking-wider text-brand-200/70 sm:inline">
          Auditoría de SLA · Transporte
        </span>
      </div>
    </header>
  );
}
