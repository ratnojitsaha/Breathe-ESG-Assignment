const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export type Company = { id: number; name: string; slug: string };
export type DataSource = { id: number; company: number; source_type: string; name: string };
export type Summary = {
  company: Company;
  totals: {
    records: number;
    needs_attention: number;
    failed_at_ingest: number;
    awaiting_setup: number;
    ready_to_lock: number;
    locked_for_audit: number;
    uploads: number;
  };
  by_source: Array<{
    source_type: string;
    name: string;
    records: number;
    issues: number;
    errors: number;
    warnings: number;
    locked: number;
  }>;
  by_scope: Array<{ scope_category: string; records: number; activity_total: string | null }>;
  recent_uploads: RawUpload[];
};
export type RawUpload = {
  id: number;
  company: number;
  data_source_name: string;
  source_type: string;
  original_filename: string;
  uploaded_at: string;
  status: string;
  records_total: number;
  records_failed: number;
  records_needing_review: number;
  records_approved: number;
  failure_message: string;
};
export type ValidationIssue = {
  id: number;
  raw_record: number;
  normalized_record: number | null;
  severity: string;
  code: string;
  message: string;
  field: string;
  raw_payload: Record<string, unknown>;
};
export type NormalizedRecord = {
  id: number;
  source_type: string;
  activity_category: string;
  scope_category: string;
  original_unit: string;
  normalized_unit: string;
  original_value: string | null;
  normalized_value: string | null;
  activity_date: string | null;
  source_record_reference: string;
  facility_or_entity: string;
  review_status: string;
  locked_for_audit: boolean;
  issues: ValidationIssue[];
};
export type AuditLog = {
  id: number;
  action: string;
  entity_type: string;
  entity_id: string;
  after: Record<string, unknown> | null;
  created_at: string;
};

type Page<T> = { count: number; results: T[] };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const text = await response.text();
    let message = text || response.statusText;
    try {
      const payload = JSON.parse(text);
      message = payload.detail ?? payload.failure_message ?? JSON.stringify(payload);
    } catch {
      message = text || response.statusText;
    }
    throw new Error(message);
  }
  return response.json();
}

export const api = {
  companies: () => request<Page<Company>>("/companies/"),
  summary: (companyId: number) => request<Summary>(`/companies/${companyId}/summary/`),
  dataSources: (companyId: number) => request<Page<DataSource>>(`/data-sources/?company=${companyId}`),
  uploads: (companyId: number) => request<Page<RawUpload>>(`/uploads/?company=${companyId}`),
  issues: (companyId: number, severity?: string) =>
    request<Page<ValidationIssue>>(`/validation-issues/?company=${companyId}${severity ? `&severity=${severity}` : ""}`),
  records: (companyId: number, reviewStatus?: string, sourceType?: string) =>
    request<Page<NormalizedRecord>>(
      `/normalized-records/?company=${companyId}${reviewStatus ? `&review_status=${reviewStatus}` : ""}${
        sourceType ? `&source_type=${sourceType}` : ""
      }`
    ),
  auditLogs: (companyId: number) => request<Page<AuditLog>>(`/audit-logs/?company=${companyId}`),
  upload: (companyId: number, dataSourceId: number, file: File) => {
    const form = new FormData();
    form.append("company", String(companyId));
    form.append("data_source", String(dataSourceId));
    form.append("file", file);
    return request<RawUpload>("/uploads/upload/", { method: "POST", body: form });
  },
  review: (recordId: number, status: "APPROVED" | "REJECTED", comment: string) =>
    request<NormalizedRecord>(`/normalized-records/${recordId}/review/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status, comment }),
    }),
};
