'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { getSupabaseClient } from '../../lib/supabase';
import { listOrganizations } from '../../services/organizationService';
import {
  createOrganizationProject,
  listOrganizationProjects,
} from '../../services/projectService';

export default function ProjectsPage() {
  const [organizations, setOrganizations] = useState([]);
  const [projectsByOrganization, setProjectsByOrganization] = useState({});
  const [organizationId, setOrganizationId] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  const loadProjects = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Sign in to view your projects.');

      const organizationResults = await listOrganizations(session.access_token);
      const projectResults = await Promise.all(
        organizationResults.map(async (organization) => [
          organization.id,
          await listOrganizationProjects(organization.id, session.access_token),
        ]),
      );
      setOrganizations(organizationResults);
      setProjectsByOrganization(Object.fromEntries(projectResults));
      setOrganizationId((current) => {
        if (current && organizationResults.some((item) => item.id === current)) return current;
        return organizationResults[0]?.id || '';
      });
    } catch (loadError) {
      setError(loadError.message || 'Could not load projects.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const projects = useMemo(
    () => organizations.flatMap((organization) => (
      (projectsByOrganization[organization.id] || []).map((project) => ({
        ...project,
        organization_name: organization.name,
      }))
    )),
    [organizations, projectsByOrganization],
  );

  async function handleCreate(event) {
    event.preventDefault();
    const trimmedName = name.trim();
    if (trimmedName.length < 2 || trimmedName.length > 200) {
      setError('Project name must be between 2 and 200 characters.');
      return;
    }
    if (!organizationId) {
      setError('Create or join an organization before creating a project.');
      return;
    }

    setCreating(true);
    setError('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Your session has expired. Sign in again to create a project.');

      const project = await createOrganizationProject(
        organizationId,
        { name: trimmedName, description: description.trim() || null },
        session.access_token,
      );
      setProjectsByOrganization((current) => ({
        ...current,
        [organizationId]: [project, ...(current[organizationId] || [])],
      }));
      setName('');
      setDescription('');
    } catch (createError) {
      setError(createError.message || 'Could not create the project.');
    } finally {
      setCreating(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <Link href="/dashboard" className="text-sm font-medium text-slate-600 hover:text-slate-950">← Back to dashboard</Link>
        <header className="mt-8">
          <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Workspace</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Projects</h1>
          <p className="mt-2 text-slate-600">Create projects inside your organizations and open their research tools.</p>
        </header>

        {error && (
          <div role="alert" className="mt-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            <p>{error}</p>
            <button type="button" onClick={loadProjects} className="mt-2 font-semibold underline">Retry</button>
          </div>
        )}

        <form onSubmit={handleCreate} className="mt-8 grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:grid-cols-2">
          <label htmlFor="project-organization" className="text-sm font-medium">
            Organization
            <select
              id="project-organization"
              value={organizationId}
              onChange={(event) => setOrganizationId(event.target.value)}
              disabled={loading || organizations.length === 0 || creating}
              className="mt-2 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5"
              required
            >
              {organizations.length === 0 && <option value="">No organizations available</option>}
              {organizations.map((organization) => (
                <option key={organization.id} value={organization.id}>{organization.name}</option>
              ))}
            </select>
          </label>
          <label htmlFor="project-name" className="text-sm font-medium">
            Project name
            <input
              id="project-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              minLength={2}
              maxLength={200}
              required
              disabled={creating || organizations.length === 0}
              className="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2.5"
              placeholder="For example, Market research"
            />
          </label>
          <label htmlFor="project-description" className="text-sm font-medium sm:col-span-2">
            Description <span className="font-normal text-slate-500">(optional)</span>
            <textarea
              id="project-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              maxLength={2000}
              rows={2}
              disabled={creating || organizations.length === 0}
              className="mt-2 block w-full resize-y rounded-lg border border-slate-300 px-3 py-2.5"
              placeholder="What will this project investigate?"
            />
          </label>
          <div className="sm:col-span-2">
            <button type="submit" disabled={creating || loading || organizations.length === 0} className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300">
              {creating ? 'Creating…' : 'Create project'}
            </button>
            {organizations.length === 0 && !loading && (
              <Link href="/organizations" className="ml-3 text-sm font-semibold text-indigo-600 hover:text-indigo-700">Create an organization first</Link>
            )}
          </div>
        </form>

        <section className="mt-8">
          <h2 className="text-xl font-semibold">All projects</h2>
          {loading ? (
            <p role="status" className="mt-4 rounded-xl bg-white p-5 text-sm text-slate-500">Loading projects…</p>
          ) : projects.length === 0 ? (
            <p className="mt-4 rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">No projects yet. Create one above to get started.</p>
          ) : (
            <ul className="mt-4 grid gap-4 sm:grid-cols-2">
              {projects.map((project) => (
                <li key={project.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">{project.organization_name}</p>
                  <h3 className="mt-2 text-lg font-semibold">{project.name}</h3>
                  <p className="mt-2 line-clamp-2 min-h-10 text-sm text-slate-600">{project.description || 'No description provided.'}</p>
                  <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-sm font-semibold">
                    <Link href={`/projects/${encodeURIComponent(project.id)}`} className="text-indigo-600 hover:text-indigo-700">Overview</Link>
                    <Link href={`/projects/${encodeURIComponent(project.id)}/documents`} className="text-indigo-600 hover:text-indigo-700">Documents</Link>
                    <Link href={`/projects/${encodeURIComponent(project.id)}/search`} className="text-indigo-600 hover:text-indigo-700">Search</Link>
                    <Link href={`/projects/${encodeURIComponent(project.id)}/chat`} className="text-indigo-600 hover:text-indigo-700">Chat</Link>
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
