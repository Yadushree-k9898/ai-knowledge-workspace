'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getSupabaseClient } from '../../../lib/supabase';
import { bootstrapProfile, safeReturnPath } from '../../../services/authService';

export default function AuthCallbackPage() {
  const router = useRouter();
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function completeAuthentication() {
      try {
        const url = new URL(window.location.href);
        const code = url.searchParams.get('code');
        const client = getSupabaseClient();
        if (code) {
          const { error: exchangeError } = await client.auth.exchangeCodeForSession(code);
          if (exchangeError) {
            throw exchangeError;
          }
          url.searchParams.delete('code');
          window.history.replaceState(
            {},
            '',
            `${url.pathname}${url.search}${url.hash}`,
          );
        } else {
          const providerError = url.searchParams.get('error_description');
          if (providerError) {
            throw new Error(providerError);
          }
        }

        const { data: { session }, error: sessionError } = await client.auth.getSession();
        if (sessionError) {
          throw sessionError;
        }
        if (!session) {
          throw new Error('The sign-in link is invalid or has expired.');
        }

        await bootstrapProfile(session);
        if (!cancelled) {
          const destination = safeReturnPath(url.searchParams.get('next'));
          router.replace(destination);
        }
      } catch (callbackError) {
        if (!cancelled) {
          setError(callbackError.message || 'Could not complete sign-in.');
        }
      }
    }

    completeAuthentication();
    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-7 text-center shadow-sm">
        {error ? (
          <>
            <h1 className="text-xl font-bold">Sign-in link could not be used</h1>
            <p role="alert" className="mt-3 text-sm text-rose-700">{error}</p>
            <Link href="/login" className="mt-5 inline-block font-semibold text-indigo-700 hover:underline">
              Return to sign in
            </Link>
          </>
        ) : (
          <>
            <h1 className="text-xl font-bold">Completing sign in</h1>
            <p role="status" className="mt-3 text-sm text-slate-600">
              Verifying your account and preparing your workspace…
            </p>
          </>
        )}
      </section>
    </main>
  );
}
