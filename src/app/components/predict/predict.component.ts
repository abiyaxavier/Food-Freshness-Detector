import { Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';

import { PredictionService } from '../../services/prediction.service';

import {
  PredictionHistoryItem,
  PredictionResponse
} from '../../models/prediction.model';

@Component({
  selector: 'app-predict',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './predict.component.html',
  styleUrl: './predict.component.css',
})
export class PredictComponent implements OnDestroy {

  selectedFile: File | null = null;
  previewUrl: string | null = null;

  isLoading = false;
  errorMessage: string | null = null;

  result: PredictionResponse | null = null;

  history: PredictionHistoryItem[] = [];

  private historyCounter = 0;

  // Keep track of object URLs so they can be released.
  private createdUrls = new Set<string>();

  constructor(
    private predictionService: PredictionService
  ) {}

  // ===================================
  // CAMERA AND GALLERY IMAGE SELECTION
  // ===================================

  onFileSelected(event: Event): void {

    const input = event.target as HTMLInputElement;

    const file = input.files?.[0];

    if (!file) return;

    this.setFile(file);

    // Allow selecting the same image again.
    input.value = '';
  }

  // ===================================
  // DRAG AND DROP
  // ===================================

  onDrop(event: DragEvent): void {

    event.preventDefault();

    if (this.isLoading) return;

    const file = event.dataTransfer?.files?.[0];

    if (file) {
      this.setFile(file);
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
  }

  // ===================================
  // IMAGE VALIDATION AND PREVIEW
  // ===================================

  private setFile(file: File): void {

    if (this.isLoading) return;

    const allowedTypes = [
      'image/jpeg',
      'image/png',
      'image/webp'
    ];

    if (!allowedTypes.includes(file.type)) {

      this.errorMessage =
        'Please select a JPG, PNG, or WEBP image.';

      return;
    }

    const maxSize = 10 * 1024 * 1024;

    if (file.size > maxSize) {

      this.errorMessage =
        'Image is too large. Maximum size is 10 MB.';

      return;
    }

    // Release old preview if it is not used by history.
    if (
      this.previewUrl &&
      !this.history.some(
        item => item.thumbnailUrl === this.previewUrl
      )
    ) {
      this.releaseUrl(this.previewUrl);
    }

    this.selectedFile = file;

    this.result = null;

    this.errorMessage = null;

    this.previewUrl = URL.createObjectURL(file);

    this.createdUrls.add(this.previewUrl);
  }

  // ===================================
  // AI PREDICTION
  // ===================================

  predict(): void {

    if (!this.selectedFile || this.isLoading) return;

    this.isLoading = true;

    this.errorMessage = null;

    this.result = null;

    const file = this.selectedFile;
    const thumbnailUrl = this.previewUrl;

    this.predictionService.predictImage(file).subscribe({

      next: (response) => {

        this.result = response;

        this.isLoading = false;

        this.addToHistory(
          response,
          file,
          thumbnailUrl
        );
      },

      error: (err) => {

        this.isLoading = false;

        const detail = err?.error?.detail;

        this.errorMessage =
          typeof detail === 'string'
            ? detail
            : 'Prediction failed. Please check the backend connection.';
      }

    });
  }

  // ===================================
  // PREDICTION HISTORY
  // ===================================

  private addToHistory(
    response: PredictionResponse,
    file: File,
    thumbnailUrl: string | null
  ): void {

    if (!thumbnailUrl) return;

    this.history.unshift({

      id: this.historyCounter++,

      fileName: file.name,

      thumbnailUrl: thumbnailUrl,

      prediction: response.prediction,

      confidence: response.confidence,

      timestamp: new Date(),

    });

    // Keep only 8 predictions.
    const removedItems = this.history.splice(8);

    for (const item of removedItems) {
      if (item.thumbnailUrl !== this.previewUrl) {
        this.releaseUrl(item.thumbnailUrl);
      }
    }
  }

  // ===================================
  // CLEAR SELECTED IMAGE
  // ===================================

  reset(): void {

    if (
      this.previewUrl &&
      !this.history.some(
        item => item.thumbnailUrl === this.previewUrl
      )
    ) {
      this.releaseUrl(this.previewUrl);
    }

    this.selectedFile = null;

    this.previewUrl = null;

    this.result = null;

    this.errorMessage = null;
  }

  // ===================================
  // RELEASE TEMPORARY IMAGE URL
  // ===================================

  private releaseUrl(url: string): void {

    if (this.createdUrls.has(url)) {

      URL.revokeObjectURL(url);

      this.createdUrls.delete(url);
    }
  }

  ngOnDestroy(): void {

    for (const url of this.createdUrls) {
      URL.revokeObjectURL(url);
    }

    this.createdUrls.clear();
  }

  // ===================================
  // CONFIDENCE GAUGE
  // ===================================

  get confidenceNumber(): number {

    if (!this.result) return 0;

    const value = parseFloat(
      String(this.result.confidence)
    );

    if (!Number.isFinite(value)) return 0;

    return Math.max(0, Math.min(100, value));
  }

}