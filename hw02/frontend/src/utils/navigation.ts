/**
 * Helper to extract eventId from either /e/:id, /events/:id, or legacy ?eventId=:id
 */
export function getEventIdFromLocation(): string | null {
  const pathname = window.location.pathname;

  // Match /e/:id or /events/:id
  const match = pathname.match(/^\/(?:e|events)\/([^/?#]+)/i);
  if (match && match[1]) {
    return decodeURIComponent(match[1]);
  }

  // Fallback to query parameter ?eventId=...
  const params = new URLSearchParams(window.location.search);
  const queryId = params.get('eventId');
  if (queryId) {
    return queryId;
  }

  return null;
}

/**
 * Navigate to event with pretty path: /e/:eventId
 */
export function navigateToEvent(eventId: string): void {
  const targetPath = `/e/${encodeURIComponent(eventId)}`;
  if (window.location.pathname !== targetPath) {
    window.history.pushState({}, '', targetPath);
  }
}

/**
 * Navigate to home/onboarding: /
 */
export function navigateToHome(): void {
  if (window.location.pathname !== '/' || window.location.search) {
    window.history.pushState({}, '', '/');
  }
}
