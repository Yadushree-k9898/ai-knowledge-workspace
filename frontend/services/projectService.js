const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

async function request(path, accessToken, options = {}, includeEnvelope = false) {
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
  return includeEnvelope ? result : result.data;
}

export async function listOrganizationProjects(organizationId, accessToken) {
  const result = await request(
    `/organizations/${encodeURIComponent(organizationId)}/projects?page=1&page_size=100`,
    accessToken,
    {},
    true,
  );
  if (!Array.isArray(result.data) || !result.pagination) {
    throw new Error('The API returned an invalid project list.');
  }
  return result.data;
}

export function createOrganizationProject(organizationId, payload, accessToken) {
  return request(
    `/organizations/${encodeURIComponent(organizationId)}/projects`,
    accessToken,
    { method: 'POST', body: JSON.stringify(payload) },
  );
}

export function getProject(projectId, accessToken) {
  return request(`/projects/${encodeURIComponent(projectId)}`, accessToken);
}

export function getProjectSummary(projectId, accessToken) {
  return request(`/projects/${encodeURIComponent(projectId)}/summary`, accessToken);
}

export function updateProject(projectId, payload, accessToken) {
  return request(
    `/projects/${encodeURIComponent(projectId)}`,
    accessToken,
    { method: 'PATCH', body: JSON.stringify(payload) },
  );
}

export function deleteProject(projectId, accessToken) {
  return request(`/projects/${encodeURIComponent(projectId)}`, accessToken, {
    method: 'DELETE',
  });
}