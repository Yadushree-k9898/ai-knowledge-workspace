'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { getSupabaseClient } from '../../../../lib/supabase';
import {
  createProjectConversation,
  getProjectConversation,
  listProjectConversations,
  sendProjectConversationMessage,
} from '../../../../services/chatService';

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

export default function ProjectChatPage() {
  const params = useParams();
  const projectId = Array.isArray(params.projectId) ? params.projectId[0] : params.projectId;
  const [accessToken, setAccessToken] = useState('');
  const [currentUserId, setCurrentUserId] = useState('');
  const [query, setQuery] = useState('');
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [openingConversation, setOpeningConversation] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const loadConversations = useCallback(async () => {
    setLoadingHistory(true);
    setError('');
    setAccessToken('');
    setCurrentUserId('');
    setConversations([]);
    setActiveConversation(null);
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Sign in to view this project’s conversations.');

      setAccessToken(session.access_token);
      setCurrentUserId(session.user.id);
      const results = await listProjectConversations(projectId, session.access_token);
      setConversations(results);
      if (results.length > 0) {
        const detail = await getProjectConversation(
          projectId,
          results[0].id,
          session.access_token,
        );
        setActiveConversation(detail);
      }
    } catch (loadError) {
      setError(loadError.message || 'Could not load project conversations.');
    } finally {
      setLoadingHistory(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  async function openConversation(conversationId) {
    setOpeningConversation(true);
    setError('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Your session has expired. Sign in again.');
      setAccessToken(session.access_token);
      setCurrentUserId(session.user.id);
      setActiveConversation(await getProjectConversation(
        projectId,
        conversationId,
        session.access_token,
      ));
    } catch (openError) {
      setError(openError.message || 'Could not open this conversation.');
    } finally {
      setOpeningConversation(false);
    }
  }

  function startNewConversation() {
    setActiveConversation(null);
    setQuery('');
    setError('');
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const question = query.trim();
    if (!question) {
      setError('Enter a question.');
      return;
    }

    setSending(true);
    setError('');
    setQuery('');
    try {
      let token = accessToken;
      if (!token) {
        const { data: { session }, error: sessionError } =
          await getSupabaseClient().auth.getSession();
        if (sessionError) throw sessionError;
        if (!session) throw new Error('Sign in to ask questions about this project.');
        token = session.access_token;
        setAccessToken(token);
        setCurrentUserId(session.user.id);
      }

      const result = activeConversation
        ? await sendProjectConversationMessage(
          projectId,
          activeConversation.conversation.id,
          question,
          token,
        )
        : await createProjectConversation(projectId, question, token);

      setActiveConversation(result);
      setConversations((current) => [
        result.conversation,
        ...current.filter((conversation) => conversation.id !== result.conversation.id),
      ]);
    } catch (chatError) {
      setQuery(question);
      setError(chatError.message || 'Could not get an answer.');
    } finally {
      setSending(false);
    }
  }

  const messages = activeConversation?.messages || [];
  const activeConversationId = activeConversation?.conversation.id;

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6">
      <div className="mx-auto max-w-6xl">
        <Link href={`/projects/${encodeURIComponent(projectId)}`} className="text-sm font-medium text-slate-600 hover:text-slate-950">
          ← Back to project
        </Link>
        <header className="mt-8">
          <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Project</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Ask your documents</h1>
          <p className="mt-2 text-slate-600">
            Conversations are shared with project members. Answers use linked documents and keep source citations.
          </p>
        </header>

        {error && (
          <div role="alert" className="mt-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            <p>{error}</p>
            <button type="button" onClick={loadConversations} className="mt-2 font-semibold underline">
              Reload conversations
            </button>
          </div>
        )}

        <div className="mt-8 grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between gap-2">
              <h2 className="font-semibold">History</h2>
              <button
                type="button"
                onClick={startNewConversation}
                disabled={sending || loadingHistory}
                className="rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                New chat
              </button>
            </div>
            {loadingHistory ? (
              <p role="status" className="mt-4 text-sm text-slate-500">Loading conversations…</p>
            ) : conversations.length === 0 ? (
              <p className="mt-4 text-sm leading-6 text-slate-500">Your project conversations will appear here.</p>
            ) : (
              <ul className="mt-4 max-h-[60vh] space-y-2 overflow-y-auto">
                {conversations.map((conversation) => (
                  <li key={conversation.id}>
                    <button
                      type="button"
                      onClick={() => openConversation(conversation.id)}
                      disabled={sending || openingConversation}
                      aria-current={conversation.id === activeConversationId ? 'page' : undefined}
                      className={`w-full rounded-xl p-3 text-left transition ${
                        conversation.id === activeConversationId
                          ? 'bg-indigo-50 text-indigo-950 ring-1 ring-indigo-200'
                          : 'hover:bg-slate-50'
                      } disabled:opacity-50`}
                    >
                      <span className="block line-clamp-2 text-sm font-medium">{conversation.title}</span>
                      <span className="mt-2 block text-xs text-slate-500">{formatDate(conversation.updated_at)}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </aside>

          <section className="min-w-0">
            <div aria-live="polite" className="min-h-[320px] space-y-5 rounded-2xl border border-slate-200 bg-slate-100/70 p-4 sm:p-6">
              {openingConversation ? (
                <p role="status" className="text-sm text-slate-500">Opening conversation…</p>
              ) : messages.length === 0 ? (
                <div className="flex min-h-[280px] items-center justify-center text-center">
                  <div>
                    <h2 className="font-semibold">Start a project conversation</h2>
                    <p className="mt-2 max-w-md text-sm leading-6 text-slate-600">
                      Ask about the project’s linked documents. The thread will be saved and shared with the project team.
                    </p>
                  </div>
                </div>
              ) : messages.map((message) => {
                const isUserMessage = message.role === 'USER';
                const isCurrentUser = message.user_id === currentUserId;
                return (
                  <article
                    key={message.id}
                    className={`max-w-3xl rounded-2xl p-4 text-sm shadow-sm ${
                      isUserMessage
                        ? 'ml-auto bg-indigo-600 text-white'
                        : 'border border-slate-200 bg-white text-slate-700'
                    }`}
                  >
                    <p className={`font-semibold ${isUserMessage ? 'text-indigo-100' : 'text-slate-900'}`}>
                      {isUserMessage ? (isCurrentUser ? 'You' : 'Project member') : 'Assistant'}
                    </p>
                    <p className="mt-1 whitespace-pre-wrap leading-6">{message.content}</p>
                    {!isUserMessage && message.sources.length > 0 && (
                      <div className="mt-4 border-t border-slate-100 pt-3">
                        <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Sources</h3>
                        <ul className="mt-2 space-y-2">
                          {message.sources.map((source) => (
                            <li key={`${source.document_id}-${source.chunk_id}`} className="rounded-lg bg-slate-50 p-3">
                              <p className="text-sm font-medium text-indigo-700">{source.filename}</p>
                              <p className="mt-1 text-xs leading-5 text-slate-600">{source.text_preview}</p>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </article>
                );
              })}
              {sending && <p role="status" className="text-sm text-slate-500">Preparing an answer…</p>}
            </div>

            <form onSubmit={handleSubmit} className="mt-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <label htmlFor="project-chat-query" className="block text-sm font-medium">
                Your question
                <textarea
                  id="project-chat-query"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  maxLength={4000}
                  required
                  rows={3}
                  disabled={sending || openingConversation}
                  placeholder="Ask a question or follow up on this conversation"
                  className="mt-2 block w-full resize-y rounded-lg border border-slate-300 px-3 py-2.5"
                />
              </label>
              <button type="submit" disabled={sending || openingConversation || loadingHistory} className="mt-3 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
                {sending ? 'Thinking…' : 'Send'}
              </button>
            </form>
          </section>
        </div>
      </div>
    </main>
  );
}
