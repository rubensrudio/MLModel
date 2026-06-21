import { CommonModule, DecimalPipe } from '@angular/common';
import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
  inject,
} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import type { ECharts } from 'echarts';

type HealthResponse = {
  status: string;
  service: string;
  version: string;
};

type SampleSummary = {
  sample_count: number;
  well_count: number;
  rock_type_count: number;
  average_porosity_fraction: number;
  average_vp_m_s: number;
};

type Sample = {
  sample_code: string;
  well: string;
  depth_m: number;
  porosity_fraction: number;
  permeability_md: number;
  rock_type: string;
  lithology_micro: string;
  vp_m_s: number;
  confining_pressure_psi: number;
};

type CrossplotPoint = {
  sample_code: string;
  x: number;
  y: number;
  color: string | null;
};

type CrossplotResponse = {
  points: CrossplotPoint[];
  indicators: {
    sample_count: number;
    pearson_correlation: number | null;
    mean_absolute_error: number | null;
  };
};

type ModelRun = {
  run_id: string;
  created_at: string;
  model_name: string;
  engine: string | null;
  parameters: Record<string, unknown>;
  result: Record<string, unknown>;
  saved_analysis_id: string | null;
  mlflow_run_id: string | null;
};

type ModelKey = 'gassmann' | 'softsand' | 'stiffsand' | 'avo.aki-richards';
type BatchInputMode = 'json' | 'csv';

type ModelOption = {
  key: ModelKey;
  label: string;
  endpoint: string;
  batchModel: ModelKey;
};

const CROSSPLOT_COLORS = ['#0f6f68', '#3867a8', '#8a6f24', '#7c4d8a', '#b84b3c'];

const MODEL_OPTIONS: ModelOption[] = [
  {
    key: 'gassmann',
    label: 'Gassmann',
    endpoint: '/api/model-runs/rockphypy/gassmann',
    batchModel: 'gassmann',
  },
  {
    key: 'softsand',
    label: 'Soft-sand',
    endpoint: '/api/model-runs/rockphypy/softsand',
    batchModel: 'softsand',
  },
  {
    key: 'stiffsand',
    label: 'Stiff-sand',
    endpoint: '/api/model-runs/rockphypy/stiffsand',
    batchModel: 'stiffsand',
  },
  {
    key: 'avo.aki-richards',
    label: 'Aki-Richards AVO',
    endpoint: '/api/model-runs/rockphypy/avo/aki-richards',
    batchModel: 'avo.aki-richards',
  },
];

@Component({
  selector: 'mlm-root',
  standalone: true,
  imports: [CommonModule, FormsModule, DecimalPipe],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent implements AfterViewInit, OnDestroy {
  private readonly http = inject(HttpClient);
  private chart: ECharts | null = null;
  private viewReady = false;

  @ViewChild('crossplotChart') private chartElement?: ElementRef<HTMLDivElement>;

  health: HealthResponse | null = null;
  summary: SampleSummary | null = null;
  samples: Sample[] = [];
  modelRuns: ModelRun[] = [];
  crossplot: CrossplotResponse | null = null;
  selectedWell = '';
  selectedRockType = '';
  loading = true;
  modelRunning = false;
  batchRunning = false;
  errorMessage = '';
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

  ngAfterViewInit(): void {
    this.viewReady = true;
    this.loadWorkspace();
  }

  ngOnDestroy(): void {
    this.chart?.dispose();
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

  loadWorkspace(): void {
    this.loading = true;
    this.errorMessage = '';

    this.http.get<HealthResponse>('/health').subscribe({
      next: (health) => {
        this.health = health;
      },
      error: () => {
        this.errorMessage = 'Backend indisponivel em /health.';
      },
    });

    this.http.get<SampleSummary>('/api/samples/summary').subscribe({
      next: (summary) => {
        this.summary = summary;
      },
      error: () => {
        this.errorMessage = 'Nao foi possivel carregar o resumo de amostras.';
      },
    });

    this.http.get<Sample[]>('/api/samples').subscribe({
      next: (samples) => {
        this.samples = samples;
        this.loadCrossplot();
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'Nao foi possivel carregar as amostras.';
      },
    });

    this.http.get<ModelRun[]>('/api/model-runs').subscribe({
      next: (runs) => {
        this.modelRuns = runs;
      },
      error: () => {
        this.modelRuns = [];
      },
    });
  }

  applyFilters(): void {
    this.loadCrossplot();
  }

  resetFilters(): void {
    this.selectedWell = '';
    this.selectedRockType = '';
    this.loadCrossplot();
  }

  exportLatestRunCsv(): void {
    if (!this.latestRun) {
      return;
    }
    window.location.href = `/api/model-runs/${this.latestRun.run_id}/export/csv`;
  }

  executeSelectedModel(): void {
    const parameters = this.selectedModelParameters();
    this.modelRunning = true;
    this.modelMessage = '';

    this.http
      .post<ModelRun>(this.selectedModelOption.endpoint, {
        parameters,
        saved_analysis_id: null,
      })
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

    this.http.post<ModelRun>('/api/model-runs/rockphypy/batch', payload).subscribe({
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

  private loadCrossplot(): void {
    const filters: Record<string, string[]> = {};
    if (this.selectedWell) {
      filters['wells'] = [this.selectedWell];
    }
    if (this.selectedRockType) {
      filters['rock_types'] = [this.selectedRockType];
    }

    this.http
      .post<CrossplotResponse>('/api/analytics/crossplot', {
        x_field: 'porosity_percent',
        y_field: 'vp_m_s',
        color_by: 'rock_type',
        filters,
      })
      .subscribe({
        next: (crossplot) => {
          this.crossplot = crossplot;
          this.loading = false;
          this.renderCrossplot();
        },
        error: () => {
          this.loading = false;
          this.errorMessage = 'Nao foi possivel carregar o crossplot.';
        },
      });
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

  private async renderCrossplot(): Promise<void> {
    if (!this.viewReady || !this.chartElement || !this.crossplot) {
      return;
    }

    const echartsModule = await import('echarts');
    const element = this.chartElement.nativeElement;
    this.chart ??= echartsModule.init(element, undefined, { renderer: 'canvas' });

    const colorByRockType = new Map<string, string>();
    let colorIndex = 0;
    const seriesData = this.crossplot.points.map((point) => {
      const key = point.color ?? 'Unknown';
      if (!colorByRockType.has(key)) {
        colorByRockType.set(key, CROSSPLOT_COLORS[colorIndex % CROSSPLOT_COLORS.length]);
        colorIndex += 1;
      }
      return {
        name: point.sample_code,
        value: [point.x, point.y],
        itemStyle: { color: colorByRockType.get(key) },
        rockType: key,
      };
    });

    this.chart.setOption({
      grid: { left: 56, right: 16, top: 20, bottom: 42 },
      tooltip: {
        trigger: 'item',
        formatter: (params: unknown) => {
          const data = (params as { data: { name: string; value: number[]; rockType: string } }).data;
          return `${data.name}<br>${data.rockType}<br>Porosity ${data.value[0].toFixed(2)}%<br>Vp ${data.value[1].toFixed(0)} m/s`;
        },
      },
      xAxis: {
        name: 'Porosity (%)',
        nameLocation: 'middle',
        nameGap: 28,
        axisLine: { lineStyle: { color: '#9aa8a4' } },
        splitLine: { lineStyle: { color: 'rgba(20,36,32,0.08)' } },
      },
      yAxis: {
        name: 'Vp (m/s)',
        nameGap: 42,
        axisLine: { lineStyle: { color: '#9aa8a4' } },
        splitLine: { lineStyle: { color: 'rgba(20,36,32,0.08)' } },
      },
      series: [
        {
          type: 'scatter',
          symbolSize: 10,
          data: seriesData,
        },
      ],
    });
  }
}
