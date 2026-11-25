import type { Environment } from './environment.model';

/**
 * Development defaults. The API runs without a path prefix on port 8000.
 * The "production" build replaces this file with environment.production.ts
 * (see the fileReplacements section of angular.json).
 */
export const environment: Environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8000',
};
