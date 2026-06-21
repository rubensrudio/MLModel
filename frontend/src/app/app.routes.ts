import { Routes } from '@angular/router';

import { DashboardComponent } from './features/dashboard/dashboard.component';
import { ModelRunsComponent } from './features/model-runs/model-runs.component';
import { RockPhysicsComponent } from './features/rock-physics/rock-physics.component';
import { SamplesComponent } from './features/samples/samples.component';

export const routes: Routes = [
  { path: 'dashboard', component: DashboardComponent },
  { path: 'samples', component: SamplesComponent },
  { path: 'rock-physics', component: RockPhysicsComponent },
  { path: 'model-runs', component: ModelRunsComponent },
  { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
  { path: '**', redirectTo: 'dashboard' },
];
