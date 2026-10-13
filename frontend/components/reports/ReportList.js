'use client';

function formatDate(value) {
  if (!value) {
    return 'Just now';
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

function StatusBadge({ status }) {
  const styles = {
    QUEUED: 'bg-amber-50 text-amber-800 ring-amber-200',
    GENERATING: 'bg-indigo-50 text-indigo-800 ring-indigo-200',
    READY: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
    FAILED: 'bg-rose-50 text-rose-800 ring-rose-200',
  };

  return (
    <span
      className={`inline-flex shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${
        styles[status] || 'bg-slate-100 text-slate-700 ring-slate-200'
      }`}
    >
      {status.toLowerCase()}
    </span>
  );
}

export default function ReportList({ reports, activeReportId, onSelect }) {
  if (!reports.length) {
    return (
      <p className="mt-4 text-sm text-slate-500">
        Generated reports will appear here.
      </p>
    );
  }

  return (
    <ul className="mt-4 space-y-2">
      {reports.map((report) => (
        <li key={report.id}>
          <button
            type="button"
            onClick={() => onSelect(report)}
            aria-current={activeReportId === report.id ? 'true' : undefined}
            className="w-full rounded-xl border border-slate-200 p-3 text-left transition hover:border-indigo-300 hover:bg-indigo-50/50 aria-[current=true]:border-indigo-300 aria-[current=true]:bg-indigo-50"
          >
            <span className="flex items-center justify-between gap-3">
              <span className="min-w-0 truncate text-sm font-medium text-slate-800">
                {report.title}
              </span>
              <StatusBadge status={report.status} />
            </span>
            <span className="mt-1 block text-xs text-slate-500">
              {report.report_type.replaceAll('_', ' ')} · {formatDate(report.created_at)}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}