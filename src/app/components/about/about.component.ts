import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

/**
 * AboutComponent
 * Purpose: Explains the problem (food freshness/waste), why AI helps,
 * the tech stack, dataset, and project objectives — static content page.
 */
@Component({
  selector: 'app-about',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './about.component.html',
  styleUrl: './about.component.css',
})
export class AboutComponent {
  techStack = [
    { category: 'Frontend', items: ['Angular 18 (standalone)', 'Bootstrap 5', 'TypeScript'] },
    { category: 'Backend', items: ['Python', 'FastAPI', 'Uvicorn'] },
    { category: 'AI / ML', items: ['TensorFlow', 'Keras', 'MobileNetV2 (Transfer Learning)'] },
    { category: 'Image Processing', items: ['OpenCV', 'Pillow', 'NumPy'] },
  ];
}
