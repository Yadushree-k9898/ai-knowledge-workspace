'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { getSupabaseClient } from '../../../../lib/supabase';
import {
  createOrganizationInvitation,
  getOrganizationSettings,
  listOrganizationMembers,
  removeOrganizationMember,
  updateOrganizationMemberRole,
} from '../../../../services/organizationService';

export default function OrganizationMembersPage() {
  const { organizationId } = useParams();
  const router = useRouter();
  const [organization, setOrganization] = useState(null);
  const [members, setMembers] = useState([]);
  const [currentUserId, setCurrentUserId] = useState('');
  const [email, setEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('MEMBER');
  const [invitationUrl, setInvitationUrl] = useState('');
  const [copyMessage, setCopyMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [busyMemberId, setBusyMemberId] = useState('');
  const [creatingInvitation, setCreatingInvitation] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const loadMembers = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Sign in to view organization members.');

      const [organizationResult, memberResults] = await Promise.all([
        getOrganizationSettings(organizationId, session.access_token),
        listOrganizationMembers(organizationId, session.access_token),
      ]);
      setOrganization(organizationResult);
      setMembers(memberResults);
      setCurrentUserId(session.user.id);
    } catch (loadError) {
      setError(loadError.message || 'Could not load organization members.');
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  const canManage = organization?.role === 'OWNER' || organization?.role === 'ADMIN';

  async function withMemberAction(memberId, action) {
    setBusyMemberId(memberId);
    setError('');
    setMessage('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Your session has expired. Sign in again and retry.');
      await action(session.access_token);
    } catch (actionError) {
      setError(actionError.message || 'Could not update this member.');
    } finally {
      setBusyMemberId('');
    }
  }

  async function handleRoleChange(member, role) {
    if (role === member.role) return;
    await withMemberAction(member.id, async (accessToken) => {
      const updated = await updateOrganizationMemberRole(
        organizationId,
        member.id,
        role,
        accessToken,
      );
      setMembers((current) => current.map((item) => (
        item.id === member.id ? updated : item
      )));
      setMessage('Member role updated.');
    });
  }

  async function handleRemove(member) {
    const selfRemoval = member.user_id === currentUserId;
    const label = selfRemoval ? 'leave this organization' : 'remove this member';
    if (!window.confirm(`Are you sure you want to ${label}?`)) return;

    await withMemberAction(member.id, async (accessToken) => {
      await removeOrganizationMember(organizationId, member.id, accessToken);
      setMembers((current) => current.filter((item) => item.id !== member.id));
      setMessage(selfRemoval ? 'You left the organization.' : 'Member removed.');
      if (selfRemoval) router.replace('/organizations');
    });
  }

  async function handleInvite(event) {
    event.preventDefault();
    setCreatingInvitation(true);
    setError('');
    setMessage('');
    setInvitationUrl('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Your session has expired. Sign in again to invite a member.');
      const invitation = await createOrganizationInvitation(
        organizationId,
        { email: email.trim(), role: inviteRole },
        session.access_token,
      );
      setInvitationUrl(`${window.location.origin}/invitations/${encodeURIComponent(invitation.token)}`);
      setMessage(`Invitation created for ${invitation.email}. Share the link before it expires.`);
      setEmail('');
    } catch (inviteError) {
      setError(inviteError.message || 'Could not create the invitation.');
    } finally {
      setCreatingInvitation(false);
    }
  }

  async function copyInvitationUrl() {
    try {
      await navigator.clipboard.writeText(invitationUrl);
      setCopyMessage('Link copied.');
    } catch {
      setCopyMessage('Copy failed. Select and copy the invitation link manually.');
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <Link href={`/organizations/${encodeURIComponent(organizationId)}`} className="text-sm font-medium text-slate-600 hover:text-slate-950">
          ← Back to organization
        </Link>
        <header className="mt-8">
          <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Organization</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Members</h1>
          {organization && <p className="mt-2 text-slate-600">{organization.name} · Your role: {organization.role}</p>}
        </header>

        {error && <p role="alert" className="mt-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p>}
        {message && <p role="status" className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{message}</p>}

        {canManage && (
          <form onSubmit={handleInvite} className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">Invite a member</h2>
            <p className="mt-1 text-sm text-slate-500">Create an invitation link and share it with the invited person.</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_180px_auto] sm:items-end">
              <label htmlFor="invite-email" className="text-sm font-medium">
                Email address
                <input
                  id="invite-email"
                  type="email"
                  required
                  maxLength={320}
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  disabled={creatingInvitation}
                  className="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2.5"
                  placeholder="name@example.com"
                />
              </label>
              <label htmlFor="invite-role" className="text-sm font-medium">
                Role
                <select
                  id="invite-role"
                  value={inviteRole}
                  onChange={(event) => setInviteRole(event.target.value)}
                  disabled={creatingInvitation}
                  className="mt-2 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5"
                >
                  <option value="MEMBER">Member</option>
                  <option value="VIEWER">Viewer</option>
                  {organization?.role === 'OWNER' && <option value="ADMIN">Admin</option>}
                </select>
              </label>
              <button type="submit" disabled={creatingInvitation} className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
                {creatingInvitation ? 'Creating…' : 'Create invitation'}
              </button>
            </div>
            {invitationUrl && (
              <div className="mt-4 rounded-xl bg-slate-50 p-4">
                <label htmlFor="invitation-link" className="block text-sm font-medium">Invitation link</label>
                <div className="mt-2 flex gap-2">
                  <input id="invitation-link" readOnly value={invitationUrl} onFocus={(event) => event.target.select()} className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" />
                  <button type="button" onClick={copyInvitationUrl} className="shrink-0 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold hover:bg-slate-100">Copy</button>
                </div>
                {copyMessage && <p role="status" className="mt-2 text-sm text-slate-600">{copyMessage}</p>}
              </div>
            )}
          </form>
        )}

        <section className="mt-8">
          <h2 className="text-xl font-semibold">Organization members</h2>
          {loading ? (
            <p role="status" className="mt-4 rounded-xl bg-white p-5 text-sm text-slate-500">Loading members…</p>
          ) : members.length === 0 ? (
            <p className="mt-4 rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">No organization members were found.</p>
          ) : (
            <ul className="mt-4 divide-y divide-slate-200 overflow-hidden rounded-2xl border border-slate-200 bg-white">
              {members.map((member) => {
                const isOwner = member.role === 'OWNER';
                const isSelf = member.user_id === currentUserId;
                return (
                  <li key={member.id} className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between sm:px-5">
                    <div className="min-w-0">
                      <p className="break-all font-medium">{member.user_id}{isSelf ? ' (you)' : ''}</p>
                      <p className="mt-1 text-xs text-slate-500">Joined {new Date(member.joined_at).toLocaleDateString()}</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      {canManage && !isOwner ? (
                        <select
                          aria-label={`Role for ${member.user_id}`}
                          value={member.role}
                          disabled={busyMemberId === member.id}
                          onChange={(event) => handleRoleChange(member, event.target.value)}
                          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
                        >
                          <option value="MEMBER">Member</option>
                          <option value="VIEWER">Viewer</option>
                          {member.role === 'ADMIN' && organization?.role !== 'OWNER' && (
                            <option value="ADMIN">Admin</option>
                          )}
                          {organization?.role === 'OWNER' && <option value="ADMIN">Admin</option>}
                        </select>
                      ) : (
                        <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">{member.role}</span>
                      )}
                      {(canManage || isSelf) && !isOwner && (
                        <button
                          type="button"
                          disabled={busyMemberId === member.id}
                          onClick={() => handleRemove(member)}
                          className="rounded-lg border border-rose-200 px-3 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-50 disabled:opacity-50"
                        >
                          {isSelf ? 'Leave organization' : 'Remove'}
                        </button>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
          {!canManage && !loading && members.length > 0 && (
            <p className="mt-3 text-sm text-slate-500">Only organization owners and admins can invite members or change other members&apos; roles.</p>
          )}
        </section>
      </div>
    </main>
  );
}
