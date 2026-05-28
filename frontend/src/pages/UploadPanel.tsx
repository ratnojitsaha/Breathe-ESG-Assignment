import { Upload } from "lucide-react";
import { useState } from "react";
import { api, DataSource } from "../api/client";

export function UploadPanel({
  companyId,
  dataSources,
  onUploaded,
}: {
  companyId: number;
  dataSources: DataSource[];
  onUploaded: () => void;
}) {
  const [sourceId, setSourceId] = useState(dataSources[0]?.id ?? 0);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!file || !sourceId) return;
    setBusy(true);
    try {
      await api.upload(companyId, sourceId, file);
      setFile(null);
      onUploaded();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto]">
      <select className="h-10 rounded border border-stone-300 bg-white px-3" value={sourceId} onChange={(e) => setSourceId(Number(e.target.value))}>
        {dataSources.map((source) => (
          <option key={source.id} value={source.id}>
            {source.name}
          </option>
        ))}
      </select>
      <input className="h-10 rounded border border-stone-300 bg-white px-3 py-2" type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      <button className="inline-flex h-10 items-center gap-2 rounded bg-slate-900 px-4 text-sm font-medium text-white" disabled={!file || busy} onClick={submit}>
        <Upload size={16} />
        Upload
      </button>
    </div>
  );
}
