'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';

export default function OrganizationMembersPage() {
  const { organizationId } = useParams();

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Organization</p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight">Members</h1>
        <p className="mt-3 text-slate-600">
          Manage team access for organization <span className="font-semibold text-slate-900">{organizationId}</span>.
        </p>
        <div className="mt-6">
          <Link href={`/organizations/${encodeURIComponent(organizationId)}`} className="text-sm font-semibold text-indigo-600 hover:text-indigo-700">
            ← Back to organization
          </Link>
        </div>
      </div>
    </main>
  );
}
