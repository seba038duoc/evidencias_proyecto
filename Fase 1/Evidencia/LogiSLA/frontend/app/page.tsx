import UploadFlow from "@/components/UploadFlow";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center px-4 py-10 sm:py-14">
      <UploadFlow />
      <footer className="mt-10 text-center text-xs text-slate-400">
        LogiSLA · Sprint 1 — Ingesta y mapeo de guías · el cálculo de
        cumplimiento de SLA llega en el Sprint 2
      </footer>
    </main>
  );
}
