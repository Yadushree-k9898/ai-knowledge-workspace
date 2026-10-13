'use client';

import { useState } from 'react';

const REPORT_TYPES = [
  { value: 'SUMMARY', label: 'Summary', description: 'Main claims, themes, and conclusions.' },
  {
    value: 'COMPETITOR_ANALYSIS',
    label: 'Competitor analysis',
    description: 'Positioning, strengths, weaknesses, and evidence-backed differences.',
  },
  {
    value: 'DOCUMENT_REVIEW',
    label: 'Document review',
    description: 'Key points, structure, gaps, and notable claims.',
  },
  {
    value: 'RISK_ANALYSIS',
    label: 'Risk analysis',
    description: 'Material risks, evidence, potential impact, and uncertainty.',
  },
  {
    value: 'RESEARCH_BRIEF',
    label: 'Research brief',
    description: 'Concise findings and open questions.',
  },
];

export default function ReportGenerator({ documentCount, onSubmit, submitting }) {
  const [title, setTitle] = useState('');
  const [reportType, setReportType] = useState('SUMMARY');
  const [instructions, setInstructions] = useState('');
  const [error, setError] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmedTitle = title.trim();
    if (trimmedTitle.length < 2 || trimmedTitle.length > 200) {
      setError('Enter a title between 2 and 200 characters.');
      return;
    }

    setError('');
    try {
      await onSubmit({
        title: trimmedTitle,
        report_type: reportType,
        instructions: instructions.trim() || null,
      });
      setTitle('');
      setInstructions('');
    } catch (submitError) {
      setError(submitError.message || 'Could not start report generation.');
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label htmlFor="report-title" className="block text-sm font-medium text-slate-800">
          Report title
        </label>
        <input
          id="report-title"
          type="text"
          required
          minLength={2}
          maxLength={200}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="For example, Q4 competitor review"
          className="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition placeholder:text-slate-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
        />
      </div>

      <div>
        <label htmlFor="report-type" className="block text-sm font-medium text-slate-800">
          Report type
        </label>
        <select
          id="report-type"
          value={reportType}
          onChange={(event) => setReportType(event.target.value)}
          className="mt-2 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
        >
          {REPORT_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
        <p className="mt-2 text-xs text-slate-500">
          {REPORT_TYPES.find((type) => type.value === reportType)?.description}
        </p>
      </div>

      <div>
        <label htmlFor="report-instructions" className="block text-sm font-medium text-slate-800">
          Additional instructions <span className="font-normal text-slate-400">Optional</span>
        </label>
        <textarea
          id="report-instructions"
          rows={3}
          maxLength={5000}
          value={instructions}
          onChange={(event) => setInstructions(event.target.value)}
          placeholder="Tell the AI what to emphasize or answer."
          className="mt-2 block w-full resize-y rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition placeholder:text-slate-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
        />
      </div>

      <p className="text-xs text-slate-500">
        This report will use all {documentCount} document{documentCount === 1 ? '' : 's'} currently
        linked to this project.
      </p>

      {error && (
        <p role="alert" className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-800">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={submitting || documentCount === 0}
        className="inline-flex w-full items-center justify-center rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 focus:outline-none focus:ring-4 focus:ring-indigo-200 disabled:cursor-not-allowed disabled:bg-slate-300 sm:w-auto"
      >
        {submitting ? 'Starting report…' : 'Generate report'}
      </button>
    </form>
  );
}