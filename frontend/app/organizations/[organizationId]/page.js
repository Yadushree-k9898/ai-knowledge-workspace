'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';

export default function OrganizationOverviewPage() {
  const { organizationId } = useParams();

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Organization</p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight">Overview</h1>
        <p className="mt-3 text-slate-600">
          Organization: <span className="font-semibold text-slate-900">{organizationId}</span>
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href={`/organizations/${encodeURIComponent(organizationId)}/settings`} className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700">
            Settings
          </Link>
          <Link href={`/organizations/${encodeURIComponent(organizationId)}/members`} className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">
            Members
          </Link>
          <Link href="/organizations" className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">
            All organizations
          </Link>
        </div>
      </div>
    </main>
  );
}
