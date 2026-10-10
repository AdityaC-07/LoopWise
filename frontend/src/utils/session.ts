import { v4 as uuidv4 } from 'uuid';

const SESSION_KEY = 'loopwise_session_id';

export function getSessionId(): string {
  let id = sessionStorage.getItem(SESSION_KEY);
  if (!id) {
    id = uuidv4();
    sessionStorage.setItem(SESSION_KEY, id);
  }
  return id;
}
