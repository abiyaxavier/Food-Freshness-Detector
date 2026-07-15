import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PredictionService } from '../../services/prediction.service';
import { PredictionHistoryItem, PredictionResponse } from '../../models/prediction.model';

/**
 * PredictComponent
 *
 * Purpose:
 *   The core feature page. Handles:
 *     1. File selection + live image preview
 *     2. Sending the file to the backend via PredictionService
 *     3. Showing a loading state while waiting for the API
 *     4. Displaying the result (Fresh/Rotten + confidence)
 *     5. Keeping a local (in-memory) history of past predictions this session
 */
@Component({
  selector: 'app-predict',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './predict.component.html',
  styleUrl: './predict.component.css',
})
export class PredictComponent {
  selectedFile: File | null = null;
  previewUrl: string | null = null;

  isLoading = false;
  errorMessage: string | null = null;
  result: PredictionResponse | null = null;

  history: PredictionHistoryItem[] = [];
  private historyCounter = 0;

  constructor(private predictionService: PredictionService) {}

  /** Triggered when the user picks a file via the input or drag-and-drop */
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    this.setFile(file);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    const file = event.dataTransfer?.files?.[0];
    if (file) this.setFile(file);
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault(); // required to allow onDrop to fire
  }

  private setFile(file: File): void {
    if (!file.type.startsWith('image/')) {
      this.errorMessage = 'Please choose an image file (JPG, PNG, or WEBP).';
      return;
    }
    this.errorMessage = null;
    this.result = null;
    this.selectedFile = file;
    this.previewUrl = URL.createObjectURL(file); // creates a temporary local URL to preview the image before upload
  }

  /** Sends the selected file to the backend and handles the response */
  predict(): void {
    if (!this.selectedFile) return;

    this.isLoading = true;
    this.errorMessage = null;
    this.result = null;

    this.predictionService.predictImage(this.selectedFile).subscribe({
      next: (response) => {
        this.result = response;
        this.isLoading = false;
        this.addToHistory(response);
      },
      error: (err) => {
        this.isLoading = false;
        // FastAPI returns { detail: "..." } on HTTPException; fall back to a generic message otherwise
        this.errorMessage =
          err?.error?.detail ||
          'Could not reach the prediction server. Make sure the FastAPI backend is running on http://localhost:8000.';
      },
    });
  }

  private addToHistory(response: PredictionResponse): void {
    if (!this.selectedFile || !this.previewUrl) return;
    this.history.unshift({
      id: this.historyCounter++,
      fileName: this.selectedFile.name,
      thumbnailUrl: this.previewUrl,
      prediction: response.prediction,
      confidence: response.confidence,
      timestamp: new Date(),
    });
    this.history = this.history.slice(0, 8); // keep only the most recent 8
  }

  reset(): void {
    this.selectedFile = null;
    this.previewUrl = null;
    this.result = null;
    this.errorMessage = null;
  }

  /** Parses "98.7%" into a number for the gauge's SVG arc calculation */
  get confidenceNumber(): number {
    if (!this.result) return 0;
    return parseFloat(this.result.confidence);
  }
}
