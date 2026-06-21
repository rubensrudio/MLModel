import { CommonModule, DecimalPipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService, Sample } from '../../core/api.service';

@Component({
  selector: 'mlm-samples',
  standalone: true,
  imports: [CommonModule, DecimalPipe, FormsModule],
  templateUrl: './samples.component.html',
})
export class SamplesComponent {
  private readonly api = inject(ApiService);

  samples: Sample[] = [];
  selectedWell = '';
  selectedRockType = '';
  loading = true;
  errorMessage = '';

  constructor() {
    this.loadSamples();
  }

  get wells(): string[] {
    return Array.from(new Set(this.samples.map((sample) => sample.well))).sort();
  }

  get rockTypes(): string[] {
    return Array.from(new Set(this.samples.map((sample) => sample.rock_type))).sort();
  }

  get visibleSamples(): Sample[] {
    return this.samples.filter((sample) => {
      const wellMatches = !this.selectedWell || sample.well === this.selectedWell;
      const rockMatches = !this.selectedRockType || sample.rock_type === this.selectedRockType;
      return wellMatches && rockMatches;
    });
  }

  loadSamples(): void {
    this.loading = true;
    this.errorMessage = '';
    this.api.getSamples().subscribe({
      next: (samples) => {
        this.samples = samples;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'Nao foi possivel carregar as amostras.';
      },
    });
  }

  resetFilters(): void {
    this.selectedWell = '';
    this.selectedRockType = '';
  }
}
