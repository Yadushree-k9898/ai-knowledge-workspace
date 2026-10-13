'use client';

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10 text-slate-900">
      <section className="w-full max-w-2xl rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm sm:p-12">
        <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">Research together</p>
        <h1 className="mt-4 text-4xl font-bold tracking-tight">AI Knowledge Workspace</h1>
        <p className="mx-auto mt-4 max-w-lg leading-7 text-slate-600">
          Securely organize your team’s documents, research, comparisons, and AI-assisted insights.
        </p>
        <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
          <a href="/signup" className="rounded-lg bg-indigo-600 px-5 py-3 text-sm font-semibold text-white hover:bg-indigo-700">
            Create an account
          </a>
          <a href="/login" className="rounded-lg border border-slate-300 px-5 py-3 text-sm font-semibold hover:bg-slate-50">
            Sign in
          </a>
        </div>
      </section>
    </main>
  );
}
