'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';
import { getSupabaseClient } from '../lib/supabase';
import { bootstrapProfile } from '../services/authService';

const PUBLIC_PATHS = new Set([
  '/',
  '/login',
  '/signup',
  '/forgot-password',
  '/reset-password',
  '/auth/callback',
]);

function isPublicPath(pathname) {
  return PUBLIC_PATHS.has(pathname) || pathname.startsWith('/invitations/');
}

export default function AuthBoundary({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const [session, setSession] = useState(null);
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');
  const verifiedUserId = useRef('');

  const verifySession = useCallback(async (activeSession) => {
    if (!activeSession) {
      verifiedUserId.current = '';
      setSession(null);
      setStatus('anonymous');
      return;
    }

    setSession(activeSession);
    if (verifiedUserId.current === activeSession.user.id) {
      setStatus('authenticated');
      return;
    }

    setStatus('checking-profile');
    setError('');
    try {
      await bootstrapProfile(activeSession);
      verifiedUserId.current = activeSession.user.id;
      setStatus('authenticated');
    } catch (bootstrapError) {
      setError(bootstrapError.message || 'Could not initialize your application profile.');
      setStatus('profile-error');
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    let checkingInitialSession = true;
    let client;
    try {
      client = getSupabaseClient();
    } catch (configurationError) {
      setError(configurationError.message);
      setStatus('session-error');
      return undefined;
    }

    const { data: { subscription } } = client.auth.onAuthStateChange((_event, newSession) => {
      if (!mounted) {
        return;
      }
      setSession(newSession);
      if (!checkingInitialSession) {
        setStatus(newSession ? 'checking-profile' : 'anonymous');
        window.setTimeout(() => {
          if (mounted) {
            verifySession(newSession);
          }
        }, 0);
      }
    });

    client.auth.getSession()
      .then(({ data, error: sessionError }) => {
        if (!mounted) {
          return;
        }
        checkingInitialSession = false;
        if (sessionError) {
          setError(sessionError.message);
          setStatus('session-error');
          return;
        }
        return verifySession(data.session);
      })
      .catch((sessionError) => {
        if (mounted) {
          checkingInitialSession = false;
          setError(sessionError.message || 'Could not verify your session.');
          setStatus('session-error');
        }
      });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, [verifySession]);

  useEffect(() => {
    if (isPublicPath(pathname) || status === 'loading' || status === 'checking-profile') {
      return;
    }
    if (status === 'anonymous') {
      router.replace(`/login?next=${encodeURIComponent(pathname || '/dashboard')}`);
    }
  }, [pathname, router, status]);

  async function signOut() {
    setError('');
    const { error: signOutError } = await getSupabaseClient().auth.signOut();
    if (signOutError) {
      setError(signOutError.message);
      return;
    }
    verifiedUserId.current = '';
    router.replace('/login');
  }

  if (isPublicPath(pathname)) {
    return children;
  }
  if (status === 'loading' || status === 'checking-profile' || status === 'anonymous') {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
        <p role="status" className="text-sm text-slate-600">
          {status === 'checking-profile' ? 'Preparing your workspace…' : 'Checking your session…'}
        </p>
      </main>
    );
  }
  if (status === 'profile-error' || status === 'session-error') {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
        <section className="w-full max-w-lg rounded-2xl border border-rose-200 bg-white p-6 shadow-sm">
          <h1 className="text-lg font-semibold">Could not verify your account</h1>
          <p role="alert" className="mt-2 text-sm text-rose-700">{error}</p>
          <div className="mt-5 flex gap-3">
            <button
              type="button"
              onClick={() => verifySession(session)}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white"
            >
              Retry
            </button>
            <button
              type="button"
              onClick={signOut}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold"
            >
              Sign out
            </button>
          </div>
        </section>
      </main>
    );
  }

  return (
    <>
      <nav className="border-b border-slate-200 bg-white px-4 py-3 sm:px-6">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          <Link href="/dashboard" className="font-semibold text-slate-900">
            AI Knowledge Workspace
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <Link href="/dashboard" className="text-slate-600 hover:text-slate-900">Dashboard</Link>
            <Link href="/notifications" className="text-slate-600 hover:text-slate-900">Notifications</Link>
            <Link href="/account" className="text-slate-600 hover:text-slate-900">Account</Link>
            <button
              type="button"
              onClick={signOut}
              className="font-semibold text-indigo-700 hover:text-indigo-900"
            >
              Sign out
            </button>
          </div>
        </div>
      </nav>
      {error && (
        <p role="alert" className="bg-rose-50 px-4 py-2 text-center text-sm text-rose-800">
          {error}
        </p>
      )}
      {children}
    </>
  );
}
