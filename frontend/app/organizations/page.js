'use client';

import Link from 'next/link';

export default function OrganizationsPage() {
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Organizations</p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight">Your workspace</h1>
        <p className="mt-3 text-slate-600">
          Manage the organizations you belong to, switch into a workspace, and review membership details.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/dashboard" className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700">
            Back to dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}
