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
    { name: 'Your Name', role: 'Team Lead / ML Engineer', initials: 'YN' },
    { name: 'Teammate Two', role: 'Backend Developer', initials: 'T2' },
    { name: 'Teammate Three', role: 'Frontend Developer', initials: 'T3' },
  ];

  projectGuide = { name: 'Dr. Guide Name', title: 'Assistant Professor, CSE Department' };

  githubUrl = 'https://github.com/your-username/FoodFreshnessDetector';
}
