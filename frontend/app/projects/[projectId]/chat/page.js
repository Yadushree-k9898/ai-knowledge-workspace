'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { getSupabaseClient } from '../../../../lib/supabase';
import { askProjectQuestion } from '../../../../services/chatService';

export default function ProjectChatPage() {
  const { projectId } = useParams();
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    const question = query.trim();
    if (!question) {
      setError('Enter a question.');
      return;
    }

    setLoading(true);
    setError('');
    setQuery('');
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Sign in to ask questions about this project.');

      const result = await askProjectQuestion(
        projectId,
        question,
        session.access_token,
      );
      setMessages((current) => [
        ...current,
        { question, answer: result.answer, sources: result.sources },
      ]);
    } catch (chatError) {
      setQuery(question);
      setError(chatError.message || 'Could not get an answer.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl">
        <Link href={`/projects/${encodeURIComponent(projectId)}`} className="text-sm font-medium text-slate-600 hover:text-slate-950">
            ← Back to project
        </Link>
        <header className="mt-8">
          <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Project</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Ask your documents</h1>
          <p className="mt-2 text-slate-600">
            Answers use documents linked to this project and include source citations.
          </p>
        </header>

        <section aria-live="polite" className="mt-8 space-y-5">
          {messages.map((message, index) => (
            <article key={`${index}-${message.question}`} className="space-y-3">
              <div className="ml-auto max-w-3xl rounded-2xl bg-indigo-600 p-4 text-sm text-white">
                <p className="font-semibold">You</p>
                <p className="mt-1 whitespace-pre-wrap">{message.question}</p>
              </div>
              <div className="max-w-3xl rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <p className="font-semibold text-slate-900">Answer</p>
                <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{message.answer}</p>
                {message.sources.length > 0 && (
                  <div className="mt-4 border-t border-slate-100 pt-3">
                    <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Sources</h2>
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
              </div>
            </article>
          ))}
        </section>

        {error && <p role="alert" className="mt-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p>}

        <form onSubmit={handleSubmit} className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <label htmlFor="project-chat-query" className="block text-sm font-medium">
            Your question
            <textarea
              id="project-chat-query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              maxLength={4000}
              required
              rows={3}
              placeholder="Ask a question about this project's documents"
              className="mt-2 block w-full resize-y rounded-lg border border-slate-300 px-3 py-2.5"
            />
          </label>
          <button type="submit" disabled={loading} className="mt-3 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
            {loading ? 'Thinking…' : 'Ask question'}
          </button>
        </form>
      </div>
    </main>
  );
}
