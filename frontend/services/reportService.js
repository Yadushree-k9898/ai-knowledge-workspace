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

  if (response.status === 204) {
    return null;
  }

  let result;
  try {
    result = await response.json();
  } catch {
    throw new Error('The API returned an invalid response.');
  }

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

export async function getProjectReports(projectId, accessToken) {
  const reports = await request(
    `/projects/${encodeURIComponent(projectId)}/reports`,
    accessToken,
  );
  if (!Array.isArray(reports)) {
    throw new Error('The API returned an invalid report list.');
  }
  return reports;
}

export function createProjectReport(projectId, payload, accessToken) {
  return request(`/projects/${encodeURIComponent(projectId)}/reports`, accessToken, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getReport(reportId, accessToken) {
  return request(`/reports/${encodeURIComponent(reportId)}`, accessToken);
}

export function regenerateReport(reportId, accessToken) {
  return request(`/reports/${encodeURIComponent(reportId)}/regenerate`, accessToken, {
    method: 'POST',
  });
}

export function deleteReport(reportId, accessToken) {
  return request(`/reports/${encodeURIComponent(reportId)}`, accessToken, {
    method: 'DELETE',
  });
}