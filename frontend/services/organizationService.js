const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

async function request(path, accessToken, options = {}, includeEnvelope = false) {
  let response;

  try {
    response = await fetch(`${API_URL}/api/v1${path}`, {
      ...options,
      headers: {
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
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

  if (!result || !Object.prototype.hasOwnProperty.call(result, 'data')) {
    throw new Error('The API returned an invalid response.');
  }

  return includeEnvelope ? result : result.data;
}

export function getInvitation(token) {
  return request(`/invitations/${encodeURIComponent(token)}`);
}

export function listOrganizations(accessToken) {
  return request('/organizations', accessToken);
}

export function createOrganization(name, accessToken) {
  return request('/organizations', accessToken, {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

export function acceptInvitation(token, accessToken) {
  return request(`/invitations/${encodeURIComponent(token)}/accept`, accessToken, {
    method: 'POST',
  });
}

export async function getOrganizationSettings(organizationId, accessToken) {
  const [organization, organizations] = await Promise.all([
    request(`/organizations/${encodeURIComponent(organizationId)}`, accessToken),
    request('/organizations', accessToken),
  ]);
  const membership = organizations.find((item) => item.id === organizationId);

  if (!membership) {
    throw new Error('You do not have access to this organization.');
  }

  return { ...organization, role: membership.role };
}

export function updateOrganizationName(organizationId, name, accessToken) {
  return request(`/organizations/${encodeURIComponent(organizationId)}`, accessToken, {
    method: 'PATCH',
    body: JSON.stringify({ name }),
  });
}

export async function getOrganizationAuditLogs(
  organizationId,
  accessToken,
  { limit = 50, offset = 0, action = '', resourceType = '' } = {},
) {
  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (action) query.set('action', action);
  if (resourceType) query.set('resource_type', resourceType);

  const result = await request(
    `/organizations/${encodeURIComponent(organizationId)}/audit-logs?${query}`,
    accessToken,
    {},
    true,
  );
  if (!Array.isArray(result.data) || !result.pagination) {
    throw new Error('The API returned an invalid audit log response.');
  }
  return { events: result.data, pagination: result.pagination };
}