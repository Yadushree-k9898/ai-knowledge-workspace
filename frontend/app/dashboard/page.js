'use client';

import { useCallback, useEffect, useState } from 'react';
import { getSupabaseClient } from '../../lib/supabase';
import {
  getOrganizationAnalytics,
  getUserOrganizations,
} from '../../services/analyticsService';

const METRICS = [
  { key: 'documents_uploaded', label: 'Documents uploaded', description: 'Project-linked uploads in this period' },
  { key: 'documents_processed', label: 'Documents processed', description: 'Processing outcomes are not recorded yet' },
  { key: 'reports_generated', label: 'Reports generated', description: 'Reports completed in this period' },
  { key: 'active_users', label: 'Active users', description: 'Members with recorded activity' },
  { key: 'questions_asked', label: 'Questions asked', description: 'Chat usage is not recorded yet' },
  { key: 'searches', label: 'Searches', description: 'Search activity is not recorded yet' },
  { key: 'processing_failures', label: 'Processing failures', description: 'Processing outcomes are not recorded yet' },
  { key: 'average_response_latency_ms', label: 'Average response latency', description: 'Latency data is not recorded yet', format: (value) => `${Math.round(value)} ms` },
  { key: 'ai_usage', label: 'AI usage', description: 'Token usage is not recorded yet' },
];

function localDateString(value) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function initialDateRange() {
  const today = new Date();
  const start = new Date(today);
  start.setDate(start.getDate() - 29);
  return { dateFrom: localDateString(start), dateTo: localDateString(today) };
}

function MetricCard({ metric, value }) {
  const notTracked = value === null || value === undefined;
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-sm font-medium text-slate-600">{metric.label}</h2>
      <p className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
        {notTracked ? 'Not tracked' : metric.format ? metric.format(value) : value.toLocaleString()}
      </p>
      <p className="mt-2 text-xs text-slate-500">{metric.description}</p>
    </article>
  );
}

export default function DashboardPage() {
  const initialRange = initialDateRange();
  const [accessToken, setAccessToken] = useState('');
  const [organizations, setOrganizations] = useState([]);
  const [organizationId, setOrganizationId] = useState('');
  const [dateFrom, setDateFrom] = useState(initialRange.dateFrom);
  const [dateTo, setDateTo] = useState(initialRange.dateTo);
  const [appliedRange, setAppliedRange] = useState(initialRange);
  const [analytics, setAnalytics] = useState(null);
  const [loadingOrganizations, setLoadingOrganizations] = useState(true);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [error, setError] = useState('');

  const loadOrganizations = useCallback(async () => {
    setLoadingOrganizations(true);
    setError('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) {
        throw sessionError;
      }
      if (!session) {
        throw new Error('Sign in to view organization analytics.');
      }

      const memberships = await getUserOrganizations(session.access_token);
      setAccessToken(session.access_token);
      setOrganizations(memberships);
      setOrganizationId((current) => (
        memberships.some((organization) => organization.id === current)
          ? current
          : memberships[0]?.id || ''
      ));
    } catch (loadError) {
      setError(loadError.message || 'Could not load your organizations.');
    } finally {
      setLoadingOrganizations(false);
    }
  }, []);

  useEffect(() => {
    loadOrganizations();
  }, [loadOrganizations]);

  useEffect(() => {
    if (!organizationId || !accessToken || loadingOrganizations) {
      return undefined;
    }

    let cancelled = false;
    setLoadingAnalytics(true);
    setAnalytics(null);
    setError('');

    getOrganizationAnalytics(
      organizationId,
      appliedRange.dateFrom,
      appliedRange.dateTo,
      accessToken,
    )
      .then((result) => {
        if (!cancelled) {
          setAnalytics(result);
        }
      })
      .catch((analyticsError) => {
        if (!cancelled) {
          setError(analyticsError.message || 'Could not load analytics.');
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingAnalytics(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [organizationId, accessToken, appliedRange, loadingOrganizations]);

  function handleDateSubmit(event) {
    event.preventDefault();
    setError('');
    if (dateFrom > dateTo) {
      setError('Start date must be on or before end date.');
      return;
    }
    setAppliedRange({ dateFrom, dateTo });
  }

  const organizationName = organizations.find((item) => item.id === organizationId)?.name;
  const noOrganizations = !loadingOrganizations && organizations.length === 0;

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">
              Workspace
            </p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight">Analytics</h1>
            <p className="mt-2 text-slate-600">
              Usage overview for your organization.
            </p>
          </div>
          {!loadingOrganizations && organizations.length > 1 && (
            <div className="w-full sm:max-w-xs">
              <label htmlFor="analytics-organization" className="block text-sm font-medium">
                Organization
              </label>
              <select
                id="analytics-organization"
                value={organizationId}
                onChange={(event) => setOrganizationId(event.target.value)}
                className="mt-2 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
              >
                {organizations.map((organization) => (
                  <option key={organization.id} value={organization.id}>
                    {organization.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </header>

        {error && (
          <div
            role="alert"
            className="mt-6 flex items-start justify-between gap-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
          >
            <p>{error}</p>
            <button
              type="button"
              onClick={loadOrganizations}
              className="shrink-0 font-semibold underline underline-offset-2"
            >
              Retry
            </button>
          </div>
        )}

        {loadingOrganizations ? (
          <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <p role="status" className="text-sm text-slate-500">Loading your workspace…</p>
          </section>
        ) : noOrganizations ? (
          <section className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
            <h2 className="text-base font-semibold">No organizations yet</h2>
            <p className="mt-1 text-sm text-slate-500">
              Join or create an organization to see its analytics.
            </p>
          </section>
        ) : (
          <>
            <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <h2 className="text-base font-semibold">
                    {organizationName || 'Organization'} usage
                  </h2>
                  <p className="mt-1 text-sm text-slate-500">
                    Choose an inclusive date range for the metrics below.
                  </p>
                </div>
                <form onSubmit={handleDateSubmit} className="flex flex-col gap-3 sm:flex-row sm:items-end">
                  <div>
                    <label htmlFor="analytics-date-from" className="block text-xs font-medium text-slate-600">
                      From
                    </label>
                    <input
                      id="analytics-date-from"
                      type="date"
                      required
                      value={dateFrom}
                      max={dateTo || undefined}
                      onChange={(event) => setDateFrom(event.target.value)}
                      className="mt-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
                    />
                  </div>
                  <div>
                    <label htmlFor="analytics-date-to" className="block text-xs font-medium text-slate-600">
                      To
                    </label>
                    <input
                      id="analytics-date-to"
                      type="date"
                      required
                      value={dateTo}
                      min={dateFrom || undefined}
                      onChange={(event) => setDateTo(event.target.value)}
                      className="mt-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={loadingAnalytics}
                    className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700 focus:outline-none focus:ring-4 focus:ring-indigo-200 disabled:cursor-wait disabled:opacity-60"
                  >
                    Apply dates
                  </button>
                </form>
              </div>
            </section>

            {analytics?.unavailable_metrics?.length > 0 && (
              <p className="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                Some activity is not recorded yet. Unsupported metrics are shown as “Not tracked,”
                not as zero.
              </p>
            )}

            {loadingAnalytics ? (
              <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
                <p role="status" className="text-sm text-slate-500">Loading analytics…</p>
              </section>
            ) : analytics ? (
              <section
                className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
                aria-label="Organization analytics metrics"
              >
                {METRICS.map((metric) => (
                  <MetricCard key={metric.key} metric={metric} value={analytics[metric.key]} />
                ))}
              </section>
            ) : !error ? (
              <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
                <p role="status" className="text-sm text-slate-500">
                  Select an organization to load analytics.
                </p>
              </section>
            ) : null}

            {analytics && (
              <p className="mt-4 text-right text-xs text-slate-500">
                {analytics.date_from} – {analytics.date_to}
              </p>
            )}
          </>
        )}
      </div>
    </main>
  );
}