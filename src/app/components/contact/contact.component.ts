import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

/**
 * ContactComponent
 * Purpose: Static page listing team members, project guide, and the
 * GitHub repository link — customize the arrays below with your real details.
 */
@Component({
  selector: 'app-contact',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './contact.component.html',
  styleUrl: './contact.component.css',
})
export class ContactComponent {
  teamMembers = [
    { name: 'Abiya Xavier', role: 'AI & ML', initials: 'T1' },
    { name: 'Aswathy Suresh', role: 'Web Design', initials: 'T2' },
    { name: 'Sreelakshmi P', role: 'Research & Dataset', initials: 'T3' },
    { name: 'Nandhana P', role: 'Testing & Documentation', initials: 'T2' },
  ];

  projectGuide = { name: 'Dr. Guide Name', title: 'Assistant Professor, CSE Department' };

  githubUrl = 'https://github.com/your-username/FoodFreshnessDetector';
}
