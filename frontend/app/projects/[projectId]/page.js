'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';

export default function ProjectOverviewPage() {
  const { projectId } = useParams();

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Project</p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight">Overview</h1>
        <p className="mt-3 text-slate-600">
          Project: <span className="font-semibold text-slate-900">{projectId}</span>
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href={`/projects/${encodeURIComponent(projectId)}/documents`} className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700">
            Documents
          </Link>
          <Link href={`/projects/${encodeURIComponent(projectId)}/search`} className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">
            Search
          </Link>
          <Link href="/projects" className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">
            All projects
          </Link>
        </div>
      </div>
    </main>
  );
}
