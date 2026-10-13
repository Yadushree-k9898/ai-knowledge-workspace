'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { getSupabaseClient } from '../../../../lib/supabase';
import {
  getOrganizationSettings,
  updateOrganizationName,
} from '../../../../services/organizationService';

export default function OrganizationSettingsPage() {
  const { organizationId } = useParams();
  const [organization, setOrganization] = useState(null);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadOrganization = useCallback(async () => {
    setLoading(true);
    setOrganization(null);
    setError('');

    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();

      if (sessionError) {
        throw sessionError;
      }
      if (!session) {
        throw new Error('Sign in to view organization settings.');
      }

      const result = await getOrganizationSettings(organizationId, session.access_token);
      setOrganization(result);
      setName(result.name);
    } catch (loadError) {
      setError(loadError.message || 'Could not load organization settings.');
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  useEffect(() => {
    loadOrganization();
  }, [loadOrganization]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setNotice('');

    const trimmedName = name.trim();
    if (trimmedName.length < 2 || trimmedName.length > 200) {
      setError('Organization name must be between 2 and 200 characters.');
      return;
    }

    setSaving(true);
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();

      if (sessionError) {
        throw sessionError;
      }
      if (!session) {
        throw new Error('Your session has expired. Sign in again to save changes.');
      }

      const updated = await updateOrganizationName(
        organizationId,
        trimmedName,
        session.access_token,
      );
      setOrganization((current) => ({ ...current, ...updated }));
      setName(updated.name);
      setNotice('Organization settings saved.');
    } catch (saveError) {
      setError(saveError.message || 'Could not save organization settings.');
    } finally {
      setSaving(false);
    }
  }

  const canManage = organization?.role === 'OWNER' || organization?.role === 'ADMIN';

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl">
        <Link
          href={`/organizations/${encodeURIComponent(organizationId)}`}
          className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 transition hover:text-slate-950"
        >
          <span aria-hidden="true">←</span>
          Back to organization
        </Link>

        <header className="mt-8">
          <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">
            Organization
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Settings</h1>
          <p className="mt-2 text-slate-600">
            Manage your organization&apos;s basic details and access.
          </p>
        </header>

        {error && (
          <div
            role="alert"
            className="mt-6 flex items-start justify-between gap-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
          >
            <p>{error}</p>
            <button
              type="button"
              onClick={loadOrganization}
              className="shrink-0 font-semibold underline underline-offset-2"
            >
              Retry
            </button>
          </div>
        )}

        {notice && (
          <p
            role="status"
            className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
          >
            {notice}
          </p>
        )}

        <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="mb-6 border-b border-slate-100 pb-5">
            <h2 className="text-lg font-semibold">General</h2>
            <p className="mt-1 text-sm text-slate-500">
              Update how this organization is identified in your workspace.
            </p>
          </div>

          {loading ? (
            <p role="status" className="py-4 text-sm text-slate-500">
              Loading organization settings…
            </p>
          ) : organization ? (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="organization-name" className="block text-sm font-medium">
                  Organization name
                </label>
                <input
                  id="organization-name"
                  name="name"
                  type="text"
                  required
                  minLength={2}
                  maxLength={200}
                  value={name}
                  onChange={(event) => {
                    setName(event.target.value);
                    setNotice('');
                  }}
                  disabled={!canManage || saving}
                  className="mt-2 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm shadow-sm outline-none transition placeholder:text-slate-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 disabled:cursor-not-allowed disabled:bg-slate-100"
                />
                <p className="mt-2 text-xs text-slate-500">
                  Between 2 and 200 characters.
                </p>
              </div>

              <div className="flex flex-col gap-3 border-t border-slate-100 pt-5 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-slate-500">
                  Your role: <span className="font-medium text-slate-700">{organization.role}</span>
                </p>
                {canManage ? (
                  <button
                    type="submit"
                    disabled={saving || name.trim() === organization.name}
                    className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 focus:outline-none focus:ring-4 focus:ring-indigo-200 disabled:cursor-not-allowed disabled:bg-slate-300"
                  >
                    {saving ? 'Saving…' : 'Save changes'}
                  </button>
                ) : (
                  <p className="text-sm text-slate-500">
                    An owner or admin can change organization settings.
                  </p>
                )}
              </div>
            </form>
          ) : null}
          {canManage && (
            <div className="mt-6 border-t border-slate-100 pt-5">
              <h3 className="text-sm font-semibold">Audit log</h3>
              <p className="mt-1 text-sm text-slate-500">
                Review organization and project activity.
              </p>
              <Link
                href={`/organizations/${encodeURIComponent(organizationId)}/audit-logs`}
                className="mt-3 inline-flex text-sm font-semibold text-indigo-600 hover:text-indigo-700"
              >
                View audit log
              </Link>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}