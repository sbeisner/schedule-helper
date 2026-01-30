import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-projects',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="projects-page">
      <header class="page-header">
        <h1>Projects</h1>
        <button class="btn btn-primary" (click)="showForm = !showForm">
          {{ showForm ? 'Cancel' : '+ Add Project' }}
        </button>
      </header>

      @if (showForm) {
        <div class="card form-card">
          <h3>New Project</h3>
          <form (ngSubmit)="createProject()">
            <div class="form-group">
              <label>Project Name</label>
              <input class="form-control" [(ngModel)]="newProject.name" name="name" required />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Total Hours</label>
                <input
                  class="form-control"
                  type="number"
                  [(ngModel)]="newProject.total_hours_allocated"
                  name="hours"
                />
              </div>
              <div class="form-group">
                <label>Weekly Cap</label>
                <input
                  class="form-control"
                  type="number"
                  [(ngModel)]="newProject.weekly_hour_cap"
                  name="weekly_cap"
                />
              </div>
              <div class="form-group">
                <label>Daily Cap</label>
                <input
                  class="form-control"
                  type="number"
                  [(ngModel)]="newProject.daily_hour_cap"
                  name="daily_cap"
                />
              </div>
            </div>
            <div class="form-group">
              <label>Priority</label>
              <select class="form-control" [(ngModel)]="newProject.priority" name="priority">
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
                <option value="flexible">Flexible</option>
              </select>
            </div>
            <button type="submit" class="btn btn-primary">Create Project</button>
          </form>
        </div>
      }

      <div class="projects-grid">
        @for (project of projects; track project.id) {
          <div class="card project-card">
            <div class="project-header">
              <h3>{{ project.name }}</h3>
              <span class="badge" [class]="'priority-' + project.priority">
                {{ project.priority }}
              </span>
            </div>
            <div class="project-stats">
              <div class="stat">
                <span class="stat-value">{{ project.hours_used | number: '1.1-1' }}</span>
                <span class="stat-label">/ {{ project.total_hours_allocated }} hrs</span>
              </div>
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  [style.width.%]="getProgressPercent(project)"
                ></div>
              </div>
            </div>
            @if (project.weekly_hour_cap || project.daily_hour_cap) {
              <div class="caps">
                @if (project.weekly_hour_cap) {
                  <span class="cap">Weekly: {{ project.weekly_hour_cap }}h</span>
                }
                @if (project.daily_hour_cap) {
                  <span class="cap">Daily: {{ project.daily_hour_cap }}h</span>
                }
              </div>
            }
            <div class="project-actions">
              <button class="btn btn-secondary" (click)="logHours(project)">
                Log Hours
              </button>
            </div>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--spacing-lg);
    }

    .form-card {
      margin-bottom: var(--spacing-lg);

      h3 { margin-bottom: var(--spacing-md); }
    }

    .form-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: var(--spacing-md);
    }

    .projects-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: var(--spacing-md);
    }

    .project-card {
      .project-header {
        display: flex;
        justify-content: space-between;
        align-items: start;
        margin-bottom: var(--spacing-md);

        h3 { font-size: var(--font-size-lg); }
      }

      .project-stats {
        margin-bottom: var(--spacing-md);

        .stat {
          display: flex;
          align-items: baseline;
          gap: var(--spacing-xs);
          margin-bottom: var(--spacing-sm);
        }

        .stat-value {
          font-size: var(--font-size-xl);
          font-weight: 700;
          color: var(--color-primary);
        }

        .stat-label {
          color: var(--text-secondary);
        }
      }

      .progress-bar {
        height: 8px;
        background: var(--bg-tertiary);
        border-radius: 4px;
        overflow: hidden;
      }

      .progress-fill {
        height: 100%;
        background: var(--color-primary);
      }

      .caps {
        display: flex;
        gap: var(--spacing-md);
        margin-bottom: var(--spacing-md);
        font-size: var(--font-size-sm);
        color: var(--text-secondary);
      }

      .project-actions {
        padding-top: var(--spacing-md);
        border-top: 1px solid var(--border-color);
      }
    }
  `]
})
export class ProjectsComponent implements OnInit {
  private api = inject(ApiService);

  projects: any[] = [];
  showForm = false;
  newProject = {
    name: '',
    total_hours_allocated: 40,
    weekly_hour_cap: null as number | null,
    daily_hour_cap: null as number | null,
    priority: 'medium',
  };

  ngOnInit() {
    this.loadProjects();
  }

  loadProjects() {
    this.api.getProjects(true).subscribe({
      next: (data) => (this.projects = data),
      error: (err) => console.error('Failed to load projects', err),
    });
  }

  createProject() {
    this.api.createProject(this.newProject).subscribe({
      next: () => {
        this.showForm = false;
        this.resetForm();
        this.loadProjects();
      },
      error: (err) => console.error('Failed to create project', err),
    });
  }

  logHours(project: any) {
    const hours = prompt('Hours to log:', '1');
    if (hours && !isNaN(parseFloat(hours))) {
      this.api.logProjectHours(project.id, parseFloat(hours)).subscribe({
        next: () => this.loadProjects(),
        error: (err) => console.error('Failed to log hours', err),
      });
    }
  }

  getProgressPercent(project: any): number {
    if (!project.total_hours_allocated) return 0;
    return Math.min(100, (project.hours_used / project.total_hours_allocated) * 100);
  }

  private resetForm() {
    this.newProject = {
      name: '',
      total_hours_allocated: 40,
      weekly_hour_cap: null,
      daily_hour_cap: null,
      priority: 'medium',
    };
  }
}
