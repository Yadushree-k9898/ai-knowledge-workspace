'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import ReportGenerator from '../../../../components/reports/ReportGenerator';
import ReportList from '../../../../components/reports/ReportList';
import ReportViewer from '../../../../components/reports/ReportViewer';
import { getSupabaseClient } from '../../../../lib/supabase';
import {
  addProjectDocument,
  getProjectDocuments,
  getUserDocuments,
} from '../../../../services/comparisonService';
import {
  createProjectReport,
  deleteReport,
  getProjectReports,
  getReport,
  regenerateReport,
} from '../../../../services/reportService';

export default function ProjectReportsPage() {
  const params = useParams();
  const projectId = Array.isArray(params.projectId) ? params.projectId[0] : params.projectId;
  const [accessToken, setAccessToken] = useState('');
  const [currentUserId, setCurrentUserId] = useState('');
  const [reports, setReports] = useState([]);
  const [projectDocuments, setProjectDocuments] = useState([]);
  const [userDocuments, setUserDocuments] = useState([]);
  const [activeReport, setActiveReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [busy, setBusy] = useState(false);
  const [attachingId, setAttachingId] = useState(null);
  const [error, setError] = useState('');

  const loadPage = useCallback(async () => {
    setLoading(true);
    setError('');
    setAccessToken('');
    setCurrentUserId('');
    setReports([]);
    setProjectDocuments([]);
    setUserDocuments([]);
    setActiveReport(null);

    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) {
        throw sessionError;
      }
      if (!session) {
        throw new Error('Sign in to view project research reports.');
      }

      setAccessToken(session.access_token);
      setCurrentUserId(session.user.id);

      const [projectReports, documents, availableDocuments] = await Promise.all([
        getProjectReports(projectId, session.access_token),
        getProjectDocuments(projectId, session.access_token),
        getUserDocuments(session.access_token),
      ]);
      setReports(projectReports);
      setProjectDocuments(documents);
      const projectDocumentIds = new Set(documents.map((document) => document.id));
      setUserDocuments(
        availableDocuments.filter((document) => !projectDocumentIds.has(document.id)),
      );
      setActiveReport(projectReports[0] || null);
    } catch (loadError) {
      setError(loadError.message || 'Could not load project reports.');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  async function handleAddDocument(document) {
    setError('');
    setAttachingId(document.id);
    try {
      const linked = await addProjectDocument(projectId, document.id, accessToken);
      setProjectDocuments((current) => [
        linked,
        ...current.filter((item) => item.id !== linked.id),
      ]);
      setUserDocuments((current) => current.filter((item) => item.id !== linked.id));
    } catch (attachError) {
      setError(attachError.message || 'Could not add this document to the project.');
    } finally {
      setAttachingId(null);
    }
  }

  useEffect(() => {
    loadPage();
  }, [loadPage]);

  useEffect(() => {
    const reportId = activeReport?.id;
    if (
      !reportId ||
      !accessToken ||
      ['READY', 'FAILED'].includes(activeReport.status)
    ) {
      return undefined;
    }

    let cancelled = false;
    let timeoutId;

    async function poll() {
      try {
        const updated = await getReport(reportId, accessToken);
        if (cancelled) {
          return;
        }
        setActiveReport(updated);
        setReports((current) => [
          updated,
          ...current.filter((report) => report.id !== updated.id),
        ]);
        if (!['READY', 'FAILED'].includes(updated.status)) {
          timeoutId = window.setTimeout(poll, 2500);
        }
      } catch (pollError) {
        if (!cancelled) {
          setError(pollError.message || 'Could not check report status.');
          timeoutId = window.setTimeout(poll, 5000);
        }
      }
    }

    timeoutId = window.setTimeout(poll, 2000);
    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [activeReport, accessToken]);

  async function handleCreate(payload) {
    setError('');
    setSubmitting(true);
    try {
      const report = await createProjectReport(projectId, payload, accessToken);
      setActiveReport(report);
      setReports((current) => [report, ...current.filter((item) => item.id !== report.id)]);
    } catch (createError) {
      setError(createError.message || 'Could not start report generation.');
      throw createError;
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRegenerate(report) {
    setError('');
    setBusy(true);
    try {
      const queuedReport = await regenerateReport(report.id, accessToken);
      setActiveReport(queuedReport);
      setReports((current) => [
        queuedReport,
        ...current.filter((item) => item.id !== queuedReport.id),
      ]);
    } catch (regenerateError) {
      setError(regenerateError.message || 'Could not regenerate this report.');
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(report) {
    if (!window.confirm(`Delete "${report.title}"? This cannot be undone.`)) {
      return;
    }
    setError('');
    setBusy(true);
    try {
      await deleteReport(report.id, accessToken);
      const remainingReports = reports.filter((item) => item.id !== report.id);
      setReports(remainingReports);
      setActiveReport(
        activeReport?.id === report.id
          ? remainingReports[0] || null
          : activeReport,
      );
    } catch (deleteError) {
      setError(deleteError.message || 'Could not delete this report.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <Link
          href={`/projects/${encodeURIComponent(projectId)}`}
          className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 transition hover:text-slate-950"
        >
          <span aria-hidden="true">←</span>
          Back to project
        </Link>

        <header className="mt-8">
          <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">
            Project research
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Research reports</h1>
          <p className="mt-2 max-w-2xl text-slate-600">
            Generate evidence-based reports from documents linked to this project. Reports cite
            source filenames and call out uncertainty rather than inventing evidence.
          </p>
        </header>

        {error && (
          <div
            role="alert"
            className="mt-6 flex items-start justify-between gap-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
          >
            <p>{error}</p>
            <button
              type="button"
              onClick={() => setError('')}
              className="shrink-0 font-semibold underline underline-offset-2"
            >
              Dismiss
            </button>
          </div>
        )}

        {loading ? (
          <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <p role="status" className="text-sm text-slate-500">
              Loading project reports…
            </p>
          </section>
        ) : (
          <>
            <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-6 border-b border-slate-100 pb-5">
                <h2 className="text-lg font-semibold">Generate a report</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Add project documents from the{' '}
                  <Link
                    href={`/projects/${encodeURIComponent(projectId)}/documents`}
                    className="font-medium text-indigo-700 underline underline-offset-2"
                  >
                    documents area
                  </Link>
                  . Reports use all documents currently linked to this project.
                </p>
              </div>
              {projectDocuments.length ? (
                <ul className="mb-5 flex flex-wrap gap-2" aria-label="Report source documents">
                  {projectDocuments.map((document) => (
                    <li
                      key={document.id}
                      title={document.filename}
                      className="max-w-full truncate rounded-lg bg-slate-100 px-2.5 py-1.5 text-xs font-medium text-slate-700"
                    >
                      {document.filename}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mb-5 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
                  Add at least one document to this project before generating a report.
                </p>
              )}
              <ReportGenerator
                documentCount={projectDocuments.length}
                onSubmit={handleCreate}
                submitting={submitting}
              />
            </section>

            <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold">Your uploaded documents</h2>
              <p className="mt-1 text-sm text-slate-500">
                Add your documents to this project to use them as report sources.
              </p>
              {userDocuments.length ? (
                <ul className="mt-4 divide-y divide-slate-100">
                  {userDocuments.map((document) => (
                    <li
                      key={document.id}
                      className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0"
                    >
                      <span className="min-w-0 truncate text-sm font-medium text-slate-800">
                        {document.filename}
                      </span>
                      <button
                        type="button"
                        disabled={attachingId === document.id}
                        onClick={() => handleAddDocument(document)}
                        className="shrink-0 rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 disabled:cursor-wait disabled:opacity-60"
                      >
                        {attachingId === document.id ? 'Adding…' : 'Add to project'}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-4 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
                  {projectDocuments.length
                    ? 'All of your uploaded documents are already linked to this project.'
                    : 'You have no uploaded documents to add yet.'}
                </p>
              )}
            </section>

            <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(260px,0.65fr)_minmax(0,1.5fr)]">
              <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between gap-3">
                  <h2 className="text-lg font-semibold">Recent reports</h2>
                  <span className="text-xs text-slate-400">Last 50</span>
                </div>
                <ReportList
                  reports={reports}
                  activeReportId={activeReport?.id}
                  onSelect={setActiveReport}
                />
              </aside>

              <ReportViewer
                report={activeReport}
                currentUserId={currentUserId}
                onRegenerate={handleRegenerate}
                onDelete={handleDelete}
                busy={busy}
              />
            </div>
          </>
        )}
      </div>
    </main>
  );
}