import type { Environment } from './environment.model';

/**
 * Production build environment. The base URL stays publicly reachable so the
 * static bundle served by nginx can still talk to the API host (docker-compose
 * publishes the backend on http://localhost:8000).
 */
export const environment: Environment = {
  production: true,
  apiBaseUrl: 'http://localhost:8000',
};
