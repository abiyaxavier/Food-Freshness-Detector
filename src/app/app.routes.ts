import { Routes } from '@angular/router';

/**
 * app.routes.ts
 *
 * Purpose:
 *   Defines every URL path in the app and which standalone component
 *   renders for it. Angular's router reads this array and swaps the
 *   <router-outlet> content in app.component.html accordingly.
 */
export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./components/home/home.component').then((m) => m.HomeComponent),
    title: 'FreshEye — AI Food Freshness Detection',
  },
  {
    path: 'about',
    loadComponent: () =>
      import('./components/about/about.component').then((m) => m.AboutComponent),
    title: 'About — FreshEye',
  },
  {
    path: 'predict',
    loadComponent: () =>
      import('./components/predict/predict.component').then((m) => m.PredictComponent),
    title: 'Predict — FreshEye',
  },
  {
    path: 'contact',
    loadComponent: () =>
      import('./components/contact/contact.component').then((m) => m.ContactComponent),
    title: 'Contact — FreshEye',
  },
  { path: '**', redirectTo: '' }, // unknown routes fall back to Home
];
