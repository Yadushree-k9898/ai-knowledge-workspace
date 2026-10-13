const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

async function request(path, accessToken, method = 'GET') {
  let response;
  try {
    response = await fetch(`${API_URL}/api/v1/notifications${path}`, {
      method,
      cache: 'no-store',
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

export function getNotifications(accessToken) {
  return request('?limit=100', accessToken);
}

export function markNotificationRead(notificationId, accessToken) {
  return request(`/${encodeURIComponent(notificationId)}/read`, accessToken, 'PATCH');
}

export function markNotificationUnread(notificationId, accessToken) {
  return request(`/${encodeURIComponent(notificationId)}/unread`, accessToken, 'PATCH');
}