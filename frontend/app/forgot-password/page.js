'use client';

import Link from 'next/link';
import { useState } from 'react';
import { getSupabaseClient } from '../../lib/supabase';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function sendResetLink(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const redirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent('/reset-password')}`;
      const { error: resetError } = await getSupabaseClient().auth.resetPasswordForEmail(
        email.trim().toLowerCase(),
        { redirectTo },
      );
      if (resetError) {
        throw resetError;
      }
      setMessage('If an account exists for that address, a password reset link is on its way.');
    } catch (requestError) {
      setError(requestError.message || 'Could not send the password reset email.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
        <Link href="/login" className="text-sm font-semibold text-indigo-700">Back to sign in</Link>
        <h1 className="mt-6 text-2xl font-bold">Reset your password</h1>
        <p className="mt-2 text-sm text-slate-600">We’ll email you a secure link to choose a new password.</p>
        {error && <p role="alert" className="mt-5 rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
        {message && <p role="status" className="mt-5 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p>}
        <form onSubmit={sendResetLink} className="mt-6 space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium">Email</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
            />
          </div>
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
          >
            {busy ? 'Sending…' : 'Send reset link'}
          </button>
        </form>
      </section>
    </main>
  );
}
