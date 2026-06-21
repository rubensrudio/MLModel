import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import {
  ApiService,
  BatchInputMode,
  MODEL_OPTIONS,
  ModelKey,
  ModelOption,
  ModelRun,
} from '../../core/api.service';

@Component({
  selector: 'mlm-rock-physics',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './rock-physics.component.html',
})
export class RockPhysicsComponent {
  private readonly api = inject(ApiService);

  modelRuns: ModelRun[] = [];
  modelRunning = false;
  batchRunning = false;
  modelMessage = '';
  selectedModel: ModelKey = 'gassmann';
  batchInputMode: BatchInputMode = 'json';
  readonly modelOptions = MODEL_OPTIONS;
  gassmannForm = {
    mineral_bulk_modulus_gpa: 37,
    mineral_shear_modulus_gpa: 44,
    mineral_density_g_cm3: 2.65,
    fluid_bulk_modulus_gpa: 2.2,
    fluid_density_g_cm3: 1,
    porosity_fraction: 0.2,
    critical_porosity_fraction: 0.4,
  };
  granularForm = {
    mineral_bulk_modulus_gpa: 37,
    mineral_shear_modulus_gpa: 44,
    porosity_fraction: 0.25,
    critical_porosity_fraction: 0.4,
    coordination_number: 8.6,
    effective_stress_mpa: 20,
    reduced_shear_factor: 0.5,
  };
  avoForm = {
    incident_angles_degrees: '0,10,20,30',
    vp_upper_m_s: 3000,
    vp_lower_m_s: 3300,
    vs_upper_m_s: 1500,
    vs_lower_m_s: 1650,
    density_upper_kg_m3: 2300,
    density_lower_kg_m3: 2400,
  };
  batchRowsText = JSON.stringify(
    [
      {
        mineral_bulk_modulus_gpa: 37,
        mineral_shear_modulus_gpa: 44,
        porosity_fraction: 0.25,
        critical_porosity_fraction: 0.4,
        coordination_number: 8.6,
        effective_stress_mpa: 20,
        reduced_shear_factor: 0.5,
      },
    ],
    null,
    2,
  );
  batchCsvText = [
    'mineral_bulk_modulus_gpa,mineral_shear_modulus_gpa,porosity_fraction,critical_porosity_fraction,coordination_number,effective_stress_mpa,reduced_shear_factor',
    '37,44,0.25,0.4,8.6,20,0.5',
  ].join('\n');

  constructor() {
    this.reloadRuns();
  }

  get latestRun(): ModelRun | null {
    return this.modelRuns[0] ?? null;
  }

  get selectedModelOption(): ModelOption {
    return MODEL_OPTIONS.find((option) => option.key === this.selectedModel) ?? MODEL_OPTIONS[0];
  }

  get latestRunSummary(): string {
    if (!this.latestRun) {
      return 'Nenhuma run persistida.';
    }
    const resultKeys = Object.keys(this.latestRun.result).slice(0, 4);
    return resultKeys.length ? resultKeys.join(', ') : 'Resultado sem campos numericos.';
  }

  reloadRuns(): void {
    this.api.getModelRuns().subscribe({
      next: (runs) => {
        this.modelRuns = runs;
      },
      error: () => {
        this.modelRuns = [];
      },
    });
  }

  exportLatestRunCsv(): void {
    if (!this.latestRun) {
      return;
    }
    window.location.href = `/api/model-runs/${this.latestRun.run_id}/export/csv`;
  }

  executeSelectedModel(): void {
    this.modelRunning = true;
    this.modelMessage = '';

    this.api
      .executeModel(this.selectedModelOption.endpoint, this.selectedModelParameters())
      .subscribe({
        next: (run) => {
          this.modelRuns = [run, ...this.modelRuns.filter((item) => item.run_id !== run.run_id)];
          this.modelRunning = false;
          this.modelMessage = `Run criada: ${run.model_name}`;
        },
        error: () => {
          this.modelRunning = false;
          this.modelMessage = 'Falha ao executar o modelo selecionado.';
        },
      });
  }

  executeBatch(): void {
    this.batchRunning = true;
    this.modelMessage = '';

    const payload: Record<string, unknown> = {
      model: this.selectedModelOption.batchModel,
      saved_analysis_id: null,
    };

    if (this.batchInputMode === 'json') {
      try {
        payload['rows'] = JSON.parse(this.batchRowsText) as unknown;
      } catch {
        this.batchRunning = false;
        this.modelMessage = 'JSON do batch invalido.';
        return;
      }
    } else {
      payload['csv_text'] = this.batchCsvText;
    }

    this.api.executeBatch(payload).subscribe({
      next: (run) => {
        this.modelRuns = [run, ...this.modelRuns.filter((item) => item.run_id !== run.run_id)];
        this.batchRunning = false;
        this.modelMessage = `Batch persistido: ${this.batchStatus(run)}`;
      },
      error: () => {
        this.batchRunning = false;
        this.modelMessage = 'Falha ao executar o batch.';
      },
    });
  }

  batchStatus(run: ModelRun): string {
    const success = run.result['successful_count'];
    const failed = run.result['failed_count'];
    if (typeof success === 'number' && typeof failed === 'number') {
      return `${success} sucesso, ${failed} erro`;
    }
    return 'resultado registrado';
  }

  modelResultValue(run: ModelRun | null, key: string): string {
    if (!run) {
      return 'n/a';
    }
    const value = run.result[key];
    if (typeof value === 'number') {
      return value.toFixed(Math.abs(value) >= 100 ? 1 : 4);
    }
    if (typeof value === 'string') {
      return value;
    }
    return 'n/a';
  }

  private selectedModelParameters(): Record<string, unknown> {
    if (this.selectedModel === 'gassmann') {
      return { ...this.gassmannForm };
    }
    if (this.selectedModel === 'softsand' || this.selectedModel === 'stiffsand') {
      return { ...this.granularForm };
    }
    return {
      ...this.avoForm,
      incident_angles_degrees: this.avoForm.incident_angles_degrees
        .split(',')
        .map((angle) => Number(angle.trim()))
        .filter((angle) => Number.isFinite(angle)),
    };
  }
}
