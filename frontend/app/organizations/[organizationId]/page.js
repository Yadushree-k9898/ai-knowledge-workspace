'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { getSupabaseClient } from '../../../lib/supabase';
import { getOrganizationSettings } from '../../../services/organizationService';
import { listOrganizationProjects } from '../../../services/projectService';

export default function OrganizationOverviewPage() {
  const { organizationId } = useParams();
  const [organization, setOrganization] = useState(null);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadOrganization = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Sign in to view this organization.');

      const [organizationResult, projectResults] = await Promise.all([
        getOrganizationSettings(organizationId, session.access_token),
        listOrganizationProjects(organizationId, session.access_token),
      ]);
      setOrganization(organizationResult);
      setProjects(projectResults);
    } catch (loadError) {
      setError(loadError.message || 'Could not load this organization.');
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  useEffect(() => {
    loadOrganization();
  }, [loadOrganization]);

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <Link href="/organizations" className="text-sm font-medium text-slate-600 hover:text-slate-950">← All organizations</Link>
        {error && <div role="alert" className="mt-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}<button type="button" onClick={loadOrganization} className="ml-3 font-semibold underline">Retry</button></div>}
        {loading ? (
          <p role="status" className="mt-8 rounded-xl bg-white p-5 text-sm text-slate-500">Loading organization…</p>
        ) : organization ? (
          <>
            <header className="mt-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Organization</p>
                <h1 className="mt-2 text-3xl font-bold tracking-tight">{organization.name}</h1>
                <p className="mt-2 text-sm text-slate-500">{organization.slug} · Your role: {organization.role}</p>
      </div>
              <div className="flex gap-3">
                <Link href={`/organizations/${encodeURIComponent(organizationId)}/members`} className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">Members</Link>
                <Link href={`/organizations/${encodeURIComponent(organizationId)}/settings`} className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700">Settings</Link>
              </div>
            </header>
            <section className="mt-8">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-semibold">Projects</h2>
                  <p className="mt-1 text-sm text-slate-500">Projects shared with this organization.</p>
                </div>
                <Link href="/projects" className="text-sm font-semibold text-indigo-600 hover:text-indigo-700">Manage projects →</Link>
              </div>
              {projects.length === 0 ? (
                <p className="mt-4 rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">No projects yet. Open project management to create one.</p>
              ) : (
                <ul className="mt-4 grid gap-4 sm:grid-cols-2">
                  {projects.map((project) => (
                    <li key={project.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                      <h3 className="text-lg font-semibold">{project.name}</h3>
                      <p className="mt-2 line-clamp-2 text-sm text-slate-600">{project.description || 'No description provided.'}</p>
                      <Link href={`/projects/${encodeURIComponent(project.id)}`} className="mt-4 inline-flex text-sm font-semibold text-indigo-600 hover:text-indigo-700">Open project →</Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        ) : null}
        </div>
    </main>
  );
}
