const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

async function request(path, accessToken, options = {}) {
  let response;

  try {
    response = await fetch(`${API_URL}/api/v1${path}`, {
      ...options,
      headers: {
        Authorization: `Bearer ${accessToken}`,
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new Error('Could not connect to the API. Check that the backend is running and try again.');
  }

  let result;
  try {
    result = await response.json();
  } catch {
    throw new Error('The API returned an invalid response.');
  }

  if (!response.ok) {
    const detail = result?.detail;
    const message =
      result?.error?.message ||
      detail?.error?.message ||
      (typeof detail === 'string' ? detail : null) ||
      `The request failed with status ${response.status}.`;
    throw new Error(message);
  }

  return result;
}

async function requestData(path, accessToken, options) {
  const result = await request(path, accessToken, options);
  if (!result || !Object.hasOwn(result, 'data')) {
    throw new Error('The API returned an invalid response.');
  }
  return result.data;
}

async function requestList(path, accessToken) {
  const data = await requestData(path, accessToken);
  if (!Array.isArray(data)) {
    throw new Error('The API returned an invalid list response.');
  }
  return data;
}

export function getUserDocuments(accessToken) {
  return request('/documents/', accessToken).then((result) => {
    if (!Array.isArray(result)) {
      throw new Error('The API returned an invalid document list.');
    }
    return result;
  });
}

export function getProjectDocuments(projectId, accessToken) {
  return requestList(`/projects/${encodeURIComponent(projectId)}/documents`, accessToken);
}

export function addProjectDocument(projectId, documentId, accessToken) {
  return requestData(`/projects/${encodeURIComponent(projectId)}/documents`, accessToken, {
    method: 'POST',
    body: JSON.stringify({ document_id: documentId }),
  });
}

export function getProjectComparisons(projectId, accessToken) {
  return requestList(`/projects/${encodeURIComponent(projectId)}/comparisons`, accessToken);
}

export function createProjectComparison(projectId, payload, accessToken) {
  return requestData(`/projects/${encodeURIComponent(projectId)}/comparisons`, accessToken, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getProjectComparison(projectId, comparisonId, accessToken) {
  return requestData(
    `/projects/${encodeURIComponent(projectId)}/comparisons/${encodeURIComponent(comparisonId)}`,
    accessToken,
  );
}
