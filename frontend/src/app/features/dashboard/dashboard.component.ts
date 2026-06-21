import { CommonModule, DecimalPipe } from '@angular/common';
import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
  inject,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import type { ECharts } from 'echarts';

import { ApiService, CrossplotResponse, ModelRun, SampleSummary } from '../../core/api.service';

const CROSSPLOT_COLORS = ['#0f6f68', '#3867a8', '#8a6f24', '#7c4d8a', '#b84b3c'];

@Component({
  selector: 'mlm-dashboard',
  standalone: true,
  imports: [CommonModule, DecimalPipe, RouterLink],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements AfterViewInit, OnDestroy {
  private readonly api = inject(ApiService);
  private chart: ECharts | null = null;
  private viewReady = false;

  @ViewChild('crossplotChart') private chartElement?: ElementRef<HTMLDivElement>;

  summary: SampleSummary | null = null;
  crossplot: CrossplotResponse | null = null;
  modelRuns: ModelRun[] = [];
  loading = true;
  errorMessage = '';

  ngAfterViewInit(): void {
    this.viewReady = true;
    this.loadDashboard();
  }

  ngOnDestroy(): void {
    this.chart?.dispose();
  }

  get latestRun(): ModelRun | null {
    return this.modelRuns[0] ?? null;
  }

  loadDashboard(): void {
    this.loading = true;
    this.errorMessage = '';

    this.api.getSampleSummary().subscribe({
      next: (summary) => {
        this.summary = summary;
      },
      error: () => {
        this.errorMessage = 'Nao foi possivel carregar o resumo de amostras.';
      },
    });

    this.api.createCrossplot().subscribe({
      next: (crossplot) => {
        this.crossplot = crossplot;
        this.loading = false;
        void this.renderCrossplot();
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'Nao foi possivel carregar o crossplot.';
      },
    });

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

  private async renderCrossplot(): Promise<void> {
    if (!this.viewReady || !this.chartElement || !this.crossplot) {
      return;
    }

    const echartsModule = await import('echarts');
    this.chart ??= echartsModule.init(this.chartElement.nativeElement, undefined, {
      renderer: 'canvas',
    });

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
          const data = (params as { data: { name: string; value: number[]; rockType: string } })
            .data;
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
      series: [{ type: 'scatter', symbolSize: 10, data: seriesData }],
    });
  }
}
