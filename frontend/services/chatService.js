const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

async function requestProjectChat(projectId, path, accessToken, options = {}) {
  let response;
  try {
    response = await fetch(
      `${API_URL}/api/v1/projects/${encodeURIComponent(projectId)}${path}`,
      {
        ...options,
        headers: {
          Authorization: `Bearer ${accessToken}`,
          ...(options.body ? { 'Content-Type': 'application/json' } : {}),
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
    throw new Error('The API returned an invalid project chat response.');
  }
  return result.data;
}

function isConversationDetail(value) {
  return (
    value?.conversation &&
    Array.isArray(value.messages) &&
    value.messages.every((message) => (
      typeof message.id === 'string' &&
      ['USER', 'ASSISTANT'].includes(message.role) &&
      typeof message.content === 'string' &&
      Array.isArray(message.sources)
    ))
  );
}

export async function askProjectQuestion(projectId, query, accessToken) {
  const data = await requestProjectChat(
    projectId,
    '/chat/ask',
    accessToken,
    { method: 'POST', body: JSON.stringify({ query }) },
  );
  if (typeof data?.answer !== 'string' || !Array.isArray(data.sources)) {
    throw new Error('The API returned an invalid project chat response.');
  }
  return data;
}

export async function listProjectConversations(projectId, accessToken) {
  const data = await requestProjectChat(
    projectId,
    '/conversations',
    accessToken,
  );
  if (!Array.isArray(data)) {
    throw new Error('The API returned an invalid conversation list.');
  }
  return data;
}

export async function getProjectConversation(projectId, conversationId, accessToken) {
  const data = await requestProjectChat(
    projectId,
    `/conversations/${encodeURIComponent(conversationId)}`,
    accessToken,
  );
  if (!isConversationDetail(data)) {
    throw new Error('The API returned an invalid conversation.');
  }
  return data;
}

export async function createProjectConversation(projectId, query, accessToken) {
  const data = await requestProjectChat(
    projectId,
    '/conversations',
    accessToken,
    { method: 'POST', body: JSON.stringify({ query }) },
  );
  if (!isConversationDetail(data)) {
    throw new Error('The API returned an invalid conversation.');
  }
  return data;
}

export async function sendProjectConversationMessage(
  projectId,
  conversationId,
  query,
  accessToken,
) {
  const data = await requestProjectChat(
    projectId,
    `/conversations/${encodeURIComponent(conversationId)}/messages`,
    accessToken,
    { method: 'POST', body: JSON.stringify({ query }) },
  );
  if (!isConversationDetail(data)) {
    throw new Error('The API returned an invalid conversation.');
  }
  return data;
}
