const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

async function request(path, accessToken, options = {}) {
  let response;
  try {
    response = await fetch(`${API_URL}/api/v1/auth${path}`, {
      ...options,
      headers: {
        Authorization: `Bearer ${accessToken}`,
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
      cache: 'no-store',
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

function displayNameFor(user) {
  const providedName = user.user_metadata?.display_name
    || user.user_metadata?.full_name
    || user.user_metadata?.name;
  const name = typeof providedName === 'string' ? providedName.trim() : '';
  if (name.length >= 2) {
    return name.slice(0, 100);
  }
  const emailName = user.email?.split('@')[0]?.trim() || '';
  return emailName.length >= 2 ? emailName.slice(0, 100) : 'User';
}

export function bootstrapProfile(session) {
  return request('/bootstrap', session.access_token, {
    method: 'POST',
    body: JSON.stringify({ display_name: displayNameFor(session.user) }),
  });
}

export function getMyProfile(accessToken) {
  return request('/me', accessToken);
}

export function updateMyProfile(accessToken, updates) {
  return request('/me', accessToken, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });
}

export function deleteMyAccount(accessToken) {
  return request('/me', accessToken, { method: 'DELETE' });
}

export function safeReturnPath(value, fallback = '/dashboard') {
  if (
    typeof value !== 'string'
    || !value.startsWith('/')
    || value.startsWith('//')
    || value.startsWith('/\\')
  ) {
    return fallback;
  }
  const parsed = new URL(value, 'https://workspace.invalid');
  if (parsed.origin !== 'https://workspace.invalid') {
    return fallback;
  }
  return value;
}