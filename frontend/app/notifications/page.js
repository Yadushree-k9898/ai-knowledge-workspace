'use client';

import { useCallback, useEffect, useState } from 'react';
import { getSupabaseClient } from '../../lib/supabase';
import {
  getNotifications,
  markNotificationRead,
  markNotificationUnread,
} from '../../services/notificationService';

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

export default function NotificationsPage() {
  const [accessToken, setAccessToken] = useState('');
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updatingId, setUpdatingId] = useState('');

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) {
        throw sessionError;
      }
      if (!session) {
        throw new Error('Sign in to view your notifications.');
      }

      setAccessToken(session.access_token);
      const rows = await getNotifications(session.access_token);
      if (!Array.isArray(rows)) {
        throw new Error('The API returned an invalid notification list.');
      }
      setNotifications(rows);
    } catch (loadError) {
      setError(loadError.message || 'Could not load notifications.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  async function toggleRead(notification) {
    setUpdatingId(notification.id);
    setError('');
    try {
      const updated = notification.read_at
        ? await markNotificationUnread(notification.id, accessToken)
        : await markNotificationRead(notification.id, accessToken);
      setNotifications((current) => current.map((item) => (
        item.id === updated.id ? updated : item
      )));
    } catch (updateError) {
      setError(updateError.message || 'Could not update this notification.');
    } finally {
      setUpdatingId('');
    }
  }

  const unreadCount = notifications.filter((notification) => !notification.read_at).length;

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">
              Workspace
            </p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight">Notifications</h1>
            <p className="mt-2 text-slate-600">
              {unreadCount
                ? `${unreadCount} unread notification${unreadCount === 1 ? '' : 's'}`
                : 'You’re all caught up.'}
            </p>
          </div>
          <button
            type="button"
            onClick={loadNotifications}
            disabled={loading}
            className="self-start rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-wait disabled:opacity-60 sm:self-auto"
          >
            Refresh
          </button>
        </header>

        {error && (
          <div
            role="alert"
            className="mt-6 flex items-start justify-between gap-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
          >
            <p>{error}</p>
            <button
              type="button"
              onClick={loadNotifications}
              className="shrink-0 font-semibold underline underline-offset-2"
            >
              Retry
            </button>
          </div>
        )}

        {loading ? (
          <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <p role="status" className="text-sm text-slate-500">Loading notifications…</p>
          </section>
        ) : notifications.length === 0 ? (
          <section className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
            <h2 className="text-base font-semibold">No notifications yet</h2>
            <p className="mt-1 text-sm text-slate-500">
              Updates about documents, reports, and organization invitations will appear here.
            </p>
          </section>
        ) : (
          <ul className="mt-8 space-y-3">
            {notifications.map((notification) => {
              const unread = !notification.read_at;
              const actionBusy = updatingId === notification.id;
              return (
                <li
                  key={notification.id}
                  className={`rounded-2xl border bg-white p-5 shadow-sm ${
                    unread ? 'border-indigo-200' : 'border-slate-200'
                  }`}
                >
                  <article className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        {unread && (
                          <span
                            aria-label="Unread"
                            className="h-2 w-2 shrink-0 rounded-full bg-indigo-600"
                          />
                        )}
                        <h2 className="font-semibold">{notification.title}</h2>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-slate-600">
                        {notification.message}
                      </p>
                      <time
                        className="mt-3 block text-xs text-slate-500"
                        dateTime={notification.created_at}
                      >
                        {formatDate(notification.created_at)}
                      </time>
                      {notification.link && (
                        <a
                          href={notification.link}
                          className="mt-3 inline-block text-sm font-semibold text-indigo-700 underline underline-offset-2"
                        >
                          View update
                        </a>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => toggleRead(notification)}
                      disabled={actionBusy}
                      className="shrink-0 self-start rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-wait disabled:opacity-60"
                    >
                      {actionBusy ? 'Saving…' : unread ? 'Mark as read' : 'Mark as unread'}
                    </button>
                  </article>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </main>
  );
}