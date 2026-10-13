'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { getSupabaseClient } from '../../../lib/supabase';
import { acceptInvitation, getInvitation } from '../../../services/organizationService';

export default function InvitationPage() {
  const { token } = useParams();
  const router = useRouter();
  const [invitation, setInvitation] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const invitationPath = `/invitations/${encodeURIComponent(token)}`;

  const loadInvitation = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [result, sessionResult] = await Promise.all([
        getInvitation(token),
        getSupabaseClient().auth.getSession(),
      ]);
      if (sessionResult.error) {
        throw sessionResult.error;
      }
      setInvitation(result);
      setSession(sessionResult.data.session);
    } catch (loadError) {
      setError(loadError.message || 'Could not load this invitation.');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadInvitation();
  }, [loadInvitation]);

  async function joinOrganization() {
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const { data: { session: currentSession }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) {
        throw sessionError;
      }
      if (!currentSession) {
        throw new Error('Sign in with the invited email address to accept this invitation.');
      }
      await acceptInvitation(token, currentSession.access_token);
      setMessage('Invitation accepted. Your organization is ready.');
      window.setTimeout(() => router.replace('/dashboard'), 1000);
    } catch (acceptError) {
      setError(acceptError.message || 'Could not accept this invitation.');
    } finally {
      setBusy(false);
    }
  }

  const unavailable = invitation?.is_expired || invitation?.is_accepted;

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <section className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
        <Link href="/" className="text-sm font-semibold text-indigo-700">AI Knowledge Workspace</Link>
        <h1 className="mt-6 text-2xl font-bold">Organization invitation</h1>
        {loading ? (
          <p role="status" className="mt-4 text-sm text-slate-500">Loading invitation…</p>
        ) : invitation ? (
          <>
            <p className="mt-4 text-slate-700">
              You’ve been invited to join <strong>{invitation.organization_name}</strong> as a{' '}
              <strong>{invitation.role.toLowerCase()}</strong>.
            </p>
            <p className="mt-2 text-sm text-slate-500">
              Invitation expires {new Date(invitation.expires_at).toLocaleString()}.
            </p>
            {invitation.is_accepted && (
              <p role="status" className="mt-5 rounded-lg bg-slate-100 p-3 text-sm text-slate-700">
                This invitation has already been accepted.
              </p>
            )}
            {invitation.is_expired && (
              <p role="alert" className="mt-5 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
                This invitation has expired. Ask an organization admin to send a new one.
              </p>
            )}
            {error && <p role="alert" className="mt-5 rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
            {message && <p role="status" className="mt-5 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p>}
            {!unavailable && !message && (session ? (
              <button
                type="button"
                onClick={joinOrganization}
                disabled={busy}
                className="mt-6 w-full rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
              >
                {busy ? 'Joining…' : 'Accept invitation'}
              </button>
            ) : (
              <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                <Link
                  href={`/login?next=${encodeURIComponent(invitationPath)}`}
                  className="flex-1 rounded-lg bg-indigo-600 px-4 py-3 text-center text-sm font-semibold text-white hover:bg-indigo-700"
                >
                  Sign in to accept
                </Link>
                <Link
                  href={`/signup?next=${encodeURIComponent(invitationPath)}`}
                  className="flex-1 rounded-lg border border-slate-300 px-4 py-3 text-center text-sm font-semibold hover:bg-slate-50"
                >
                  Create account
                </Link>
              </div>
            ))}
          </>
        ) : (
          <>
            {error && <p role="alert" className="mt-5 rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
            <button
              type="button"
              onClick={loadInvitation}
              className="mt-5 font-semibold text-indigo-700 hover:underline"
            >
              Try again
            </button>
          </>
        )}
      </section>
    </main>
  );
}