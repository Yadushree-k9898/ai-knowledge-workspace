'use client';

import { useEffect, useState } from 'react';
import { getSupabaseClient } from '../../lib/supabase';
import { getMyProfile, updateMyProfile } from '../../services/authService';

export default function AccountPage() {
  const [profile, setProfile] = useState(null);
  const [displayName, setDisplayName] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function loadProfile() {
      try {
        const { data, error: sessionError } = await getSupabaseClient().auth.getSession();
        if (sessionError) {
          throw sessionError;
        }
        if (!data.session) {
          throw new Error('Your session has expired. Sign in again.');
        }
        const result = await getMyProfile(data.session.access_token);
        if (mounted) {
          setProfile(result);
          setDisplayName(result.display_name);
          setAvatarUrl(result.avatar_url || '');
        }
      } catch (loadError) {
        if (mounted) {
          setError(loadError.message || 'Could not load your profile.');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    loadProfile();
    return () => {
      mounted = false;
    };
  }, []);

  async function saveProfile(event) {
    event.preventDefault();
    setSaving(true);
    setError('');
    setMessage('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) {
        throw sessionError;
      }
      if (!session) {
        throw new Error('Your session has expired. Sign in again.');
      }
      const updated = await updateMyProfile(session.access_token, {
        display_name: displayName.trim(),
        avatar_url: avatarUrl.trim() || null,
      });
      setProfile(updated);
      setDisplayName(updated.display_name);
      setAvatarUrl(updated.avatar_url || '');
      setMessage('Your profile has been updated.');
    } catch (saveError) {
      setError(saveError.message || 'Could not update your profile.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-2xl">
        <header>
          <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Account</p>
          <h1 className="mt-2 text-3xl font-bold">Profile settings</h1>
          <p className="mt-2 text-slate-600">Manage the profile associated with your sign-in.</p>
        </header>

        {error && <p role="alert" className="mt-6 rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
        {message && <p role="status" className="mt-6 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p>}

        <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          {loading ? (
            <p role="status" className="text-sm text-slate-500">Loading profile…</p>
          ) : profile ? (
            <form onSubmit={saveProfile} className="space-y-5">
              <div>
                <span className="block text-sm font-medium">Email</span>
                <p className="mt-1 rounded-lg bg-slate-50 px-3 py-2.5 text-sm text-slate-600">{profile.email}</p>
                <p className="mt-1 text-xs text-slate-500">Email address changes are managed by your identity provider.</p>
              </div>
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
                <label htmlFor="avatar-url" className="block text-sm font-medium">Avatar URL</label>
                <input
                  id="avatar-url"
                  type="url"
                  maxLength={500}
                  placeholder="https://example.com/avatar.png"
                  value={avatarUrl}
                  onChange={(event) => setAvatarUrl(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
                />
              </div>
              <button
                type="submit"
                disabled={saving}
                className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-wait disabled:opacity-60"
              >
                {saving ? 'Saving…' : 'Save profile'}
              </button>
            </form>
          ) : (
            <p className="text-sm text-slate-600">Profile information is unavailable.</p>
          )}
        </section>
      </div>
    </main>
  );
}
