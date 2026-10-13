'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { getSupabaseClient } from '../../lib/supabase';
import { safeReturnPath } from '../../services/authService';

function getDestination() {
  if (typeof window === 'undefined') {
    return '/dashboard';
  }
  return safeReturnPath(new URLSearchParams(window.location.search).get('next'));
}

export default function SignupPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function signUp(event) {
    event.preventDefault();
    setMessage('');
    setError('');
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
      const redirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(getDestination())}`;
      const { data, error: signUpError } = await getSupabaseClient().auth.signUp({
        email: email.trim().toLowerCase(),
        password,
        options: {
          emailRedirectTo: redirectTo,
          data: { display_name: displayName.trim() },
        },
      });
      if (signUpError) {
        throw signUpError;
      }
      if (data.session) {
        router.replace(getDestination());
        return;
      }
      setMessage('Check your email for a verification link. After confirming your address, you’ll be returned to your workspace.');
    } catch (authError) {
      setError(authError.message || 'Could not create your account.');
    } finally {
      setBusy(false);
    }
  }

  async function signUpWithGoogle() {
    setError('');
    setBusy(true);
    try {
      const redirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(getDestination())}`;
      const { error: oauthError } = await getSupabaseClient().auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo,
          queryParams: { prompt: 'select_account' },
        },
      });
      if (oauthError) {
        throw oauthError;
      }
    } catch (authError) {
      setError(authError.message || 'Could not start Google sign-up.');
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
        <Link href="/" className="text-sm font-semibold text-indigo-700">AI Knowledge Workspace</Link>
        <h1 className="mt-6 text-2xl font-bold">Create your account</h1>
        <p className="mt-2 text-sm text-slate-600">Start organizing and researching your knowledge.</p>

        {error && <p role="alert" className="mt-5 rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
        {message && <p role="status" className="mt-5 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p>}

        <button
          type="button"
          onClick={signUpWithGoogle}
          disabled={busy}
          className="mt-6 w-full rounded-lg border border-slate-300 px-4 py-3 text-sm font-semibold hover:bg-slate-50 disabled:opacity-60"
        >
          Continue with Google
        </button>

        <div className="my-5 flex items-center gap-3 text-xs text-slate-400">
          <span className="h-px flex-1 bg-slate-200" />
          OR WITH EMAIL
          <span className="h-px flex-1 bg-slate-200" />
        </div>

        <form onSubmit={signUp} className="space-y-4">
          <div>
            <label htmlFor="display-name" className="block text-sm font-medium">Display name</label>
            <input
              id="display-name"
              autoComplete="name"
              required
              minLength={2}
              maxLength={100}
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
            />
          </div>
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
          <div>
            <label htmlFor="password" className="block text-sm font-medium">Password</label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
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
              required
              minLength={8}
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
            />
          </div>
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-wait disabled:opacity-60"
          >
            {busy ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-600">
          Already have an account?{' '}
          <Link href={`/login?next=${encodeURIComponent(getDestination())}`} className="font-semibold text-indigo-700 hover:underline">
            Sign in
          </Link>
        </p>
      </section>
    </main>
  );
}