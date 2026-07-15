/**
 * prediction.model.ts
 *
 * Purpose:
 *   TypeScript interfaces describing the shape of data flowing between the
 *   Angular frontend and the FastAPI backend. Using typed interfaces (instead
 *   of `any`) catches typos and mismatches at compile time, e.g. if the
 *   backend field were ever renamed from `prediction` to `label`.
 */

/** Exact JSON shape returned by POST /predict */
export interface PredictionResponse {
  prediction: 'Fresh' | 'Rotten';
  confidence: string; // e.g. "98.7%"
}

/** One entry in the local prediction history log shown on the Predict page */
export interface PredictionHistoryItem {
  id: number;
  fileName: string;
  thumbnailUrl: string;
  prediction: 'Fresh' | 'Rotten';
  confidence: string;
  timestamp: Date;
}
