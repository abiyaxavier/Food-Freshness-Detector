import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { PredictionService } from '../../services/prediction.service';
import { PredictionResponse, PredictionHistoryItem } from '../../models/prediction.model';

@Component({
  selector: 'app-predict',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './predict.component.html',
  styleUrls: ['./predict.component.css']
})
export class PredictComponent {
  selectedFile: File | null = null;
  previewUrl: string | null = null;

  result: PredictionResponse | null = null;
  isLoading = false;
  errorMessage = '';

  storageCondition: 'room' | 'fridge' = 'room';
  history: PredictionHistoryItem[] = [];

  constructor(private predictionService: PredictionService) {}

  get fruitName(): string {
    if (this.result?.fruit_name) {
      return this.result.fruit_name;
    }
    return '';
  }

  get isFruitSupported(): boolean {
    if (!this.result) {
      return true;
    }
    if (this.result.is_supported === false) {
      return false;
    }
    const nameLower = (this.result.fruit_name || '').toLowerCase();
    return !nameLower.includes('unrecognized') && !nameLower.includes('unsupported') && !nameLower.includes('unidentified');
  }

  get fruitConfidenceNumber(): number {
    if (!this.result?.fruit_confidence) {
      return 0;
    }
    const parsed = parseFloat(this.result.fruit_confidence);
    return isNaN(parsed) ? 0 : Math.round(parsed);
  }

  get confidenceNumber(): number {
    const raw = this.result?.freshness_confidence || this.result?.confidence;
    if (!raw) {
      return 0;
    }
    const parsed = parseFloat(raw);
    return isNaN(parsed) ? 0 : Math.round(parsed);
  }

  get fruitEmoji(): string {
    const name = (this.result?.fruit_name || '').toLowerCase();
    if (name.includes('apple')) return '🍎';
    if (name.includes('banana')) return '🍌';
    if (name.includes('orange')) return '🍊';
    return '🌿';
  }

  get shelfLifeInfo(): { days: string; advice: string } {
    if (!this.result) {
      return { days: '', advice: '' };
    }

    const isRotten =
      this.result.freshness?.toLowerCase() === 'rotten' ||
      this.result.prediction?.toLowerCase() === 'rotten';

    if (isRotten) {
      return {
        days: '0 Days',
        advice:
          this.result.storage_recommendation?.safety_caution ||
          'This fruit shows signs of spoilage and is not safe to consume. Discard to prevent spreading mold.'
      };
    }

    const rec = this.result.storage_recommendation;
    const isFridge = this.storageCondition === 'fridge';

    if (rec) {
      if (isFridge) {
        return {
          days: rec.shelf_life_days || '2 - 3 Weeks',
          advice:
            rec.refrigerated_advice ||
            'Store in the crisper drawer to maintain firmness and moisture balance.'
        };
      } else {
        return {
          days: rec.shelf_life_days || '5 - 7 Days',
          advice:
            rec.room_temp_advice ||
            'Store at room temperature out of direct sunlight in a cool, dry, well-ventilated spot.'
        };
      }
    }

    return isFridge
      ? {
          days: '1 - 2 Weeks',
          advice: 'Store in the refrigerator crisper drawer to maximize shelf life.'
        }
      : {
          days: '3 - 5 Days',
          advice: 'Store at room temperature in a cool, dry area away from direct sunlight.'
        };
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) {
      return;
    }

    this.handleFile(file);
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();

    const file = event.dataTransfer?.files?.[0];
    if (file) {
      this.handleFile(file);
    }
  }

  private handleFile(file: File): void {
    if (!file.type.startsWith('image/')) {
      this.errorMessage = 'Please select a valid image file (JPG, PNG, or WEBP).';
      this.selectedFile = null;
      this.previewUrl = null;
      return;
    }

    this.selectedFile = file;
    this.previewUrl = URL.createObjectURL(file);
    this.result = null;
    this.errorMessage = '';
  }

  selectStorage(condition: 'room' | 'fridge'): void {
    this.storageCondition = condition;
  }

  reset(): void {
    this.selectedFile = null;
    this.previewUrl = null;
    this.result = null;
    this.errorMessage = '';
  }

  predict(): void {
    if (!this.selectedFile) {
      this.errorMessage = 'Please select or upload a fruit image first.';
      return;
    }

    if (this.isLoading) {
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.result = null;

    const currentFile = this.selectedFile;
    const currentPreviewUrl = this.previewUrl;

    this.predictionService.predictImage(currentFile).subscribe({
      next: (response: PredictionResponse) => {
        console.log('Prediction response received:', response);

        const freshnessLabel =
          (response.freshness || response.prediction || '').toLowerCase() === 'rotten'
            ? 'Rotten'
            : 'Fresh';

        this.result = {
          ...response,
          prediction: freshnessLabel,
          freshness: freshnessLabel
        };

        this.history.unshift({
          id: Date.now(),
          fileName: currentFile.name,
          thumbnailUrl: currentPreviewUrl ?? '',
          fruitName: response.fruit_name || 'Detected Fruit',
          fruitConfidence: response.fruit_confidence,
          prediction: freshnessLabel,
          confidence: response.freshness_confidence || response.confidence,
          timestamp: new Date()
        });

        this.isLoading = false;
      },

      error: (err: HttpErrorResponse) => {
        console.error('Prediction error:', err);
        this.isLoading = false;

        const detail = err.error?.detail;

        if (typeof detail === 'string') {
          this.errorMessage = detail;
        } else if (typeof err.error === 'string') {
          this.errorMessage = err.error;
        } else {
          this.errorMessage =
            `Prediction request failed (HTTP ${err.status || 'Connection Error'}). ` +
            'Please verify that the FastAPI backend server is running.';
        }
      }
    });
  }
}
