import { Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';

import { PredictionService } from '../../services/prediction.service';

import {
  PredictionHistoryItem,
  PredictionResponse
} from '../../models/prediction.model';

type FruitType = 'apple' | 'banana' | 'orange';
type StorageCondition = 'room' | 'fridge';

interface ShelfLifeInfo {
  days: string;
  advice: string;
}

@Component({
  selector: 'app-predict',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './predict.component.html',
  styleUrl: './predict.component.css',
})
export class PredictComponent implements OnDestroy {

  // ===================================
  // VARIABLES
  // ===================================

  selectedFile: File | null = null;
  previewUrl: string | null = null;

  isLoading = false;
  errorMessage: string | null = null;

  result: PredictionResponse | null = null;

  history: PredictionHistoryItem[] = [];

  private historyCounter = 0;
  private createdUrls = new Set<string>();

  // ===================================
  // FRUIT AND STORAGE SELECTION
  // ===================================

  selectedFruit: FruitType | null = null;

  storageCondition: StorageCondition = 'room';

  // ===================================
  // CONSTRUCTOR
  // ===================================

  constructor(
    private predictionService: PredictionService
  ) {}

  // ===================================
  // SELECT FRUIT
  // ===================================

  selectFruit(fruit: FruitType): void {

    if (this.isLoading) return;

    if (this.selectedFruit !== fruit) {
      this.selectedFruit = fruit;

      // Previous prediction no longer applies
      // to the newly selected fruit.
      this.result = null;
      this.errorMessage = null;
    }
  }

  // ===================================
  // SELECT STORAGE
  // ===================================

  selectStorage(condition: StorageCondition): void {
    this.storageCondition = condition;
  }

  // ===================================
  // GET FRUIT NAME
  // ===================================

  get fruitName(): string {

    if (!this.selectedFruit) {
      return 'Not selected';
    }

    return (
      this.selectedFruit.charAt(0).toUpperCase() +
      this.selectedFruit.slice(1)
    );
  }

  // ===================================
  // SHELF LIFE GUIDANCE
  // ===================================

  get shelfLifeInfo(): ShelfLifeInfo {

    if (!this.result || !this.selectedFruit) {
      return {
        days: 'Not available',
        advice: ''
      };
    }

    const prediction = this.result.prediction.toLowerCase();

    if (prediction === 'rotten') {
      return {
        days: 'Not applicable',
        advice:
          'Possible spoilage detected. Do not eat fruit showing mold, decay, or other clear signs of spoilage.'
      };
    }

    if (prediction !== 'fresh') {
      return {
        days: 'Not available',
        advice: 'Unable to interpret the freshness prediction.'
      };
    }

    const shelfLife: Record<
      FruitType,
      {
        room: string;
        fridge: string;
        advice: string;
      }
    > = {

      apple: {
        room: 'About 5–7 days',
        fridge: 'About 4–6 weeks',
        advice:
          'Store apples in a cool place. Refrigeration generally helps preserve freshness longer.'
      },

      banana: {
        room: 'About 2–7 days',
        fridge: 'Depends on ripeness',
        advice:
          'Keep unripe bananas at room temperature. Refrigerate ripe bananas to slow further ripening.'
      },

      orange: {
        room: 'About 5–7 days',
        fridge: 'About 2–3 weeks',
        advice:
          'Store oranges in a cool, dry place or refrigerate for longer storage.'
      }

    };

    const fruit = shelfLife[this.selectedFruit];

    return {
      days: fruit[this.storageCondition],
      advice: fruit.advice
    };
  }

  // ===================================
  // CAMERA AND GALLERY
  // ===================================

  onFileSelected(event: Event): void {

    const input = event.target as HTMLInputElement;

    const file = input.files?.[0];

    if (!file) return;

    this.setFile(file);

    // Allow selecting the same file again.
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
  // IMAGE VALIDATION
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

    // Release previous preview if it is
    // not being used in prediction history.

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

    if (
      !this.selectedFile ||
      !this.selectedFruit ||
      this.isLoading
    ) {
      return;
    }

    this.isLoading = true;

    this.errorMessage = null;

    this.result = null;

    const file = this.selectedFile;

    const thumbnailUrl = this.previewUrl;

    this.predictionService.predictImage(file).subscribe({

      next: (response: PredictionResponse) => {

        this.result = response;

        this.isLoading = false;

        this.addToHistory(
          response,
          file,
          thumbnailUrl
        );
      },

      error: (err: HttpErrorResponse) => {

        this.isLoading = false;

        const detail = err.error?.detail;

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

    // Keep only the latest 8 predictions.

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

    this.selectedFruit = null;

    this.storageCondition = 'room';
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

  // ===================================
  // COMPONENT CLEANUP
  // ===================================

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

    if (!Number.isFinite(value)) {
      return 0;
    }

    return Math.max(
      0,
      Math.min(100, value)
    );
  }

}