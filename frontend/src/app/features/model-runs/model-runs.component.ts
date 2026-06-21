import { CommonModule, DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';

import { ApiService, ModelRun } from '../../core/api.service';

@Component({
  selector: 'mlm-model-runs',
  standalone: true,
  imports: [CommonModule, DatePipe],
  templateUrl: './model-runs.component.html',
})
export class ModelRunsComponent {
  private readonly api = inject(ApiService);

  modelRuns: ModelRun[] = [];
  loading = true;
  errorMessage = '';

  constructor() {
    this.loadRuns();
  }

  loadRuns(): void {
    this.loading = true;
    this.errorMessage = '';
    this.api.getModelRuns().subscribe({
      next: (runs) => {
        this.modelRuns = runs;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'Nao foi possivel carregar model runs.';
      },
    });
  }

  exportCsv(run: ModelRun): void {
    window.location.href = `/api/model-runs/${run.run_id}/export/csv`;
  }

  exportJson(run: ModelRun): void {
    window.location.href = `/api/model-runs/${run.run_id}/export/json`;
  }

  resultSummary(run: ModelRun): string {
    const keys = Object.keys(run.result).slice(0, 5);
    return keys.length ? keys.join(', ') : 'Sem campos de resultado.';
  }
}
