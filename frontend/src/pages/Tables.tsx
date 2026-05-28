import { Check, Lock, X } from "lucide-react";
import { api, AuditLog, NormalizedRecord, RawUpload, ValidationIssue } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";

export function UploadTable({ uploads }: { uploads: RawUpload[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b text-xs uppercase text-slate-500">
          <tr><th className="py-2">File</th><th>Source</th><th>Status</th><th>Total</th><th>Failed</th><th>Review</th></tr>
        </thead>
        <tbody>
          {uploads.map((u) => (
            <tr key={u.id} className="border-b border-stone-100">
              <td className="py-3 font-medium">{u.original_filename}</td>
              <td>{u.data_source_name}</td>
              <td><StatusBadge value={u.status} /></td>
              <td>{u.records_total}</td>
              <td>{u.records_failed}</td>
              <td>{u.records_needing_review}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function IssueTable({ issues }: { issues: ValidationIssue[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b text-xs uppercase text-slate-500">
          <tr><th className="py-2">Severity</th><th>Code</th><th>Field</th><th>Message</th></tr>
        </thead>
        <tbody>
          {issues.map((issue) => (
            <tr key={issue.id} className="border-b border-stone-100">
              <td className="py-3"><StatusBadge value={issue.severity} /></td>
              <td className="font-mono text-xs">{issue.code}</td>
              <td>{issue.field || "-"}</td>
              <td>{issue.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ReviewTable({ records, onChanged }: { records: NormalizedRecord[]; onChanged: () => void }) {
  async function act(id: number, status: "APPROVED" | "REJECTED") {
    await api.review(id, status, status === "APPROVED" ? "Analyst accepted source row." : "Analyst rejected row.");
    onChanged();
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b text-xs uppercase text-slate-500">
          <tr><th className="py-2">Reference</th><th>Scope</th><th>Activity</th><th>Value</th><th>Status</th><th>Audit</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr key={record.id} className="border-b border-stone-100">
              <td className="py-3 font-medium">{record.source_record_reference}</td>
              <td>{record.scope_category}</td>
              <td>{record.activity_category}</td>
              <td>{record.normalized_value ?? "-"} {record.normalized_unit}</td>
              <td><StatusBadge value={record.review_status} /></td>
              <td>{record.locked_for_audit ? <Lock size={16} className="text-emerald-700" /> : "-"}</td>
              <td className="flex gap-2 py-2">
                <button title="Approve" className="rounded border border-emerald-300 p-2 text-emerald-700" disabled={record.locked_for_audit} onClick={() => act(record.id, "APPROVED")}><Check size={16} /></button>
                <button title="Reject" className="rounded border border-rose-300 p-2 text-rose-700" disabled={record.locked_for_audit} onClick={() => act(record.id, "REJECTED")}><X size={16} /></button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AuditTable({ logs }: { logs: AuditLog[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b text-xs uppercase text-slate-500">
          <tr><th className="py-2">Time</th><th>Action</th><th>Entity</th><th>After</th></tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id} className="border-b border-stone-100">
              <td className="py-3">{new Date(log.created_at).toLocaleString()}</td>
              <td>{log.action}</td>
              <td>{log.entity_type} #{log.entity_id}</td>
              <td className="font-mono text-xs">{JSON.stringify(log.after)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
