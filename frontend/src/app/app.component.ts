import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { ApiService, HealthResponse } from './core/api.service';

@Component({
  selector: 'mlm-root',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  private readonly api = inject(ApiService);

  health: HealthResponse | null = null;

  constructor() {
    this.api.getHealth().subscribe({
      next: (health) => {
        this.health = health;
      },
      error: () => {
        this.health = null;
      },
    });
  }
}
