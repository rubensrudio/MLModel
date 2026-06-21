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

const CROSSPLOT_COLORS = ['#0f6f68', '#3867a8', '#8a6f24', '#7c4d8a', '#b84b3c'];

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
  errorMessage = '';

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
