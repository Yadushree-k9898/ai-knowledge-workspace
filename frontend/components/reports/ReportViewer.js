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

export default function ReportViewer({
  report,
  currentUserId,
  onRegenerate,
  onDelete,
  busy,
}) {
  if (!report) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 px-6 py-12 text-center">
        <h2 className="text-base font-semibold text-slate-800">No report selected</h2>
        <p className="mt-1 text-sm text-slate-500">
          Generate a report or choose one from your recent reports.
        </p>
      </div>
    );
  }

  const canRegenerate = ['READY', 'FAILED'].includes(report.status);
  const isOwner = report.created_by === currentUserId;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 pb-5">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">
            {report.report_type.replaceAll('_', ' ')}
          </p>
          <h2 className="mt-1 break-words text-xl font-semibold">{report.title}</h2>
          <p className="mt-1 text-xs text-slate-500">
            Created {formatDate(report.created_at)}
          </p>
        </div>
        <span
          className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
            report.status === 'READY'
              ? 'bg-emerald-50 text-emerald-800'
              : report.status === 'FAILED'
                ? 'bg-rose-50 text-rose-800'
                : 'bg-indigo-50 text-indigo-800'
          }`}
        >
          {report.status.toLowerCase()}
        </span>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {canRegenerate && (
          <button
            type="button"
            onClick={() => onRegenerate(report)}
            disabled={busy}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 disabled:cursor-wait disabled:opacity-60"
          >
            {busy ? 'Working…' : 'Regenerate'}
          </button>
        )}
        {isOwner && (
          <button
            type="button"
            onClick={() => onDelete(report)}
            disabled={busy}
            className="rounded-lg border border-rose-200 px-3 py-2 text-sm font-semibold text-rose-700 transition hover:bg-rose-50 disabled:cursor-wait disabled:opacity-60"
          >
            Delete report
          </button>
        )}
      </div>

      {report.status === 'READY' && report.content ? (
        <div className="mt-6 max-h-[55rem] overflow-y-auto rounded-xl bg-slate-50 p-5 text-sm leading-7 text-slate-700">
          <pre className="whitespace-pre-wrap font-sans">{report.content}</pre>
        </div>
      ) : report.status === 'FAILED' ? (
        <p role="alert" className="mt-6 rounded-xl bg-rose-50 p-4 text-sm text-rose-800">
          {report.error || 'The report could not be generated.'}
        </p>
      ) : (
        <p role="status" className="mt-6 rounded-xl bg-indigo-50 p-4 text-sm text-indigo-800">
          {report.status === 'QUEUED'
            ? 'Your report is waiting for a worker.'
            : 'The AI is preparing your report from the project documents.'}
        </p>
      )}
    </section>
  );
}