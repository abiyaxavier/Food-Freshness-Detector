import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';

import { routes } from './app.routes';

/**
 * app.config.ts
 *
 * Purpose:
 *   Root application configuration for a STANDALONE Angular app (no
 *   NgModules). This replaces the old app.module.ts. Every provider the
 *   whole app needs (routing, HTTP client, change detection settings)
 *   is registered here once.
 */
export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(), // Enables HttpClient injection in services (used by PredictionService)
  ],
};
