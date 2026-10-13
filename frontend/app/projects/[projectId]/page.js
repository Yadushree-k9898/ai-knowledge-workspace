'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { getSupabaseClient } from '../../../lib/supabase';
import { getOrganizationSettings } from '../../../services/organizationService';
import {
  deleteProject,
  getProject,
  getProjectSummary,
  updateProject,
} from '../../../services/projectService';

export default function ProjectOverviewPage() {
  const { projectId } = useParams();
  const router = useRouter();
  const [project, setProject] = useState(null);
  const [summary, setSummary] = useState(null);
  const [organizationRole, setOrganizationRole] = useState('');
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadProject = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Sign in to view this project.');
      const projectResult = await getProject(projectId, session.access_token);
      const [summaryResult, organization] = await Promise.all([
        getProjectSummary(projectId, session.access_token),
        getOrganizationSettings(projectResult.organization_id, session.access_token),
      ]);
      setProject(projectResult);
      setSummary(summaryResult);
      setOrganizationRole(organization.role);
      setName(projectResult.name);
      setDescription(projectResult.description || '');
    } catch (loadError) {
      setError(loadError.message || 'Could not load this project.');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadProject();
  }, [loadProject]);

  async function handleUpdate(event) {
    event.preventDefault();
    const trimmedName = name.trim();
    if (trimmedName.length < 2 || trimmedName.length > 200) {
      setError('Project name must be between 2 and 200 characters.');
      return;
    }

    setSaving(true);
    setError('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Your session has expired. Sign in again to update this project.');
      const updated = await updateProject(
        projectId,
        { name: trimmedName, description: description.trim() },
        session.access_token,
      );
      setProject(updated);
      setEditing(false);
    } catch (updateError) {
      setError(updateError.message || 'Could not update this project.');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    const confirmed = window.confirm(
      `Delete "${project.name}"? This removes the project, its reports, comparisons, and project links. Uploaded documents remain in your library.`,
    );
    if (!confirmed) return;

    setDeleting(true);
    setError('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Your session has expired. Sign in again to delete this project.');
      await deleteProject(projectId, session.access_token);
      router.replace('/projects');
    } catch (deleteError) {
      setError(deleteError.message || 'Could not delete this project.');
      setDeleting(false);
    }
  }

  const canEdit = ['OWNER', 'ADMIN', 'MEMBER'].includes(organizationRole);
  const canDelete = ['OWNER', 'ADMIN'].includes(organizationRole);

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <Link href="/projects" className="text-sm font-medium text-slate-600 hover:text-slate-950">← All projects</Link>
        {error && (
          <div role="alert" className="mt-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            <p>{error}</p>
            <button type="button" onClick={loadProject} className="mt-2 font-semibold underline">Retry</button>
          </div>
        )}
        {loading ? (
          <p role="status" className="mt-8 rounded-xl bg-white p-5 text-sm text-slate-500">Loading project…</p>
        ) : project ? (
          <>
            <header className="mt-8">
              <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Project</p>
                  <h1 className="mt-2 text-3xl font-bold tracking-tight">{project.name}</h1>
                  <p className="mt-3 max-w-3xl leading-7 text-slate-600">{project.description || 'No description provided.'}</p>
                  <Link href={`/organizations/${encodeURIComponent(project.organization_id)}`} className="mt-3 inline-flex text-sm font-medium text-indigo-600 hover:text-indigo-700">Open organization →</Link>
                </div>
                {(canEdit || canDelete) && (
                  <div className="flex shrink-0 gap-2">
                    {canEdit && (
                      <button
                        type="button"
                        onClick={() => setEditing((current) => !current)}
                        className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                      >
                        {editing ? 'Cancel edit' : 'Edit project'}
                      </button>
                    )}
                    {canDelete && (
                      <button
                        type="button"
                        onClick={handleDelete}
                        disabled={deleting}
                        className="rounded-lg border border-rose-200 bg-white px-4 py-2.5 text-sm font-semibold text-rose-700 hover:bg-rose-50 disabled:opacity-50"
                      >
                        {deleting ? 'Deleting…' : 'Delete project'}
                      </button>
                    )}
                  </div>
                )}
              </div>
            </header>
            {editing && canEdit && (
              <form onSubmit={handleUpdate} className="mt-6 grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <label htmlFor="edit-project-name" className="text-sm font-medium">
                  Project name
                  <input
                    id="edit-project-name"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    minLength={2}
                    maxLength={200}
                    required
                    disabled={saving}
                    className="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2.5"
                  />
                </label>
                <label htmlFor="edit-project-description" className="text-sm font-medium">
                  Description
                  <textarea
                    id="edit-project-description"
                    value={description}
                    onChange={(event) => setDescription(event.target.value)}
                    maxLength={2000}
                    rows={3}
                    disabled={saving}
                    className="mt-2 block w-full resize-y rounded-lg border border-slate-300 px-3 py-2.5"
                  />
                </label>
                <div>
                  <button type="submit" disabled={saving} className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
                    {saving ? 'Saving…' : 'Save changes'}
                  </button>
                  <button type="button" onClick={() => { setName(project.name); setDescription(project.description || ''); setEditing(false); }} disabled={saving} className="ml-3 rounded-lg px-4 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-100">
                    Cancel
                  </button>
                </div>
              </form>
            )}
            {summary && (
              <section aria-label="Project summary" className="mt-8 grid gap-4 sm:grid-cols-3">
                {[
                  ['Documents', summary.document_count],
                  ['Reports', summary.report_count],
                  ['Conversations', summary.conversation_count],
                ].map(([label, count]) => (
                  <div key={label} className="rounded-xl border border-slate-200 bg-white p-4">
                    <p className="text-sm text-slate-500">{label}</p>
                    <p className="mt-1 text-2xl font-bold">{count}</p>
                  </div>
                ))}
              </section>
            )}
            <section className="mt-8">
              <h2 className="text-lg font-semibold">Project workspace</h2>
              <ul className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {[
                  ['Documents', `/projects/${projectId}/documents`, 'Upload and manage project files.'],
                  ['Search', `/projects/${projectId}/search`, 'Find relevant passages in the files.'],
                  ['Chat', `/projects/${projectId}/chat`, 'Ask questions with source citations.'],
                  ['Comparisons', `/projects/${projectId}/comparisons`, 'Compare information across documents.'],
                  ['Reports', `/projects/${projectId}/reports`, 'Generate and review research reports.'],
                ].map(([title, href, description]) => (
                  <li key={title} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                    <h3 className="font-semibold">{title}</h3>
                    <p className="mt-2 min-h-10 text-sm leading-5 text-slate-600">{description}</p>
                    <Link href={href} className="mt-4 inline-flex text-sm font-semibold text-indigo-600 hover:text-indigo-700">Open {title.toLowerCase()} →</Link>
                  </li>
                ))}
              </ul>
            </section>
          </>
        ) : null}
      </div>
    </main>
  );
}
