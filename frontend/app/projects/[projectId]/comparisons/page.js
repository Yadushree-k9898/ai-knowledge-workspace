'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { getSupabaseClient } from '../../../../lib/supabase';
import {
  addProjectDocument,
  createProjectComparison,
  getProjectComparison,
  getProjectComparisons,
  getProjectDocuments,
  getUserDocuments,
} from '../../../../services/comparisonService';

const MAX_SELECTED_DOCUMENTS = 5;

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
    PROCESSING: 'bg-indigo-50 text-indigo-800 ring-indigo-200',
    COMPLETED: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
    FAILED: 'bg-rose-50 text-rose-800 ring-rose-200',
  };

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${
        styles[status] || 'bg-slate-100 text-slate-700 ring-slate-200'
      }`}
    >
      {status.toLowerCase()}
    </span>
  );
}

export default function ProjectComparisonsPage() {
  const params = useParams();
  const projectId = Array.isArray(params.projectId) ? params.projectId[0] : params.projectId;
  const [accessToken, setAccessToken] = useState('');
  const [projectDocuments, setProjectDocuments] = useState([]);
  const [userDocuments, setUserDocuments] = useState([]);
  const [comparisons, setComparisons] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [instructions, setInstructions] = useState('');
  const [activeComparison, setActiveComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [attachingId, setAttachingId] = useState(null);
  const [error, setError] = useState('');

  const loadPage = useCallback(async () => {
    setLoading(true);
    setError('');
    setAccessToken('');
    setProjectDocuments([]);
    setUserDocuments([]);
    setComparisons([]);
    setActiveComparison(null);
    setSelectedIds([]);

    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();

      if (sessionError) {
        throw sessionError;
      }
      if (!session) {
        throw new Error('Sign in to compare project documents.');
      }
      setAccessToken(session.access_token);

      const [projectDocs, availableDocs, recentComparisons] = await Promise.all([
        getProjectDocuments(projectId, session.access_token),
        getUserDocuments(session.access_token),
        getProjectComparisons(projectId, session.access_token),
      ]);

      setProjectDocuments(projectDocs);
      const projectDocumentIds = new Set(projectDocs.map((document) => document.id));
      setUserDocuments(availableDocs.filter((document) => !projectDocumentIds.has(document.id)));
      setComparisons(recentComparisons);
      setActiveComparison(recentComparisons[0] || null);
    } catch (loadError) {
      setError(loadError.message || 'Could not load project comparisons.');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadPage();
  }, [loadPage]);

  useEffect(() => {
    const comparisonId = activeComparison?.id;
    if (
      !comparisonId ||
      !accessToken ||
      ['COMPLETED', 'FAILED'].includes(activeComparison.status)
    ) {
      return undefined;
    }

    let cancelled = false;
    let timeoutId;

    async function poll() {
      try {
        const updated = await getProjectComparison(projectId, comparisonId, accessToken);
        if (cancelled) {
          return;
        }
        setActiveComparison(updated);
        setComparisons((current) => [
          updated,
          ...current.filter((comparison) => comparison.id !== updated.id),
        ]);
        if (!['COMPLETED', 'FAILED'].includes(updated.status)) {
          timeoutId = window.setTimeout(poll, 2500);
        }
      } catch (pollError) {
        if (!cancelled) {
          setError(pollError.message || 'Could not check comparison status.');
          timeoutId = window.setTimeout(poll, 5000);
        }
      }
    }

    timeoutId = window.setTimeout(poll, 2000);
    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [activeComparison, accessToken, projectId]);

  function toggleDocument(documentId) {
    if (selectedIds.includes(documentId)) {
      setSelectedIds((current) => current.filter((id) => id !== documentId));
      return;
    }
    if (selectedIds.length >= MAX_SELECTED_DOCUMENTS) {
      setError(`Choose no more than ${MAX_SELECTED_DOCUMENTS} documents per comparison.`);
      return;
    }
    setError('');
    setSelectedIds((current) => (
      current.includes(documentId) ? current : [...current, documentId]
    ));
  }

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

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const comparison = await createProjectComparison(
        projectId,
        { document_ids: selectedIds, instructions: instructions.trim() || null },
        accessToken,
      );
      setActiveComparison(comparison);
      setComparisons((current) => [
        comparison,
        ...current.filter((item) => item.id !== comparison.id),
      ]);
    } catch (submitError) {
      setError(submitError.message || 'Could not start the comparison.');
    } finally {
      setSubmitting(false);
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
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Compare documents</h1>
          <p className="mt-2 max-w-2xl text-slate-600">
            Select two to five project documents. AI will identify key similarities, differences,
            and changes, with findings grounded in the source documents.
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
              Loading project documents…
            </p>
          </section>
        ) : (
          <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(300px,0.8fr)]">
            <section className="space-y-6">
              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex flex-wrap items-end justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold">Choose project documents</h2>
                    <p className="mt-1 text-sm text-slate-500">
                      Select 2–5 documents to compare.
                    </p>
                  </div>
                  <span className="text-sm font-medium text-slate-500">
                    {selectedIds.length}/{MAX_SELECTED_DOCUMENTS} selected
                  </span>
                </div>

                {projectDocuments.length ? (
                  <ul className="mt-5 divide-y divide-slate-100">
                    {projectDocuments.map((document) => (
                      <li key={document.id} className="py-3 first:pt-0 last:pb-0">
                        <label className="flex cursor-pointer items-center gap-3">
                          <input
                            type="checkbox"
                            checked={selectedIds.includes(document.id)}
                            onChange={() => toggleDocument(document.id)}
                            disabled={
                              !selectedIds.includes(document.id) &&
                              selectedIds.length >= MAX_SELECTED_DOCUMENTS
                            }
                            className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 disabled:cursor-not-allowed"
                          />
                          <span className="min-w-0 flex-1">
                            <span className="block truncate text-sm font-medium text-slate-800">
                              {document.filename}
                            </span>
                            <span className="mt-0.5 block text-xs text-slate-500">
                              Added {formatDate(document.added_at)}
                            </span>
                          </span>
                        </label>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="mt-5 rounded-xl border border-dashed border-slate-300 px-5 py-8 text-center">
                    <p className="text-sm font-medium text-slate-700">
                      No documents have been added to this project yet.
                    </p>
                    <p className="mt-1 text-sm text-slate-500">
                      Add one of your uploaded documents below to get started.
                    </p>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="mt-6 space-y-4 border-t border-slate-100 pt-5">
                  <div>
                    <label htmlFor="comparison-instructions" className="block text-sm font-medium">
                      What should the AI focus on? <span className="font-normal text-slate-400">Optional</span>
                    </label>
                    <textarea
                      id="comparison-instructions"
                      rows={3}
                      maxLength={5000}
                      value={instructions}
                      onChange={(event) => setInstructions(event.target.value)}
                      placeholder="For example: compare the proposed timelines and risks."
                      className="mt-2 block w-full resize-y rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm shadow-sm outline-none transition placeholder:text-slate-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={submitting || selectedIds.length < 2 || !accessToken}
                    className="inline-flex w-full items-center justify-center rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 focus:outline-none focus:ring-4 focus:ring-indigo-200 disabled:cursor-not-allowed disabled:bg-slate-300 sm:w-auto"
                  >
                    {submitting ? 'Starting comparison…' : 'Compare selected documents'}
                  </button>
                </form>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-semibold">Your uploaded documents</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Add a document to this project before including it in a comparison.
                </p>
                {userDocuments.length ? (
                  <ul className="mt-4 divide-y divide-slate-100">
                    {userDocuments.map((document) => (
                      <li
                        key={document.id}
                        className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0"
                      >
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-medium text-slate-800">
                            {document.filename}
                          </span>
                          <span className="mt-0.5 block text-xs text-slate-500">
                            Uploaded {formatDate(document.created_at)}
                          </span>
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
                    You don&apos;t have any uploaded documents yet. Upload documents in the project&apos;s{' '}
                    <Link
                      href={`/projects/${encodeURIComponent(projectId)}/documents`}
                      className="font-semibold text-indigo-700 underline underline-offset-2"
                    >
                      documents area
                    </Link>
                    .
                  </p>
                )}
              </div>
            </section>

            <aside className="space-y-6">
              {activeComparison && (
                <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h2 className="text-lg font-semibold">Comparison result</h2>
                      <p className="mt-1 text-xs text-slate-500">
                        Started {formatDate(activeComparison.created_at)}
                      </p>
                    </div>
                    <StatusBadge status={activeComparison.status} />
                  </div>

                  <ul className="mt-4 flex flex-wrap gap-2">
                    {activeComparison.document_names.map((name, index) => (
                      <li
                        key={`${activeComparison.document_ids[index]}-${index}`}
                        className="max-w-full truncate rounded-lg bg-slate-100 px-2.5 py-1.5 text-xs font-medium text-slate-700"
                      >
                        {name}
                      </li>
                    ))}
                  </ul>

                  {activeComparison.status === 'COMPLETED' && activeComparison.result ? (
                    <div className="mt-5 max-h-[36rem] overflow-y-auto rounded-xl bg-slate-50 p-4 text-sm leading-6 text-slate-700">
                      <pre className="whitespace-pre-wrap font-sans">{activeComparison.result}</pre>
                    </div>
                  ) : activeComparison.status === 'FAILED' ? (
                    <p role="alert" className="mt-5 rounded-xl bg-rose-50 p-4 text-sm text-rose-800">
                      {activeComparison.error || 'The comparison could not be completed.'}
                    </p>
                  ) : (
                    <p role="status" className="mt-5 rounded-xl bg-indigo-50 p-4 text-sm text-indigo-800">
                      {activeComparison.status === 'QUEUED'
                        ? 'Your comparison is waiting for a worker.'
                        : 'The AI is comparing the selected documents. This may take a little while.'}
                    </p>
                  )}
                </section>
              )}

              <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center justify-between gap-3">
                  <h2 className="text-lg font-semibold">Recent comparisons</h2>
                  <span className="text-xs text-slate-400">Last 20</span>
                </div>
                {comparisons.length ? (
                  <ul className="mt-4 space-y-2">
                    {comparisons.map((comparison) => (
                      <li key={comparison.id}>
                        <button
                          type="button"
                          onClick={() => setActiveComparison(comparison)}
                          aria-current={activeComparison?.id === comparison.id ? 'true' : undefined}
                          className="w-full rounded-xl border border-slate-200 p-3 text-left transition hover:border-indigo-300 hover:bg-indigo-50/50 aria-[current=true]:border-indigo-300 aria-[current=true]:bg-indigo-50"
                        >
                          <span className="flex items-center justify-between gap-3">
                            <span className="min-w-0 truncate text-sm font-medium text-slate-800">
                              {comparison.document_names.join(' · ')}
                            </span>
                            <StatusBadge status={comparison.status} />
                          </span>
                          <span className="mt-1 block text-xs text-slate-500">
                            {formatDate(comparison.created_at)}
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-4 text-sm text-slate-500">
                    Your project comparisons will appear here.
                  </p>
                )}
              </section>
            </aside>
          </div>
        )}
      </div>
    </main>
  );
}