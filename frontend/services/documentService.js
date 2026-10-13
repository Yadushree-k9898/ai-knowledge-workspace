const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

async function projectDocumentRequest(projectId, accessToken, suffix = '', options = {}) {
  let response;

  try {
    response = await fetch(
      `${API_URL}/api/v1/projects/${encodeURIComponent(projectId)}/documents${suffix}`,
      {
        ...options,
        headers: {
          Authorization: `Bearer ${accessToken}`,
          ...options.headers,
        },
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
  if (!result || !Object.hasOwn(result, 'data')) {
    throw new Error('The API returned an invalid response.');
  }
  return result.data;
}

export async function listProjectDocuments(projectId, accessToken) {
  const documents = await projectDocumentRequest(projectId, accessToken);
  if (!Array.isArray(documents)) {
    throw new Error('The API returned an invalid project document list.');
  }
  return documents;
}

export function uploadProjectDocument(projectId, file, accessToken) {
  const formData = new FormData();
  formData.append('file', file);
  return projectDocumentRequest(projectId, accessToken, '', {
    method: 'POST',
    body: formData,
  });
}

export function removeProjectDocument(projectId, documentId, accessToken) {
  return projectDocumentRequest(
    projectId,
    accessToken,
    `/${encodeURIComponent(documentId)}`,
    { method: 'DELETE' },
  );
}