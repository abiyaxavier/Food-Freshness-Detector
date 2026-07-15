import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

/**
 * HomeComponent
 * Purpose: Landing page. Introduces the project, explains what it does,
 * and funnels visitors toward the Predict page (the core feature).
 */
@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css',
})
export class HomeComponent {
  steps = [
    { icon: 'bi-cloud-arrow-up', title: 'Upload a photo', text: 'Snap or upload a picture of any fruit or vegetable.' },
    { icon: 'bi-cpu', title: 'MobileNetV2 analyzes it', text: 'A transfer-learned CNN scans texture, color, and blemishes.' },
    { icon: 'bi-check2-circle', title: 'Get an instant verdict', text: 'Fresh or Rotten, with a confidence score, in under a second.' },
  ];

  features = [
    { icon: 'bi-lightning-charge', title: 'Instant results', text: 'No waiting — predictions return in real time as you upload.' },
    { icon: 'bi-graph-up', title: 'Confidence scoring', text: 'Every prediction comes with a percentage, not just a label.' },
    { icon: 'bi-basket', title: 'Multiple produce types', text: 'Trained across apples, bananas, tomatoes, potatoes, and more.' },
    { icon: 'bi-phone', title: 'Works on any device', text: 'Fully responsive — use it from your phone in the kitchen.' },
  ];
}
