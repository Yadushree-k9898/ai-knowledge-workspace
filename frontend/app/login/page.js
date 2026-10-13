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

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function signIn(event) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      const { error: signInError } = await getSupabaseClient().auth.signInWithPassword({
        email: email.trim().toLowerCase(),
        password,
      });
      if (signInError) {
        throw signInError;
      }
      router.replace(getDestination());
    } catch (authError) {
      setError(authError.message || 'Could not sign in.');
    } finally {
      setBusy(false);
    }
  }

  async function signInWithGoogle() {
    setError('');
    setBusy(true);
    try {
      const redirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(getDestination())}`;
      const { error: oauthError } = await getSupabaseClient().auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo },
      });
      if (oauthError) {
        throw oauthError;
      }
    } catch (authError) {
      setError(authError.message || 'Could not start Google sign-in.');
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
        <Link href="/" className="text-sm font-semibold text-indigo-700">AI Knowledge Workspace</Link>
        <h1 className="mt-6 text-2xl font-bold">Sign in</h1>
        <p className="mt-2 text-sm text-slate-600">Use your account to continue to your workspace.</p>

        {error && <p role="alert" className="mt-5 rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}

        <button
          type="button"
          onClick={signInWithGoogle}
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

        <form onSubmit={signIn} className="space-y-4">
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
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
            />
          </div>
          <div className="text-right">
            <Link href="/forgot-password" className="text-sm font-medium text-indigo-700 hover:underline">
              Forgot password?
            </Link>
          </div>
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-wait disabled:opacity-60"
          >
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-600">
          New here?{' '}
          <Link href={`/signup?next=${encodeURIComponent(getDestination())}`} className="font-semibold text-indigo-700 hover:underline">
            Create an account
          </Link>
        </p>
      </section>
    </main>
  );
}