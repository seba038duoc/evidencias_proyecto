"use client";

import { useState } from "react";
import {
  uploadAuditBatch,
  confirmAuditBatchMapping,
  ApiError,
  UploadResponse,
  REQUIRED_FIELDS,
  OPTIONAL_FIELDS,
  FIELD_LABELS,
} from "@/lib/api";

/**
 * Flujo de carga de LogiSLA (Sprint 1), conectado directo a los
 * endpoints reales del backend:
 *
 *   1. El usuario sube un CSV/Excel -> POST /upload
 *   2a. Si el mapeo automático de columnas funcionó -> listo, se ve el
 *       resumen del batch (status PENDING, a la espera del Sprint 2).
 *   2b. Si el backend no pudo mapear algún campo obligatorio
 *       (status MAPPING_FAILED) -> se muestra un formulario para que el
 *       usuario indique manualmente qué columna del archivo corresponde
 *       a cada campo, usando los `available_headers` que ya vino en la
 *       respuesta. Al confirmar, se reenvía el mismo archivo a
 *       POST /upload/confirm.
 *
 * Este componente es intencionalmente autocontenido (sin librería de
 * formularios/estado) para que sea fácil de portar o fusionar con la
 * maquetación que ya tenga el equipo.
 */

type Step =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "mapping_needed"; file: File; result: UploadResponse }
  | { kind: "success"; result: UploadResponse }
  | { kind: "error"; message: string };

/* ---------------------------------------------------------------------- */
/* Iconos en línea (sin dependencias externas)                             */
/* ---------------------------------------------------------------------- */

function IconUploadCloud(props: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={props.className} aria-hidden="true">
      <path
        d="M7 18a4.5 4.5 0 01-.4-8.98A5.5 5.5 0 0117.2 8.1 4 4 0 0117 16"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M12 12v7m0-7l-2.5 2.5M12 12l2.5 2.5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IconCheckCircle(props: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={props.className} aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M8.3 12.3l2.4 2.4 5-5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IconAlertTriangle(props: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={props.className} aria-hidden="true">
      <path
        d="M12 3.5l9.3 16.1a1 1 0 01-.87 1.5H3.57a1 1 0 01-.87-1.5L12 3.5z"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <path d="M12 9.5v4.2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="12" cy="16.8" r="0.9" fill="currentColor" />
    </svg>
  );
}

function IconXCircle(props: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={props.className} aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
      <path d="M9.5 9.5l5 5m0-5l-5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function IconSpinner(props: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={`animate-spin ${props.className ?? ""}`} aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.5" opacity="0.2" />
      <path d="M21 12a9 9 0 00-9-9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

function IconFile(props: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={props.className} aria-hidden="true">
      <path
        d="M6 3.5h8l4 4V20a.5.5 0 01-.5.5h-11a.5.5 0 01-.5-.5V4a.5.5 0 01.5-.5z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M14 3.5V8h4" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

/* ---------------------------------------------------------------------- */

function StatusPanel({
  tone,
  icon,
  title,
  children,
}: {
  tone: "amber" | "emerald" | "rose";
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  const tones = {
    amber: {
      border: "border-amber-200",
      bar: "bg-amber-400",
      iconWrap: "bg-amber-100 text-amber-700",
      title: "text-amber-900",
    },
    emerald: {
      border: "border-emerald-200",
      bar: "bg-emerald-400",
      iconWrap: "bg-emerald-100 text-emerald-700",
      title: "text-emerald-900",
    },
    rose: {
      border: "border-rose-200",
      bar: "bg-rose-400",
      iconWrap: "bg-rose-100 text-rose-700",
      title: "text-rose-900",
    },
  }[tone];

  return (
    <div className={`relative overflow-hidden rounded-xl border ${tones.border} bg-white pl-5`}>
      <div className={`absolute inset-y-0 left-0 w-1 ${tones.bar}`} />
      <div className="flex items-start gap-3 px-4 py-4">
        <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${tones.iconWrap}`}>
          {icon}
        </div>
        <div className="min-w-0 flex-1 space-y-3">
          <p className={`font-semibold ${tones.title}`}>{title}</p>
          {children}
        </div>
      </div>
    </div>
  );
}

export default function UploadFlow() {
  const [companyId, setCompanyId] = useState("");
  const [step, setStep] = useState<Step>({ kind: "idle" });
  const [manualMapping, setManualMapping] = useState<Record<string, string>>({});
  const [fileName, setFileName] = useState<string | null>(null);

  async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fileInput = e.currentTarget.elements.namedItem("file") as HTMLInputElement;
    const file = fileInput.files?.[0];
    if (!file || !companyId.trim()) return;

    setStep({ kind: "loading" });
    try {
      const result = await uploadAuditBatch(companyId.trim(), file);
      if (result.status === "MAPPING_FAILED") {
        // pre-cargamos el formulario manual con lo que el auto-mapeo sí
        // logró adivinar (incluidos los ambiguos), para no partir de cero
        const seeded: Record<string, string> = { ...result.column_mapping };
        for (const [field, candidates] of Object.entries(result.ambiguous_warnings)) {
          if (candidates[0]) seeded[field] = candidates[0];
        }
        setManualMapping(seeded);
        setStep({ kind: "mapping_needed", file, result });
      } else {
        setStep({ kind: "success", result });
      }
    } catch (err) {
      setStep({ kind: "error", message: err instanceof ApiError ? err.message : String(err) });
    }
  }

  async function handleConfirmMapping() {
    if (step.kind !== "mapping_needed") return;
    const missing = REQUIRED_FIELDS.filter((f) => !manualMapping[f]);
    if (missing.length > 0) {
      setStep({
        kind: "error",
        message: `Falta asignar una columna para: ${missing.map((f) => FIELD_LABELS[f]).join(", ")}`,
      });
      return;
    }

    setStep({ kind: "loading" });
    try {
      const result = await confirmAuditBatchMapping(companyId.trim(), step.file, manualMapping);
      setStep({ kind: "success", result });
    } catch (err) {
      setStep({ kind: "error", message: err instanceof ApiError ? err.message : String(err) });
    }
  }

  function resetAll() {
    setStep({ kind: "idle" });
    setFileName(null);
  }

  const isBusy = step.kind === "loading";

  return (
    <div className="w-full max-w-xl space-y-5">
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm shadow-slate-200/60">
        <div className="border-b border-slate-100 px-6 py-5">
          <h1 className="text-xl font-semibold tracking-tight text-slate-900">
            Carga de envíos
          </h1>
          <p className="mt-1 text-sm leading-relaxed text-slate-500">
            Subí el archivo CSV o Excel con las guías del período. El sistema
            intenta reconocer las columnas automáticamente; si no logra
            identificar alguna obligatoria, te va a pedir confirmarla a mano.
          </p>
        </div>

        <div className="px-6 py-6">
          {(step.kind === "idle" || step.kind === "loading") && (
            <form onSubmit={handleUpload} className="space-y-5">
              <div>
                <label htmlFor="companyId" className="block text-sm font-medium text-slate-700">
                  Company ID
                </label>
                <input
                  id="companyId"
                  type="text"
                  value={companyId}
                  onChange={(e) => setCompanyId(e.target.value)}
                  placeholder="ID de la empresa"
                  disabled={isBusy}
                  className="mt-1.5 w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100 disabled:bg-slate-50"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700">
                  Archivo de envíos
                </label>
                <label
                  htmlFor="file"
                  className={`mt-1.5 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors ${
                    isBusy
                      ? "cursor-not-allowed border-slate-200 bg-slate-50"
                      : "border-slate-300 bg-slate-50/60 hover:border-brand-400 hover:bg-brand-50/40"
                  }`}
                >
                  {fileName ? (
                    <>
                      <IconFile className="h-7 w-7 text-brand-600" />
                      <span className="text-sm font-medium text-slate-700">{fileName}</span>
                      <span className="text-xs text-slate-400">Hacé clic para elegir otro archivo</span>
                    </>
                  ) : (
                    <>
                      <IconUploadCloud className="h-7 w-7 text-slate-400" />
                      <span className="text-sm font-medium text-slate-600">
                        Hacé clic para elegir un archivo
                      </span>
                      <span className="text-xs text-slate-400">CSV, XLSX o XLS</span>
                    </>
                  )}
                  <input
                    id="file"
                    type="file"
                    name="file"
                    accept=".csv,.xlsx,.xls"
                    disabled={isBusy}
                    onChange={(e) => setFileName(e.target.files?.[0]?.name ?? null)}
                    className="sr-only"
                    required
                  />
                </label>
              </div>

              <button
                type="submit"
                disabled={isBusy}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-800 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-900 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isBusy ? (
                  <>
                    <IconSpinner className="h-4 w-4" />
                    Subiendo…
                  </>
                ) : (
                  "Subir archivo"
                )}
              </button>
            </form>
          )}

          {step.kind === "mapping_needed" && (
            <div className="space-y-5">
              <StatusPanel
                tone="amber"
                icon={<IconAlertTriangle className="h-5 w-5" />}
                title="No pudimos reconocer todas las columnas obligatorias"
              >
                <p className="text-sm leading-relaxed text-amber-800">{step.result.message}</p>
              </StatusPanel>

              <div className="space-y-3 rounded-xl border border-slate-200 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                  Confirmá el mapeo de columnas
                </p>
                {[...REQUIRED_FIELDS, ...OPTIONAL_FIELDS].map((field) => (
                  <div key={field} className="flex items-center gap-3">
                    <label className="w-36 shrink-0 text-sm font-medium text-slate-700">
                      {FIELD_LABELS[field]}
                      {(REQUIRED_FIELDS as readonly string[]).includes(field) && (
                        <span className="text-rose-500"> *</span>
                      )}
                    </label>
                    <select
                      value={manualMapping[field] ?? ""}
                      onChange={(e) =>
                        setManualMapping((prev) => ({ ...prev, [field]: e.target.value }))
                      }
                      className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100"
                    >
                      <option value="">— sin asignar —</option>
                      {step.result.available_headers.map((h) => (
                        <option key={h} value={h}>
                          {h}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleConfirmMapping}
                  className="flex-1 rounded-lg bg-brand-800 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-900"
                >
                  Confirmar mapeo y cargar
                </button>
                <button
                  onClick={resetAll}
                  className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}

          {step.kind === "success" && (
            <StatusPanel tone="emerald" icon={<IconCheckCircle className="h-5 w-5" />} title="Carga completada">
              <p className="text-sm text-emerald-800">{step.result.message}</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2 rounded-lg bg-emerald-50/60 px-3 py-3 text-sm">
                <dt className="text-emerald-700">Batch ID</dt>
                <dd className="truncate font-mono text-xs text-emerald-900 sm:text-sm">{step.result.batch_id}</dd>
                <dt className="text-emerald-700">Filas cargadas</dt>
                <dd className="text-emerald-900">{step.result.total_rows}</dd>
              </dl>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                Pendiente de auditoría · Sprint 2
              </span>
              <div>
                <button
                  onClick={resetAll}
                  className="rounded-lg border border-emerald-300 bg-white px-3.5 py-1.5 text-sm font-medium text-emerald-800 transition-colors hover:bg-emerald-50"
                >
                  Cargar otro archivo
                </button>
              </div>
            </StatusPanel>
          )}

          {step.kind === "error" && (
            <StatusPanel tone="rose" icon={<IconXCircle className="h-5 w-5" />} title="Ocurrió un error">
              <p className="text-sm text-rose-800">{step.message}</p>
              <button
                onClick={resetAll}
                className="rounded-lg border border-rose-300 bg-white px-3.5 py-1.5 text-sm font-medium text-rose-800 transition-colors hover:bg-rose-50"
              >
                Reintentar
              </button>
            </StatusPanel>
          )}
        </div>
      </div>
    </div>
  );
}
