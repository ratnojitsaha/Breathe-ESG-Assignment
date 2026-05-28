import {
  AlertTriangle,
  BarChart3,
  Check,
  ChevronDown,
  ClipboardCheck,
  Database,
  FileDown,
  FileJson,
  FileSpreadsheet,
  HelpCircle,
  Lock,
  LogOut,
  RefreshCw,
  Settings,
  ShieldCheck,
  Upload,
  User,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  api,
  AuditLog,
  Company,
  DataSource,
  NormalizedRecord,
  RawUpload,
  Summary,
  ValidationIssue,
} from "./api/client";
import { StatusBadge } from "./components/StatusBadge";

const SOURCE_LABELS: Record<string, string> = {
  SAP_FUEL: "SAP fuel & procurement",
  UTILITY_ELECTRICITY: "Utility electricity",
  CORPORATE_TRAVEL: "Corporate travel",
};

const SOURCE_UPLOADS = [
  {
    sourceType: "SAP_FUEL",
    title: "SAP fuel & procurement",
    format: "CSV",
    accept: ".csv,text/csv",
    icon: FileSpreadsheet,
    description: "Flat-file SAP ECC/S/4 export with plant codes, posting dates, material/fuel labels, quantities, and units.",
  },
  {
    sourceType: "UTILITY_ELECTRICITY",
    title: "Utility electricity",
    format: "CSV",
    accept: ".csv,text/csv",
    icon: FileSpreadsheet,
    description: "Utility portal export with meter IDs, billing periods, kWh/MWh usage, tariff, and non-calendar cycles.",
  },
  {
    sourceType: "CORPORATE_TRAVEL",
    title: "Corporate travel",
    format: "JSON",
    accept: ".json,application/json",
    icon: FileJson,
    description: "Concur/Navan-like expense feed containing flights, hotels, and ground transport with airport codes and optional distances.",
  },
];

const SOURCE_UPLOAD_MAP = Object.fromEntries(
  SOURCE_UPLOADS.map((spec) => [spec.sourceType, spec])
) as Record<string, (typeof SOURCE_UPLOADS)[number]>;

type View = "review" | "ingest" | "reports" | "admin";

const NAV_ITEMS: Array<{ view: View; label: string; icon: typeof ClipboardCheck }> = [
  { view: "review", label: "Review", icon: ClipboardCheck },
  { view: "ingest", label: "Ingest", icon: Upload },
  { view: "reports", label: "Reports", icon: BarChart3 },
  { view: "admin", label: "Admin", icon: Database },
];

export default function App() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [companyId, setCompanyId] = useState<number | null>(null);
  const [role, setRole] = useState<"Analyst" | "Admin">("Analyst");
  const [view, setView] = useState<View>("review");
  const [sourceTab, setSourceTab] = useState("ALL");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [sources, setSources] = useState<DataSource[]>([]);
  const [uploads, setUploads] = useState<RawUpload[]>([]);
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [records, setRecords] = useState<NormalizedRecord[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [selected, setSelected] = useState<NormalizedRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const activeCompany = companies.find((company) => company.id === companyId) ?? null;
  const activeSource = sourceTab === "ALL" ? undefined : sourceTab;

  async function load(nextCompanyId = companyId, forceResetSelection = false) {
    setLoading(true);
    setError("");
    try {
      const companyPage = await api.companies();
      const allCompanies = companyPage.results;
      setCompanies(allCompanies);
      const selectedCompanyId = nextCompanyId ?? allCompanies[0]?.id ?? null;
      setCompanyId(selectedCompanyId);
      if (!selectedCompanyId) return;

      const [summaryData, sourcePage, uploadPage, issuePage, recordPage, logPage] = await Promise.all([
        api.summary(selectedCompanyId),
        api.dataSources(selectedCompanyId),
        api.uploads(selectedCompanyId),
        api.issues(selectedCompanyId),
        api.records(selectedCompanyId, undefined, activeSource),
        api.auditLogs(selectedCompanyId),
      ]);
      
      setSummary(summaryData);
      setSources(sourcePage.results);
      setUploads(uploadPage.results);
      setIssues(issuePage.results);
      
      const allRecords = recordPage.results;
      setRecords(allRecords);
      setLogs(logPage.results);

      setSelected((current) => {
        if (current && !forceResetSelection) {
          const stillExists = allRecords.find((r) => r.id === current.id);
          // If the selected record is now approved/rejected or locked, we should find a new one
          if (stillExists && !stillExists.locked_for_audit && stillExists.review_status !== "APPROVED" && stillExists.review_status !== "REJECTED") {
            return stillExists;
          }
        }
        
        // Priority selection: find the first (most recent) record that hasn't been reviewed
        return allRecords.find((r) => !r.locked_for_audit && r.review_status !== "APPROVED" && r.review_status !== "REJECTED") ?? allRecords[0] ?? null;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load platform data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    if (companyId) void load(companyId, true);
  }, [sourceTab]);

  const filteredIssues = useMemo(() => {
    if (sourceTab === "ALL") return issues;
    return issues.filter((issue) => {
      const record = records.find((item) => item.id === issue.normalized_record);
      return record?.source_type === sourceTab;
    });
  }, [issues, records, sourceTab]);

  const exceptionIssues = filteredIssues.filter(
    (issue) => issue.severity === "ERROR" || issue.severity === "WARNING"
  );
  const reviewRecords = records.filter(
    (record) => !record.locked_for_audit && record.review_status !== "APPROVED" && record.review_status !== "REJECTED"
  );
  const lockedRecords = records.filter((record) => record.locked_for_audit);

  async function review(record: NormalizedRecord, status: "APPROVED" | "REJECTED") {
    setError("");
    try {
      await api.review(
        record.id,
        status,
        status === "APPROVED" ? "Approved after analyst inspection." : "Rejected pending source correction."
      );
      setSelected(null);
      await load(companyId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit review. Please check backend connection.");
    }
  }

  function exportReport() {
    const header = ["reference", "scope", "activity", "date", "normalized_value", "unit", "status", "locked"];
    const rows = records.map((record) => [
      record.source_record_reference,
      record.scope_category,
      record.activity_category,
      record.activity_date ?? "",
      record.normalized_value ?? "",
      record.normalized_unit,
      record.review_status,
      String(record.locked_for_audit),
    ]);
    const csv = [header, ...rows]
      .map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(","))
      .join("\n");
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    link.download = `${activeCompany?.slug ?? "tenant"}-activity-report.csv`;
    link.click();
  }

  return (
    <main className="app-shell">
      <div className="app-frame">
        <header className="topbar">
          <div className="brand">
            <div className="brand-icon">
              <ShieldCheck size={22} />
            </div>
            <div>
              <div className="brand-title">{activeCompany?.name ?? "ESG Platform"}</div>
            </div>
          </div>
          <div className="topbar-right">
            <div className="topbar-icons">
              <button className="icon-pill" title="Account"><User size={18} /></button>
              <button className="icon-pill" title="Help"><HelpCircle size={18} /></button>
              <button className="icon-pill" title="Settings"><Settings size={18} /></button>
              <button className="icon-pill" title="Sign out"><LogOut size={18} /></button>
            </div>
            <div className="topbar-controls">
              <button className="icon-pill" title="Refresh tenant data" onClick={() => load(companyId)}>
                <RefreshCw size={18} />
              </button>
              <select className="control control-compact" value={role} onChange={(event) => setRole(event.target.value as "Analyst" | "Admin")}>
                <option>Analyst</option>
                <option>Admin</option>
              </select>
              <label className="org-picker">
                <span>Organization</span>
                <select
                  value={companyId ?? ""}
                  onChange={(event) => {
                    const next = Number(event.target.value);
                    setCompanyId(next);
                    void load(next);
                  }}
                >
                  {companies.map((company) => (
                    <option key={company.id} value={company.id}>
                      {company.name}
                    </option>
                  ))}
                </select>
                <ChevronDown size={16} />
              </label>
            </div>
          </div>
        </header>

        <div className="app-body">
          <aside className="sidebar">
            <div className="sidebar-section">
              <div className="sidebar-label">Navigation</div>
              <nav className="sidebar-nav">
                {NAV_ITEMS.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.view}
                      className={`sidebar-button ${view === item.view ? "sidebar-button-active" : ""}`}
                      onClick={() => setView(item.view)}
                    >
                      <Icon size={18} />
                      {item.label}
                    </button>
                  );
                })}
              </nav>
            </div>
            {summary && (
              <div className="sidebar-card">
                <span>Total records</span>
                <strong>{summary.totals.records}</strong>
                <p>{summary.totals.locked_for_audit} locked for audit</p>
              </div>
            )}
          </aside>

          <div className="app-content">
            <div className="content-inner">
              {error && <div className="banner banner-error">{error}</div>}
              {loading && <div className="banner banner-loading">Loading tenant data...</div>}

              {view === "review" && summary && companyId && (
                <ReviewView
                  summary={summary}
                  sourceTab={sourceTab}
                  setSourceTab={setSourceTab}
                  exceptionIssues={exceptionIssues}
                  records={reviewRecords}
                  selected={selected}
                  setSelected={setSelected}
                  onReview={review}
                  companyId={companyId}
                  sources={sources}
                  onUploaded={() => load(companyId)}
                />
              )}

              {view === "ingest" && activeCompany && (
                <IngestView companyId={activeCompany.id} sources={sources} uploads={uploads} onUploaded={() => load(companyId)} />
              )}

              {view === "reports" && summary && (
                <ReportsView summary={summary} records={records} lockedRecords={lockedRecords} logs={logs} onExport={exportReport} />
              )}

              {view === "admin" && (
                <AdminView role={role} companies={companies} sources={sources} uploads={uploads} logs={logs} />
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

function ReviewView({
  summary,
  sourceTab,
  setSourceTab,
  exceptionIssues,
  records,
  selected,
  setSelected,
  onReview,
  companyId,
  sources,
  onUploaded,
}: {
  summary: Summary;
  sourceTab: string;
  setSourceTab: (value: string) => void;
  exceptionIssues: ValidationIssue[];
  records: NormalizedRecord[];
  selected: NormalizedRecord | null;
  setSelected: (record: NormalizedRecord) => void;
  onReview: (record: NormalizedRecord, status: "APPROVED" | "REJECTED") => void;
  companyId: number;
  sources: DataSource[];
  onUploaded: () => void;
}) {
  return (
    <>
      <section className="mb-7">
        <h1 className="text-3xl font-bold">Review</h1>
        <p className="mt-2 text-lg text-slate-600">Ingested data from {summary.by_source.length} sources. Inspect normalization, resolve exceptions, and approve audit-ready rows.</p>
      </section>

      <div className="metric-grid">
        <Metric tone="amber" label="Needs attention" value={summary.totals.needs_attention} detail="Activity records awaiting analyst review" />
        <Metric tone="red" label="Failed at ingest" value={summary.totals.failed_at_ingest} detail="Source rows the platform could not trust" />
        <Metric tone="amber" label="Awaiting setup" value={summary.totals.awaiting_setup} detail="Missing unit, plant, meter, or travel mapping" />
        <Metric tone="blue" label="Ready to lock" value={summary.totals.ready_to_lock} detail="Approved records pending audit lock" />
        <Metric tone="green" label="Locked for audit" value={summary.totals.locked_for_audit} detail="Immutable records ready for reporting" />
      </div>

      <SourceTabs summary={summary} active={sourceTab} onChange={setSourceTab} companyId={companyId} sources={sources} onUploaded={onUploaded} />
      <ExceptionPanel issues={exceptionIssues} />

      <div className="mt-7 grid gap-6 xl:grid-cols-[1fr_420px]">
        <ReviewTable records={records} selected={selected} onSelect={setSelected} />
        <Inspector record={selected} onReview={onReview} />
      </div>
    </>
  );
}

function Metric({ label, value, detail, tone }: { label: string; value: number; detail: string; tone: "amber" | "red" | "blue" | "green" }) {
  return (
    <div className={`metric metric-${tone}`}>
      <div className="text-xs font-bold uppercase tracking-[0.12em] text-slate-600">{label}</div>
      <div className="mt-2 text-4xl font-bold">{value}</div>
      <div className="mt-2 text-sm text-slate-500">{detail}</div>
    </div>
  );
}

function SourceTabs({
  summary,
  active,
  onChange,
  companyId,
  sources,
  onUploaded,
}: {
  summary: Summary;
  active: string;
  onChange: (value: string) => void;
  companyId: number;
  sources: DataSource[];
  onUploaded: () => void;
}) {
  const totalIssues = summary.by_source.reduce((count, source) => count + source.issues, 0);
  const [uploadState, setUploadState] = useState<
    Record<string, { file: File | null; busy: boolean; message: string }>
  >({});

  function stateFor(sourceType: string) {
    return uploadState[sourceType] ?? { file: null, busy: false, message: "" };
  }

  function updateState(sourceType: string, next: Partial<{ file: File | null; busy: boolean; message: string }>) {
    setUploadState((current) => ({
      ...current,
      [sourceType]: { ...(current[sourceType] ?? { file: null, busy: false, message: "" }), ...next },
    }));
  }

  async function submit(sourceType: string) {
    const dataSource = sources.find((item) => item.source_type === sourceType);
    const state = stateFor(sourceType);
    if (!dataSource || !state.file) return;
    updateState(sourceType, { busy: true, message: "" });
    try {
      const result = await api.upload(companyId, dataSource.id, state.file);
      updateState(
        sourceType,
        {
          file: null,
          message: `Upload complete. ${result.records_total} rows ingested: ${result.records_approved} passed validation, ${result.records_needing_review} need review, ${result.records_failed} failed.`,
        }
      );
    } catch (err) {
      updateState(sourceType, { message: err instanceof Error ? err.message : "Upload failed validation" });
    } finally {
      updateState(sourceType, { busy: false });
      onUploaded();
    }
  }

  return (
    <div className="source-tabs">
      <div className="source-tab-group">
        <button className={`source-tab ${active === "ALL" ? "source-tab-active" : ""}`} onClick={() => onChange("ALL")}>
          <strong>All sources</strong>
          <span>{summary.totals.records} records / {totalIssues} issues</span>
        </button>
      </div>
      {summary.by_source.map((source) => {
        const dataSource = sources.find((item) => item.source_type === source.source_type);
        const spec = SOURCE_UPLOAD_MAP[source.source_type];
        const state = stateFor(source.source_type);
        return (
          <div key={source.source_type} className="source-tab-group">
            <button className={`source-tab ${active === source.source_type ? "source-tab-active" : ""}`} onClick={() => onChange(source.source_type)}>
              <strong>{SOURCE_LABELS[source.source_type] ?? source.name}</strong>
              <span>{source.records} records / {source.issues} issues</span>
            </button>
            <div className="source-tab-upload">
              <label className={`source-tab-file ${!dataSource || state.busy ? "source-tab-file-disabled" : ""}`}>
                <input
                  type="file"
                  accept={spec?.accept ?? ""}
                  disabled={!dataSource || state.busy}
                  onChange={(event) => updateState(source.source_type, { file: event.target.files?.[0] ?? null, message: "" })}
                />
                <span>{state.file?.name ?? `Choose ${spec?.format ?? "file"}`}</span>
              </label>
              <button
                className="source-tab-upload-button"
                disabled={!state.file || !dataSource || state.busy}
                onClick={() => submit(source.source_type)}
              >
                {state.busy ? "Uploading..." : "Upload"}
              </button>
            </div>
            {!dataSource && <div className="source-tab-message">Missing data source setup.</div>}
            {state.message && <div className="source-tab-message">{state.message}</div>}
          </div>
        );
      })}
    </div>
  );
}

function ExceptionPanel({ issues }: { issues: ValidationIssue[] }) {
  return (
    <section className="exception-panel">
      <div>
        <h2>Failed or Suspicious - {issues.length}</h2>
        <p>Each item explains why the row is blocked or flagged. Check raw data and resolve before approval.</p>
      </div>
      <div className="exception-grid">
        {issues.slice(0, 6).map((issue) => (
          <article key={issue.id} className="exception-card">
            <div className="flex items-center justify-between gap-4">
              <span className={`pill ${issue.severity === "ERROR" ? "pill-red" : "pill-amber"}`}>
                {issue.severity === "ERROR" ? "Rejected" : "Suspicious"}
              </span>
              <code>{String(issue.raw_payload?.source_document ?? issue.raw_payload?.meter_id ?? issue.raw_payload?.expense_id ?? `Raw #${issue.raw_record}`)}</code>
            </div>
            <p className="mt-4 text-base"><strong>Why it is flagged:</strong> {issue.message}</p>
            <div className="mt-4 rounded bg-white px-4 py-3">
              <strong>Next step:</strong> {nextStep(issue.code)}
            </div>
            <details className="mt-3 text-sm text-slate-600">
              <summary>Raw payload</summary>
              <pre>{JSON.stringify(issue.raw_payload, null, 2)}</pre>
            </details>
          </article>
        ))}
      </div>
    </section>
  );
}

function ReviewTable({
  records,
  selected,
  onSelect,
}: {
  records: NormalizedRecord[];
  selected: NormalizedRecord | null;
  onSelect: (record: NormalizedRecord) => void;
}) {
  return (
    <section className="data-panel">
      <div className="panel-heading">
        <div>
          <h2>Awaiting your review - {records.length}</h2>
          <p>Click a row to inspect lineage, validation, and normalized values.</p>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="review-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Scope</th>
              <th>Activity</th>
              <th>Location</th>
              <th>As reported</th>
              <th>Normalized</th>
              <th>Status</th>
              <th>Why flagged</th>
            </tr>
          </thead>
          <tbody>
            {records.map((record) => {
              const flagged = record.issues.length > 0;
              return (
                <tr key={record.id} className={`${selected?.id === record.id ? "selected-row" : ""} ${flagged ? "flagged-row" : ""}`} onClick={() => onSelect(record)}>
                  <td>{record.activity_date ?? "Unparsed"}</td>
                  <td><span className="pill pill-amber">{record.scope_category}</span></td>
                  <td><strong>{titleize(record.activity_category)}</strong><br /><span>{record.source_record_reference}</span></td>
                  <td>{record.facility_or_entity || "-"}</td>
                  <td>{record.original_value ?? "-"} {record.original_unit}</td>
                  <td>{record.normalized_value ?? "-"} {record.normalized_unit}</td>
                  <td><span className={`pill ${flagged ? "pill-amber" : "pill-muted"}`}>{flagged ? "Needs attention" : "Awaiting review"}</span></td>
                  <td>{record.issues.map((issue) => issue.message).join("; ")}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Inspector({
  record,
  onReview,
}: {
  record: NormalizedRecord | null;
  onReview: (record: NormalizedRecord, status: "APPROVED" | "REJECTED") => void;
}) {
  if (!record) {
    return <aside className="inspector"><p>Select a row to inspect normalization lineage.</p></aside>;
  }
  return (
    <aside className="inspector">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2>{titleize(record.activity_category)}</h2>
          <p>{record.source_record_reference}</p>
        </div>
        {record.locked_for_audit && <Lock className="text-emerald-700" size={20} />}
      </div>
      <div className="lineage">
        <div><span>Source</span><strong>{SOURCE_LABELS[record.source_type]}</strong></div>
        <div><span>Scope</span><strong>{record.scope_category}</strong></div>
        <div><span>Original</span><strong>{record.original_value ?? "-"} {record.original_unit}</strong></div>
        <div><span>Normalized</span><strong>{record.normalized_value ?? "-"} {record.normalized_unit}</strong></div>
      </div>
      <div className="mt-5">
        <h3>Validation</h3>
        {record.issues.length === 0 ? (
          <p className="mt-2 rounded bg-emerald-50 px-3 py-2 text-sm text-emerald-800">No blocking issues found.</p>
        ) : (
          <div className="mt-2 space-y-2">
            {record.issues.map((issue) => (
              <div key={issue.id} className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                <strong>{issue.code}</strong>: {issue.message}
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="mt-5 flex gap-3">
        <button className="action action-approve" disabled={record.locked_for_audit} onClick={() => onReview(record, "APPROVED")}><Check size={16} /> Approve</button>
        <button className="action action-reject" disabled={record.locked_for_audit} onClick={() => onReview(record, "REJECTED")}><X size={16} /> Reject</button>
      </div>
    </aside>
  );
}

function IngestView({ companyId, sources, uploads, onUploaded }: { companyId: number; sources: DataSource[]; uploads: RawUpload[]; onUploaded: () => void }) {
  return (
    <div className="space-y-6">
      <section className="data-panel">
        <div className="panel-heading">
          <div>
            <h1>Ingest source data</h1>
            <p>Upload source files into raw staging. The platform preserves each row, normalizes it, validates it, and routes exceptions into analyst review.</p>
          </div>
        </div>
        <div className="source-upload-grid">
          {SOURCE_UPLOADS.map((spec) => (
            <SourceUploadCard
              key={spec.sourceType}
              companyId={companyId}
              spec={spec}
              dataSource={sources.find((source) => source.source_type === spec.sourceType)}
              uploads={uploads.filter((upload) => upload.source_type === spec.sourceType)}
              onUploaded={onUploaded}
            />
          ))}
        </div>
      </section>
      <section className="data-panel">
        <UploadHistory uploads={uploads} />
      </section>
    </div>
  );
}

function SourceUploadCard({
  companyId,
  spec,
  dataSource,
  uploads,
  onUploaded,
}: {
  companyId: number;
  spec: (typeof SOURCE_UPLOADS)[number];
  dataSource: DataSource | undefined;
  uploads: RawUpload[];
  onUploaded: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const Icon = spec.icon;
  const latest = uploads[0];
  const selectedFileLabel = file ? file.name : `Choose ${spec.format} file`;

  async function submit() {
    if (!file || !dataSource) return;
    setBusy(true);
    setMessage("");
    try {
      const result = await api.upload(companyId, dataSource.id, file);
      setFile(null);
      setMessage(
        `Upload complete. ${result.records_total} rows ingested: ${result.records_approved} passed validation, ${result.records_needing_review} need analyst review, ${result.records_failed} failed. Next: approve or reject rows in Review before audit lock.`
      );
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Upload failed validation");
    } finally {
      setBusy(false);
      onUploaded();
    }
  }

  return (
    <article className="source-upload-card">
      <div className="flex items-start justify-between gap-4">
        <div className="flex gap-3">
          <div className="source-upload-icon"><Icon size={22} /></div>
          <div>
            <h2>{spec.title}</h2>
            <p>{spec.description}</p>
          </div>
        </div>
        <span className="pill pill-muted">{spec.format}</span>
      </div>
      <div className="mt-5 space-y-3">
        <div className="text-sm text-slate-600">
          <strong>Configured adapter:</strong> {dataSource?.name ?? "Missing data source setup"}
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
          <strong>{spec.title}</strong> requires {spec.format} upload input. After upload, the file is normalized and the resulting rows move to analyst review.
        </div>
        <input
          className="control w-full"
          type="file"
          accept={spec.accept}
          disabled={!dataSource || busy}
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        <div className="flex items-center justify-between gap-3 text-sm text-slate-600">
          <span>{selectedFileLabel}</span>
          <span>{spec.accept}</span>
        </div>
        <button className="primary-button w-full" disabled={!file || !dataSource || busy} onClick={submit}>
          <Upload size={16} />
          {busy ? "Normalizing..." : `Upload ${spec.title}`}
        </button>
        {message && <div className="upload-message">{message}</div>}
      </div>
      {latest && (
        <div className="latest-upload">
          <div className="flex items-center justify-between gap-3">
            <span>Latest upload</span>
            <StatusBadge value={latest.status} />
          </div>
          <strong>{latest.original_filename}</strong>
          <p>Uploaded {new Date(latest.uploaded_at).toLocaleString()}</p>
          <p>{latest.records_total} rows / {latest.records_approved} passed validation / {latest.records_needing_review} need review / {latest.records_failed} failed</p>
          {latest.failure_message && <p className="text-red-700">{latest.failure_message}</p>}
        </div>
      )}
    </article>
  );
}

function ReportsView({ summary, records, lockedRecords, logs, onExport }: { summary: Summary; records: NormalizedRecord[]; lockedRecords: NormalizedRecord[]; logs: AuditLog[]; onExport: () => void }) {
  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_420px]">
      <section className="data-panel">
        <div className="panel-heading">
          <div><h1>Reporting readiness</h1><p>Activity totals are normalized but not converted to CO2e. Only locked records should be used externally.</p></div>
          <button className="primary-button" onClick={onExport}><FileDown size={16} /> Export CSV</button>
        </div>
        <div className="report-grid">
          {summary.by_scope.map((scope) => (
            <div key={scope.scope_category} className="report-card">
              <span>{scope.scope_category}</span>
              <strong>{scope.records}</strong>
              <p>normalized activity records</p>
            </div>
          ))}
        </div>
        <ReviewTable records={records} selected={null} onSelect={() => undefined} />
      </section>
      <aside className="inspector">
        <h2>Audit package</h2>
        <div className="lineage">
          <div><span>Locked rows</span><strong>{lockedRecords.length}</strong></div>
          <div><span>Total rows</span><strong>{records.length}</strong></div>
          <div><span>Audit events</span><strong>{logs.length}</strong></div>
        </div>
      </aside>
    </div>
  );
}

function AdminView({ role, companies, sources, uploads, logs }: { role: string; companies: Company[]; sources: DataSource[]; uploads: RawUpload[]; logs: AuditLog[] }) {
  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <section className="data-panel">
        <div className="panel-heading"><div><h1>Tenant administration</h1><p>Current role: {role}. Tenant isolation is represented by company-scoped records and source configurations.</p></div></div>
        <div className="admin-list">
          {companies.map((company) => <div key={company.id}><Database size={18} /><strong>{company.name}</strong><span>{company.slug}</span></div>)}
        </div>
      </section>
      <section className="data-panel">
        <div className="panel-heading"><div><h1>Configured sources</h1><p>Source adapters define expected format and normalization assumptions.</p></div></div>
        <div className="admin-list">
          {sources.map((source) => <div key={source.id}><AlertTriangle size={18} /><strong>{SOURCE_LABELS[source.source_type]}</strong><span>{source.name}</span></div>)}
        </div>
      </section>
      <section className="data-panel"><UploadHistory uploads={uploads} /></section>
      <section className="data-panel"><AuditTrail logs={logs} /></section>
    </div>
  );
}

function UploadHistory({ uploads }: { uploads: RawUpload[] }) {
  return (
    <div>
      <h2>Ingestion status</h2>
      <table className="review-table compact">
        <thead><tr><th>File</th><th>Source</th><th>Status</th><th>Total</th><th>Approved</th><th>Failed</th><th>Review</th></tr></thead>
        <tbody>
          {uploads.map((upload) => (
            <tr key={upload.id}>
              <td>{upload.original_filename}</td>
              <td>{upload.data_source_name}</td>
              <td><StatusBadge value={upload.status} /></td>
              <td>{upload.records_total}</td>
              <td>{upload.records_approved}</td>
              <td>{upload.records_failed}</td>
              <td>{upload.records_needing_review}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AuditTrail({ logs }: { logs: AuditLog[] }) {
  return (
    <div>
      <h2>Audit trail</h2>
      <div className="audit-list">
        {logs.slice(0, 8).map((log) => (
          <div key={log.id}>
            <BarChart3 size={16} />
            <span>{new Date(log.created_at).toLocaleString()}</span>
            <strong>{log.action}</strong>
            <code>{log.entity_type} #{log.entity_id}</code>
          </div>
        ))}
      </div>
    </div>
  );
}

function nextStep(code: string) {
  if (code === "MISSING_UNIT") return "Add a unit mapping or request a corrected source extract before normalization.";
  if (code === "INVALID_AIRPORT_CODE") return "Correct the airport code or enrich the travel source with a valid IATA route.";
  if (code === "MISSING_DISTANCE") return "Run route-distance enrichment before approval.";
  if (code === "UNKNOWN_FUEL_TYPE") return "Map the fuel type to an approved combustion category.";
  return "Send the raw row back to the data provider, correct staging, then rerun ingestion.";
}

function titleize(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
