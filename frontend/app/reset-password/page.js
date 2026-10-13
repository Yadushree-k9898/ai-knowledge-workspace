'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { getSupabaseClient } from '../../lib/supabase';

export default function ResetPasswordPage() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function checkResetSession() {
      try {
        const { data, error: sessionError } = await getSupabaseClient().auth.getSession();
        if (sessionError) {
          throw sessionError;
        }
        if (!data.session && mounted) {
          setError('This password reset link is invalid or has expired. Request a new link to continue.');
        }
        if (mounted) {
          setReady(true);
        }
      } catch (sessionError) {
        if (mounted) {
          setError(sessionError.message || 'Could not verify the password reset session.');
          setReady(true);
        }
      }
    }
    checkResetSession();
    return () => {
      mounted = false;
    };
  }, []);

  async function updatePassword(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    if (password.length < 8) {
      setError('Use a password with at least 8 characters.');
      return;
    }
    if (password !== confirmation) {
      setError('The passwords do not match.');
      return;
    }

    setBusy(true);
    try {
      const { error: updateError } = await getSupabaseClient().auth.updateUser({ password });
      if (updateError) {
        throw updateError;
      }
      setMessage('Your password has been updated. You can continue to your workspace.');
      window.setTimeout(() => router.replace('/dashboard'), 1200);
    } catch (updateError) {
      setError(updateError.message || 'Could not update your password.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
        <h1 className="text-2xl font-bold">Choose a new password</h1>
        <p className="mt-2 text-sm text-slate-600">Use at least 8 characters.</p>
        {error && <p role="alert" className="mt-5 rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
        {message && <p role="status" className="mt-5 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p>}
        {ready && !error && (
          <form onSubmit={updatePassword} className="mt-6 space-y-4">
            <div>
              <label htmlFor="password" className="block text-sm font-medium">New password</label>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                minLength={8}
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
              />
            </div>
            <div>
              <label htmlFor="confirm-password" className="block text-sm font-medium">Confirm password</label>
              <input
                id="confirm-password"
                type="password"
                autoComplete="new-password"
                minLength={8}
                required
                value={confirmation}
                onChange={(event) => setConfirmation(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
              />
            </div>
            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
            >
              {busy ? 'Updating…' : 'Update password'}
            </button>
          </form>
        )}
        {ready && error && (
          <Link href="/forgot-password" className="mt-5 inline-block text-sm font-semibold text-indigo-700 hover:underline">
            Request a new reset link
          </Link>
        )}
      </section>
    </main>
  );
}
