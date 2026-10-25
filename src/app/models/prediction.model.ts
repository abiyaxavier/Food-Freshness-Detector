export interface StorageRecommendation {
  ideal_storage?: string;
  shelf_life_days?: string;
  room_temp_advice?: string;
  refrigerated_advice?: string;
  handling_tips?: string;
  safety_caution?: string;
  supported_fruits?: string[];
  is_supported?: boolean;
}

export interface PredictionResponse {
  fruit_name?: string;
  fruit_confidence?: string;
  freshness: string;
  freshness_confidence?: string;
  storage_recommendation?: StorageRecommendation;
  is_supported?: boolean;

  // Backward compatibility fields
  prediction: string;
  confidence: string;
}

export interface PredictionHistoryItem {
  id: number;
  fileName: string;
  thumbnailUrl: string;
  fruitName?: string;
  fruitConfidence?: string;
  prediction: string;
  confidence: string;
  timestamp: Date;
}
