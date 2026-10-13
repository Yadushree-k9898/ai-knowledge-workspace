'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { getSupabaseClient } from '../../../lib/supabase';
import { getProject } from '../../../services/projectService';

export default function ProjectOverviewPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
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
      setProject(await getProject(projectId, session.access_token));
    } catch (loadError) {
      setError(loadError.message || 'Could not load this project.');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadProject();
  }, [loadProject]);

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
              <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Project</p>
              <h1 className="mt-2 text-3xl font-bold tracking-tight">{project.name}</h1>
              <p className="mt-3 max-w-3xl leading-7 text-slate-600">{project.description || 'No description provided.'}</p>
              <Link href={`/organizations/${encodeURIComponent(project.organization_id)}`} className="mt-3 inline-flex text-sm font-medium text-indigo-600 hover:text-indigo-700">Open organization →</Link>
            </header>
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
