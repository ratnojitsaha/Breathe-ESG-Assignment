import { ReactNode } from "react";

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-t border-stone-200 bg-white">
      <div className="mx-auto max-w-7xl px-5 py-6">
        <h2 className="mb-4 text-base font-semibold text-slate-900">{title}</h2>
        {children}
      </div>
    </section>
  );
}
