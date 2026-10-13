'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { getSupabaseClient } from '../../lib/supabase';
import {
  createOrganization,
  listOrganizations,
} from '../../services/organizationService';

export default function OrganizationsPage() {
  const [organizations, setOrganizations] = useState([]);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  const loadOrganizations = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Sign in to view your organizations.');
      setOrganizations(await listOrganizations(session.access_token));
    } catch (loadError) {
      setError(loadError.message || 'Could not load organizations.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOrganizations();
  }, [loadOrganizations]);

  async function handleCreate(event) {
    event.preventDefault();
    const trimmedName = name.trim();
    if (trimmedName.length < 2 || trimmedName.length > 200) {
      setError('Organization name must be between 2 and 200 characters.');
      return;
    }

    setCreating(true);
    setError('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Your session has expired. Sign in again to create an organization.');
      const organization = await createOrganization(trimmedName, session.access_token);
      setOrganizations((current) => [
        ...current,
        { ...organization, role: 'OWNER' },
      ]);
      setName('');
    } catch (createError) {
      setError(createError.message || 'Could not create the organization.');
    } finally {
      setCreating(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <Link href="/dashboard" className="text-sm font-medium text-slate-600 hover:text-slate-950">
            Back to dashboard
        </Link>
        <header className="mt-8">
          <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Workspace</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Organizations</h1>
          <p className="mt-2 text-slate-600">Create and open the organizations you belong to.</p>
        </header>

        {error && (
          <div role="alert" className="mt-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            <p>{error}</p>
            <button type="button" onClick={loadOrganizations} className="mt-2 font-semibold underline">Retry</button>
          </div>
        )}

        <form onSubmit={handleCreate} className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:flex sm:items-end sm:gap-3">
          <label htmlFor="new-organization-name" className="block flex-1 text-sm font-medium">
            New organization
            <input
              id="new-organization-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              minLength={2}
              maxLength={200}
              required
              className="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2.5"
              placeholder="Organization name"
            />
          </label>
          <button type="submit" disabled={creating} className="mt-3 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 sm:mt-0">
            {creating ? 'Creating…' : 'Create organization'}
          </button>
        </form>

        <section className="mt-8">
          <h2 className="text-lg font-semibold">Your organizations</h2>
          {loading ? (
            <p role="status" className="mt-4 rounded-xl bg-white p-5 text-sm text-slate-500">Loading organizations…</p>
          ) : organizations.length === 0 ? (
            <p className="mt-4 rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">
              You don&apos;t belong to any organizations yet. Create one above to get started.
            </p>
          ) : (
            <ul className="mt-4 grid gap-4 sm:grid-cols-2">
              {organizations.map((organization) => (
                <li key={organization.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="truncate text-lg font-semibold">{organization.name}</h3>
                      <p className="mt-1 text-sm text-slate-500">{organization.slug}</p>
                    </div>
                    <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
                      {organization.role}
                    </span>
                  </div>
                  <Link href={`/organizations/${encodeURIComponent(organization.id)}`} className="mt-4 inline-flex text-sm font-semibold text-indigo-600 hover:text-indigo-700">
                    Open organization →
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}
