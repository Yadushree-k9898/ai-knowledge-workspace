'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { getSupabaseClient } from '../../../../lib/supabase';
import { getOrganizationAuditLogs } from '../../../../services/organizationService';

const PAGE_SIZE = 50;

export default function OrganizationAuditLogsPage() {
  const { organizationId } = useParams();
  const [events, setEvents] = useState([]);
  const [pagination, setPagination] = useState({ offset: 0, total: 0 });
  const [action, setAction] = useState('');
  const [resourceType, setResourceType] = useState('');
  const [activeFilters, setActiveFilters] = useState({ action: '', resourceType: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadEvents = useCallback(async (offset = 0) => {
    setLoading(true);
    setError('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Sign in to view organization audit logs.');

      const result = await getOrganizationAuditLogs(
        organizationId,
        session.access_token,
        {
          limit: PAGE_SIZE,
          offset,
          action: activeFilters.action,
          resourceType: activeFilters.resourceType,
        },
      );
      setEvents(result.events);
      setPagination(result.pagination);
    } catch (loadError) {
      setError(loadError.message || 'Could not load organization audit logs.');
    } finally {
      setLoading(false);
    }
  }, [activeFilters, organizationId]);

  useEffect(() => {
    loadEvents(0);
  }, [loadEvents]);

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <Link
          href={`/organizations/${encodeURIComponent(organizationId)}/settings`}
          className="text-sm font-medium text-slate-600 hover:text-slate-950"
        >
          ← Back to settings
        </Link>
        <header className="mt-8">
          <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">
            Organization
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Audit log</h1>
          <p className="mt-2 text-slate-600">
            A read-only history of organization and project activity. Visible to owners and admins.
          </p>
        </header>

        <form
          className="mt-8 grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 sm:grid-cols-[1fr_1fr_auto]"
          onSubmit={(event) => {
            event.preventDefault();
            setActiveFilters({ action: action.trim(), resourceType: resourceType.trim() });
          }}
        >
          <label className="text-sm font-medium">
            Action
            <input
              value={action}
              onChange={(event) => setAction(event.target.value)}
              maxLength={100}
              placeholder="e.g. PROJECT_CREATED"
              className="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2 font-normal"
            />
          </label>
          <label className="text-sm font-medium">
            Resource type
            <input
              value={resourceType}
              onChange={(event) => setResourceType(event.target.value)}
              maxLength={50}
              placeholder="e.g. project"
              className="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2 font-normal"
            />
          </label>
          <button
            type="submit"
            disabled={loading}
            className="self-end rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            Apply filters
          </button>
        </form>

        {error && (
          <div role="alert" className="mt-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            <p>{error}</p>
            <button type="button" onClick={() => loadEvents(pagination.offset)} className="mt-2 font-semibold underline">
              Retry
            </button>
          </div>
        )}

        <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          {loading ? (
            <p role="status" className="p-6 text-sm text-slate-500">Loading audit events…</p>
          ) : events.length === 0 ? (
            <p className="p-6 text-sm text-slate-500">No audit events match these filters.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {events.map((event) => (
                <li key={event.id} className="p-5">
                  <div className="flex flex-col justify-between gap-2 sm:flex-row">
                    <div>
                      <p className="font-semibold">{event.action}</p>
                      <p className="mt-1 text-sm text-slate-600">
                        {event.resource_type} · {event.resource_id}
                      </p>
                    </div>
                    <time dateTime={event.timestamp} className="text-sm text-slate-500">
                      {new Date(event.timestamp).toLocaleString()}
                    </time>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    Actor: {event.user_id || 'System'} · Event ID: {event.id}
                  </p>
                  {Object.keys(event.metadata || {}).length > 0 && (
                    <details className="mt-3 text-sm">
                      <summary className="cursor-pointer font-medium text-indigo-700">Event details</summary>
                      <pre className="mt-2 overflow-x-auto rounded-lg bg-slate-50 p-3 text-xs">
                        {JSON.stringify(event.metadata, null, 2)}
                      </pre>
                    </details>
                  )}
                </li>
              ))}
            </ul>
          )}
          <footer className="flex items-center justify-between border-t border-slate-100 px-5 py-4 text-sm text-slate-600">
            <span>{pagination.total} total events</span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => loadEvents(Math.max(0, pagination.offset - PAGE_SIZE))}
                disabled={loading || pagination.offset === 0}
                className="rounded-lg border border-slate-300 px-3 py-1.5 disabled:opacity-40"
              >
                Previous
              </button>
              <button
                type="button"
                onClick={() => loadEvents(pagination.offset + PAGE_SIZE)}
                disabled={loading || pagination.offset + PAGE_SIZE >= pagination.total}
                className="rounded-lg border border-slate-300 px-3 py-1.5 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </footer>
        </section>
      </div>
    </main>
  );
}
