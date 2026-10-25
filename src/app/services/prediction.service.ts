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
 */
@Injectable({ providedIn: 'root' })
export class PredictionService {
  private apiUrl = `http://${window.location.hostname}:8000/predict`;
  constructor(private http: HttpClient) {}

  /**
   * Sends the selected image file to the backend as multipart/form-data.
   * Optionally sends user-selected fruit ('auto', 'apple', 'banana', 'orange', 'other').
   */
  predictImage(file: File, fruit?: string): Observable<PredictionResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (fruit && fruit !== 'auto') {
      formData.append('fruit', fruit);
    }

    return this.http.post<PredictionResponse>(this.apiUrl, formData);
  }
}
