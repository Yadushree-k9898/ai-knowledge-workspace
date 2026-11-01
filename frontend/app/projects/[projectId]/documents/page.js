'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { getSupabaseClient } from '../../../../lib/supabase';
import {
  getProjectDocumentStatus,
  listProjectDocuments,
  removeProjectDocument,
  retryProjectDocument,
  uploadProjectDocument,
} from '../../../../services/documentService';

const ACTIVE_STATUSES = new Set(['PENDING', 'PROCESSING']);

function statusStyle(status) {
  if (status === 'COMPLETED') return 'bg-emerald-50 text-emerald-700';
  if (status === 'FAILED') return 'bg-rose-50 text-rose-700';
  if (status === 'PROCESSING') return 'bg-indigo-50 text-indigo-700';
  return 'bg-amber-50 text-amber-700';
}

export default function ProjectDocumentsPage() {
  const { projectId } = useParams();
  const fileInputRef = useRef(null);
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [removingId, setRemovingId] = useState(null);
  const [retryingId, setRetryingId] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Sign in to view project documents.');
      setDocuments(await listProjectDocuments(projectId, session.access_token));
    } catch (loadError) {
      setError(loadError.message || 'Could not load project documents.');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    const activeDocuments = documents.filter((document) =>
      ACTIVE_STATUSES.has(document.status),
    );
    if (activeDocuments.length === 0) return undefined;

    let cancelled = false;
    const pollStatuses = async () => {
      try {
        const { data: { session }, error: sessionError } =
          await getSupabaseClient().auth.getSession();
        if (sessionError || !session) return;

        const updates = await Promise.all(activeDocuments.map(async (document) => {
          try {
            const status = await getProjectDocumentStatus(
              projectId,
              document.id,
              session.access_token,
            );
            return [document.id, status];
          } catch {
            return [document.id, null];
          }
        }));

        if (!cancelled) {
          const statusById = new Map(updates.filter(([, status]) => status));
          setDocuments((current) => current.map((document) => {
            const status = statusById.get(document.id);
            return status ? { ...document, ...status } : document;
          }));
        }
      } catch {
        // A temporary polling failure should not hide the document list.
      }
    };

    const timer = setInterval(pollStatuses, 2500);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [documents, projectId]);

  async function handleUpload(event) {
    event.preventDefault();
    setError('');
    setNotice('');
    if (!selectedFile) {
      setError('Choose a file to upload.');
      return;
    }

    setUploading(true);
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Your session has expired. Sign in again to upload.');

      const uploaded = await uploadProjectDocument(
        projectId,
        selectedFile,
        session.access_token,
      );
      setDocuments((current) => [uploaded, ...current]);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setNotice(
        uploaded.queued
          ? `${uploaded.filename} was uploaded. Processing has started in the background.`
          : `${uploaded.filename} was saved, but the worker queue could not be reached. Use Retry when Redis is available.`,
      );
    } catch (uploadError) {
      setError(uploadError.message || 'Could not upload the document.');
    } finally {
      setUploading(false);
    }
  }

  async function handleRetry(document) {
    setError('');
    setNotice('');
    setRetryingId(document.id);
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Your session has expired. Sign in again to retry.');

      const result = await retryProjectDocument(
        projectId,
        document.id,
        session.access_token,
      );
      setDocuments((current) => current.map((item) => (
        item.id === document.id
          ? { ...item, status: 'PENDING', processing_error: null }
          : item
      )));
      setNotice(
        result.queued
          ? `Processing for ${document.filename} has been queued.`
          : 'The job is saved as pending, but Redis could not be reached. Try again when the worker queue is available.',
      );
    } catch (retryError) {
      setError(retryError.message || 'Could not retry document processing.');
    } finally {
      setRetryingId(null);
    }
  }

  async function handleRemove(document) {
    setError('');
    setNotice('');
    setRemovingId(document.id);
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Your session has expired. Sign in again to remove documents.');

      await removeProjectDocument(projectId, document.id, session.access_token);
      setDocuments((current) => current.filter((item) => item.id !== document.id));
      setNotice(`${document.filename} was removed from this project. The stored document was not deleted.`);
    } catch (removeError) {
      setError(removeError.message || 'Could not remove the document from this project.');
    } finally {
      setRemovingId(null);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl">
        <Link href={`/projects/${encodeURIComponent(projectId)}`} className="text-sm font-medium text-slate-600 hover:text-slate-950">
          ← Back to project
        </Link>
        <header className="mt-8">
          <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Project</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Documents</h1>
          <p className="mt-2 text-slate-600">
            Upload and manage documents connected to this project.
          </p>
        </header>

        {error && (
          <div role="alert" className="mt-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            <p>{error}</p>
            <button type="button" onClick={loadDocuments} className="mt-2 font-semibold underline">
              Retry loading documents
            </button>
          </div>
        )}
        {notice && (
          <p role="status" className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            {notice}
          </p>
        )}

        <form onSubmit={handleUpload} className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <label htmlFor="project-document" className="block text-sm font-semibold">
            Upload a document
          </label>
          <p className="mt-1 text-sm text-slate-500">
            PDF, TXT, Markdown, CSV, or JSON. Maximum file size: 10 MB.
          </p>
          <input
            ref={fileInputRef}
            id="project-document"
            type="file"
            accept=".pdf,.txt,.md,.csv,.json"
            onChange={(event) => {
              setSelectedFile(event.target.files?.[0] || null);
              setNotice('');
            }}
            disabled={uploading}
            className="mt-4 block w-full text-sm text-slate-700 file:mr-4 file:rounded-lg file:border-0 file:bg-indigo-50 file:px-4 file:py-2 file:font-semibold file:text-indigo-700 hover:file:bg-indigo-100 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!selectedFile || uploading}
            className="mt-4 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {uploading ? 'Uploading…' : 'Upload document'}
          </button>
        </form>

        <section className="mt-8 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-6 py-4">
            <h2 className="font-semibold">Project files</h2>
            <p className="mt-1 text-sm text-slate-500">
              Processing continues in the background. This list refreshes status automatically.
            </p>
          </div>
          {loading ? (
            <p role="status" className="p-6 text-sm text-slate-500">Loading project documents…</p>
          ) : documents.length === 0 ? (
            <p className="p-6 text-sm text-slate-500">No documents have been added to this project.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {documents.map((document) => (
                <li key={document.id} className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{document.filename}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusStyle(document.status || 'COMPLETED')}`}>
                        {(document.status || 'COMPLETED').toLowerCase()}
                      </span>
                      <span className="text-xs text-slate-500">
                        Added {document.added_at ? new Date(document.added_at).toLocaleString() : 'just now'}
                      </span>
                    </div>
                    {document.processing_error && (
                      <p className="mt-2 text-sm text-rose-700">{document.processing_error}</p>
                    )}
                  </div>
                  <div className="flex shrink-0 flex-wrap gap-2">
                    {(document.status === 'FAILED' || document.status === 'PENDING') && (
                      <button
                        type="button"
                        onClick={() => handleRetry(document)}
                        disabled={retryingId !== null || uploading || removingId !== null}
                        className="rounded-lg border border-indigo-200 px-3 py-2 text-sm font-semibold text-indigo-700 hover:bg-indigo-50 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {retryingId === document.id ? 'Queuing…' : 'Retry processing'}
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => handleRemove(document)}
                      disabled={removingId !== null || uploading || retryingId !== null}
                      className="rounded-lg border border-rose-200 px-3 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {removingId === document.id ? 'Removing…' : 'Remove from project'}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}
