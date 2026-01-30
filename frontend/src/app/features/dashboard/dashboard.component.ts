import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="dashboard">
      <header class="dashboard-header">
        <h1>Dashboard</h1>
        <div class="header-actions">
          <button class="btn btn-primary" (click)="generateSchedule()">
            Generate Schedule
          </button>
        </div>
      </header>

      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="card summary-card">
          <h3>Available Hours</h3>
          <div class="stat">{{ summary?.total_available_hours || 0 }}</div>
          <span class="stat-label">This week</span>
        </div>
        <div class="card summary-card">
          <h3>Scheduled</h3>
          <div class="stat">{{ summary?.total_scheduled_hours || 0 }}</div>
          <span class="stat-label">Hours blocked</span>
        </div>
        <div class="card summary-card">
          <h3>Meetings</h3>
          <div class="stat">{{ summary?.meeting_hours || 0 }}</div>
          <span class="stat-label">Hours in meetings</span>
        </div>
        <div class="card summary-card">
          <h3>Free Time</h3>
          <div class="stat">{{ summary?.free_hours || 0 }}</div>
          <span class="stat-label">Hours available</span>
        </div>
      </div>

      <div class="dashboard-grid">
        <!-- Today's Schedule -->
        <div class="card">
          <h2>Today's Schedule</h2>
          @if (todayBlocks.length === 0) {
            <p class="empty-state">No blocks scheduled for today</p>
          } @else {
            <div class="time-blocks">
              @for (block of todayBlocks; track block.id) {
                <div class="time-block" [class]="'type-' + block.task_type">
                  <div class="block-time">
                    {{ formatTime(block.start_time) }} - {{ formatTime(block.end_time) }}
                  </div>
                  <div class="block-name">{{ block.task_name }}</div>
                  <span class="badge" [class]="'badge-' + block.task_type">
                    {{ block.task_type }}
                  </span>
                </div>
              }
            </div>
          }
        </div>

        <!-- Upcoming Deadlines -->
        <div class="card">
          <h2>Upcoming Deadlines</h2>
          @if (upcomingAssignments.length === 0) {
            <p class="empty-state">No upcoming deadlines</p>
          } @else {
            <div class="deadline-list">
              @for (assignment of upcomingAssignments; track assignment.id) {
                <div class="deadline-item" [class.overdue]="assignment.is_overdue">
                  <div class="deadline-info">
                    <span class="deadline-name">{{ assignment.name }}</span>
                    <span class="deadline-date">
                      Due: {{ formatDate(assignment.due_date) }}
                    </span>
                  </div>
                  <span class="days-badge" [class.urgent]="assignment.days_until_due <= 3">
                    {{ assignment.days_until_due }} days
                  </span>
                </div>
              }
            </div>
          }
        </div>

        <!-- Active Projects -->
        <div class="card">
          <h2>Active Projects</h2>
          @if (projects.length === 0) {
            <p class="empty-state">No active projects</p>
          } @else {
            <div class="project-list">
              @for (project of projects; track project.id) {
                <div class="project-item">
                  <div class="project-info">
                    <span class="project-name">{{ project.name }}</span>
                    <div class="progress-bar">
                      <div
                        class="progress-fill"
                        [style.width.%]="getProgressPercent(project)"
                      ></div>
                    </div>
                  </div>
                  <span class="hours-label">
                    {{ project.hours_used | number: '1.1-1' }} /
                    {{ project.total_hours_allocated }} hrs
                  </span>
                </div>
              }
            </div>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--spacing-lg);
    }

    .summary-cards {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: var(--spacing-md);
      margin-bottom: var(--spacing-lg);
    }

    .summary-card {
      text-align: center;

      h3 {
        font-size: var(--font-size-sm);
        color: var(--text-secondary);
        margin-bottom: var(--spacing-sm);
      }

      .stat {
        font-size: var(--font-size-2xl);
        font-weight: 700;
        color: var(--color-primary);
      }

      .stat-label {
        font-size: var(--font-size-xs);
        color: var(--text-muted);
      }
    }

    .dashboard-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: var(--spacing-lg);
    }

    .card h2 {
      font-size: var(--font-size-lg);
      margin-bottom: var(--spacing-md);
      padding-bottom: var(--spacing-sm);
      border-bottom: 1px solid var(--border-color);
    }

    .empty-state {
      color: var(--text-muted);
      text-align: center;
      padding: var(--spacing-lg);
    }

    .time-blocks {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
    }

    .time-block {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-sm) var(--spacing-md);
      border-radius: var(--border-radius);
      background: var(--bg-secondary);
      border-left: 3px solid var(--color-primary);

      &.type-project { border-left-color: var(--color-project); }
      &.type-assignment { border-left-color: var(--color-assignment); }
      &.type-household { border-left-color: var(--color-household); }
    }

    .block-time {
      font-size: var(--font-size-sm);
      color: var(--text-secondary);
      min-width: 120px;
    }

    .block-name {
      flex: 1;
      font-weight: 500;
    }

    .deadline-list {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
    }

    .deadline-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--spacing-sm);
      border-radius: var(--border-radius);
      background: var(--bg-secondary);

      &.overdue {
        background: rgba(239, 68, 68, 0.1);
      }
    }

    .deadline-info {
      display: flex;
      flex-direction: column;
    }

    .deadline-name {
      font-weight: 500;
    }

    .deadline-date {
      font-size: var(--font-size-sm);
      color: var(--text-secondary);
    }

    .days-badge {
      padding: 2px 8px;
      border-radius: 4px;
      font-size: var(--font-size-xs);
      background: var(--bg-tertiary);

      &.urgent {
        background: rgba(239, 68, 68, 0.1);
        color: var(--color-danger);
      }
    }

    .project-list {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-md);
    }

    .project-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .project-info {
      flex: 1;
      margin-right: var(--spacing-md);
    }

    .project-name {
      display: block;
      font-weight: 500;
      margin-bottom: var(--spacing-xs);
    }

    .progress-bar {
      height: 6px;
      background: var(--bg-tertiary);
      border-radius: 3px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: var(--color-primary);
      transition: width 0.3s ease;
    }

    .hours-label {
      font-size: var(--font-size-sm);
      color: var(--text-secondary);
      white-space: nowrap;
    }
  `]
})
export class DashboardComponent implements OnInit {
  private api = inject(ApiService);

  summary: any = null;
  todayBlocks: any[] = [];
  upcomingAssignments: any[] = [];
  projects: any[] = [];

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    // Get schedule summary
    this.api.getScheduleSummary().subscribe({
      next: (data) => (this.summary = data),
      error: (err) => console.error('Failed to load summary', err),
    });

    // Get today's blocks
    const today = new Date().toISOString().split('T')[0];
    this.api.getTimeBlocks(today, today).subscribe({
      next: (data) => (this.todayBlocks = data),
      error: (err) => console.error('Failed to load blocks', err),
    });

    // Get upcoming assignments
    this.api.getUpcomingAssignments(14).subscribe({
      next: (data) => (this.upcomingAssignments = data.slice(0, 5)),
      error: (err) => console.error('Failed to load assignments', err),
    });

    // Get active projects
    this.api.getProjects(true).subscribe({
      next: (data) => (this.projects = data.slice(0, 5)),
      error: (err) => console.error('Failed to load projects', err),
    });
  }

  generateSchedule() {
    this.api.generateSchedule(undefined, undefined, false).subscribe({
      next: () => {
        this.loadData();
      },
      error: (err) => console.error('Failed to generate schedule', err),
    });
  }

  formatTime(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  }

  formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  }

  getProgressPercent(project: any): number {
    if (!project.total_hours_allocated) return 0;
    return Math.min(
      100,
      (project.hours_used / project.total_hours_allocated) * 100
    );
  }
}
