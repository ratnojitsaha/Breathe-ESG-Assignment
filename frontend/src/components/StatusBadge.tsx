const colors: Record<string, string> = {
  PROCESSED: "bg-[#e7efd7] text-[#3f5a3f]",
  FAILED: "bg-[#f3dede] text-[#8a3b3b]",
  PENDING: "bg-[#f2f1ea] text-[#6b7462]",
  NEEDS_REVIEW: "bg-[#fbf4dd] text-[#8a6d2d]",
  APPROVED: "bg-[#dbe7c6] text-[#3a5a3a]",
  REJECTED: "bg-[#f3dede] text-[#8a3b3b]",
  WARNING: "bg-[#fbf4dd] text-[#8a6d2d]",
  ERROR: "bg-[#f3dede] text-[#8a3b3b]",
};

export function StatusBadge({ value }: { value: string }) {
  return (
    <span className={`inline-flex rounded px-2 py-1 text-xs font-medium ${colors[value] ?? "bg-[#f2f1ea] text-[#6b7462]"}`}>
      {value.replaceAll("_", " ")}
    </span>
  );
}
