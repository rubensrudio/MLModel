import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export type HealthResponse = {
  status: string;
  service: string;
  version: string;
};

export type SampleSummary = {
  sample_count: number;
  well_count: number;
  rock_type_count: number;
  average_porosity_fraction: number;
  average_vp_m_s: number;
};

export type Sample = {
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

export type CrossplotPoint = {
  sample_code: string;
  x: number;
  y: number;
  color: string | null;
};

export type CrossplotResponse = {
  points: CrossplotPoint[];
  indicators: {
    sample_count: number;
    pearson_correlation: number | null;
    mean_absolute_error: number | null;
  };
};

export type ModelRun = {
  run_id: string;
  created_at: string;
  model_name: string;
  engine: string | null;
  parameters: Record<string, unknown>;
  result: Record<string, unknown>;
  saved_analysis_id: string | null;
  mlflow_run_id: string | null;
};

export type ModelKey = 'gassmann' | 'softsand' | 'stiffsand' | 'avo.aki-richards';
export type BatchInputMode = 'json' | 'csv';

export type ModelOption = {
  key: ModelKey;
  label: string;
  endpoint: string;
  batchModel: ModelKey;
};

export const MODEL_OPTIONS: ModelOption[] = [
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

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  getHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>('/health');
  }

  getSampleSummary(): Observable<SampleSummary> {
    return this.http.get<SampleSummary>('/api/samples/summary');
  }

  getSamples(): Observable<Sample[]> {
    return this.http.get<Sample[]>('/api/samples');
  }

  getModelRuns(): Observable<ModelRun[]> {
    return this.http.get<ModelRun[]>('/api/model-runs');
  }

  createCrossplot(filters: Record<string, string[]> = {}): Observable<CrossplotResponse> {
    return this.http.post<CrossplotResponse>('/api/analytics/crossplot', {
      x_field: 'porosity_percent',
      y_field: 'vp_m_s',
      color_by: 'rock_type',
      filters,
    });
  }

  executeModel(endpoint: string, parameters: Record<string, unknown>): Observable<ModelRun> {
    return this.http.post<ModelRun>(endpoint, {
      parameters,
      saved_analysis_id: null,
    });
  }

  executeBatch(payload: Record<string, unknown>): Observable<ModelRun> {
    return this.http.post<ModelRun>('/api/model-runs/rockphypy/batch', payload);
  }
}
