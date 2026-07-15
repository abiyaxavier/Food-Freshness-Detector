import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PredictionResponse } from '../models/prediction.model';

/**
 * prediction.service.ts
 *
 * Purpose:
 *   Centralizes ALL communication with the FastAPI backend in one place.
 *   Components never call HttpClient directly — they call this service.
 *   This means if the API URL or request format ever changes, we only
 *   update it here, not in every component that needs predictions.
 *
 * @Injectable({ providedIn: 'root' })
 *   Registers this service as a single shared instance (singleton) for the
 *   whole app, without needing to list it in a module's `providers` array.
 */
@Injectable({ providedIn: 'root' })
export class PredictionService {
  // In production, move this to an environment file (environment.ts /
  // environment.prod.ts) so dev vs prod API URLs can differ.
  private readonly apiUrl = 'http://localhost:8000/predict';

  constructor(private http: HttpClient) {}

  /**
   * Sends the selected image file to the backend as multipart/form-data
   * (required because FastAPI's `UploadFile` expects a file upload, not JSON)
   * and returns an Observable of the typed prediction response.
   */
  predictImage(file: File): Observable<PredictionResponse> {
    const formData = new FormData();
    formData.append('file', file); // key "file" MUST match FastAPI's `file: UploadFile` param name

    return this.http.post<PredictionResponse>(this.apiUrl, formData);
  }
}
