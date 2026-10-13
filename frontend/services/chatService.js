const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export async function askProjectQuestion(projectId, query, accessToken) {
  let response;
  try {
    response = await fetch(
      `${API_URL}/api/v1/projects/${encodeURIComponent(projectId)}/chat/ask`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      },
    );
  } catch {
    throw new Error('Could not connect to the API. Check that the backend is running and try again.');
  }

  const result = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = result?.detail;
    throw new Error(
      result?.error?.message ||
        detail?.error?.message ||
        (typeof detail === 'string' ? detail : null) ||
        `The request failed with status ${response.status}.`,
    );
  }
  if (typeof result?.data?.answer !== 'string' || !Array.isArray(result.data.sources)) {
    throw new Error('The API returned an invalid project chat response.');
  }
  return result.data;
}