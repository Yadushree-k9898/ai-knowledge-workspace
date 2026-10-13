'use client';

import { useParams } from 'next/navigation';
import { useState } from 'react';
import Link from 'next/link';
import { getSupabaseClient } from '../../../../lib/supabase';
import { searchProjectDocuments } from '../../../../services/searchService';

export default function ProjectSearchPage() {
  const { projectId } = useParams();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSearch(event) {
    event.preventDefault();
    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      setError('Enter a search query.');
      return;
    }

    setLoading(true);
    setError('');
    setSearched(true);
    try {
      const { data: { session }, error: sessionError } =
        await getSupabaseClient().auth.getSession();
      if (sessionError) throw sessionError;
      if (!session) throw new Error('Sign in to search this project.');

      const searchResults = await searchProjectDocuments(
        projectId,
        trimmedQuery,
        session.access_token,
      );
      setResults(searchResults);
    } catch (searchError) {
      setError(searchError.message || 'Could not search this project.');
      setResults([]);
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
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Search documents</h1>
          <p className="mt-2 text-slate-600">
            Search only documents linked to this project.
          </p>
        </header>

        <form onSubmit={handleSearch} className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:flex sm:items-end sm:gap-3">
          <label htmlFor="project-search-query" className="block flex-1 text-sm font-medium">
            Search query
            <input
              id="project-search-query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              maxLength={4000}
              required
              placeholder="Ask about a topic in the project documents"
              className="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2.5 font-normal"
            />
          </label>
          <button type="submit" disabled={loading} className="mt-3 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 sm:mt-0">
            {loading ? 'Searching…' : 'Search'}
          </button>
        </form>

        {error && <p role="alert" className="mt-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p>}
        <section aria-live="polite" className="mt-6 space-y-4">
          {loading ? (
            <p role="status" className="rounded-xl bg-white p-5 text-sm text-slate-500">Searching project documents…</p>
          ) : searched && results.length === 0 && !error ? (
            <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">
              No relevant results found. Add documents to this project and try again.
            </p>
          ) : results.map((result, index) => (
            <article key={`${result.document_id}-${result.chunk_id}`} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold">{result.filename}</h2>
                <span className="text-xs text-slate-500">Result {index + 1}</span>
              </div>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{result.text}</p>
              <p className="mt-3 text-xs text-slate-500">Document ID: {result.document_id}</p>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
