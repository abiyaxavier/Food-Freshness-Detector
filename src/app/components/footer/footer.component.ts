import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

/**
 * FooterComponent
 * Purpose: Site-wide footer with quick links and project credit, shown on
 * every page beneath the router-outlet content.
 */
@Component({
  selector: 'app-footer',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './footer.component.html',
  styleUrl: './footer.component.css',
})
export class FooterComponent {
  year = new Date().getFullYear();
}
