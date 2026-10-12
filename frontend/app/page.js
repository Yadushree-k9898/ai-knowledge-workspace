'use client';

import { useEffect, useState } from 'react';

export default function Home() {
  const [backendStatus, setBackendStatus] = useState('Checking...');

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/health')
      .then((res) => res.json())
      .then((data) => setBackendStatus(data.status === 'ok' ? 'Online 🚀' : 'Error'))
      .catch((err) => setBackendStatus('Offline ❌'));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-8">AI Knowledge Workspace</h1>
      
      <div className="p-6 bg-white rounded-xl shadow-md flex items-center space-x-4">
        <div>
          <div className="text-xl font-medium text-black">FastAPI Backend Status</div>
          <p className="text-gray-500">{backendStatus}</p>
        </div>
      </div>
    </main>
  );
}
