const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

async function request(path, accessToken) {
  let response;
  try {
    response = await fetch(`${API_URL}/api/v1${path}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
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

export async function getUserOrganizations(accessToken) {
  const organizations = await request('/organizations', accessToken);
  if (!Array.isArray(organizations)) {
    throw new Error('The API returned an invalid organization list.');
  }
  return organizations;
}

export function getOrganizationAnalytics(organizationId, dateFrom, dateTo, accessToken) {
  const query = new URLSearchParams({ date_from: dateFrom, date_to: dateTo });
  return request(
    `/organizations/${encodeURIComponent(organizationId)}/analytics?${query.toString()}`,
    accessToken,
  );
}
