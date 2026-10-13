const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export async function searchProjectDocuments(projectId, query, accessToken) {
  let response;
  try {
    response = await fetch(
      `${API_URL}/api/v1/projects/${encodeURIComponent(projectId)}/search`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, limit: 10 }),
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
  if (!Array.isArray(result?.data)) {
    throw new Error('The API returned an invalid search response.');
  }
  return result.data;
}