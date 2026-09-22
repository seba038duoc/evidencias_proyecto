/**
 * Cliente delgado para el backend de LogiSLA (Sprint 1: ingesta).
 *
 * Todo lo que expone este archivo corresponde a los dos endpoints reales
 * de app/routers/audit_batches.py del backend:
 *   POST /api/v1/audit-batches/upload
 *   POST /api/v1/audit-batches/upload/confirm
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type UploadResponse = {
  batch_id: string;
  filename: string;
  status: "PENDING" | "MAPPING_FAILED";
  total_rows: number;
  column_mapping: Record<string, string>;
  unmapped_warnings: string[];
  ambiguous_warnings: Record<string, string[]>;
  message: string;
  available_headers: string[];
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseErrorOrThrow(response: Response): Promise<never> {
  let detail = response.statusText;
  try {
    const body = await response.json();
    detail = body.detail ?? JSON.stringify(body);
  } catch {
    // el body no era JSON, usamos statusText
  }
  throw new ApiError(response.status, detail);
}

export async function uploadAuditBatch(
  companyId: string,
  file: File
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `${API_URL}/api/v1/audit-batches/upload?company_id=${encodeURIComponent(companyId)}`,
    { method: "POST", body: formData }
  );

  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

export async function confirmAuditBatchMapping(
  companyId: string,
  file: File,
  columnMapping: Record<string, string>
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("column_mapping", JSON.stringify(columnMapping));

  const response = await fetch(
    `${API_URL}/api/v1/audit-batches/upload/confirm?company_id=${encodeURIComponent(companyId)}`,
    { method: "POST", body: formData }
  );

  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

// Campos internos que el backend espera (app/column_mapping.py).
// Se duplica aquí (en vez de pedirlos a la API) porque son estáticos y
// así el formulario de mapeo manual se puede pintar sin un round-trip extra.
export const REQUIRED_FIELDS = ["guide_number", "carrier_name", "dispatch_date"] as const;
export const OPTIONAL_FIELDS = ["delivery_date", "destination", "declared_value"] as const;

export const FIELD_LABELS: Record<string, string> = {
  guide_number: "N° de Guía",
  carrier_name: "Transportista",
  dispatch_date: "Fecha de Despacho",
  delivery_date: "Fecha de Entrega",
  destination: "Destino",
  declared_value: "Valor Declarado",
};
