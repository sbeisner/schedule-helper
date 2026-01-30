import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-courses',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="courses-page">
      <h1>Courses & Assignments</h1>

      <div class="courses-grid">
        @for (course of courses; track course.id) {
          <div class="card course-card">
            <div class="course-header">
              <span class="course-code">{{ course.code }}</span>
              <h3>{{ course.name }}</h3>
            </div>
            <div class="course-schedule">
              <span>{{ getDayName(course.day_of_week) }}</span>
              <span>{{ course.start_time }} - {{ course.end_time }}</span>
            </div>
            @if (course.location) {
              <div class="course-location">{{ course.location }}</div>
            }
          </div>
        }
      </div>

      <h2>Upcoming Assignments</h2>
      <div class="assignments-list">
        @for (assignment of assignments; track assignment.id) {
          <div class="card assignment-card" [class.overdue]="assignment.is_overdue">
            <div class="assignment-info">
              <h4>{{ assignment.name }}</h4>
              <span class="due-date">Due: {{ formatDate(assignment.due_date) }}</span>
            </div>
            <div class="assignment-actions">
              <span class="days-badge" [class.urgent]="assignment.days_until_due <= 3">
                {{ assignment.days_until_due }} days
              </span>
              @if (!assignment.is_completed) {
                <button class="btn btn-secondary btn-sm" (click)="complete(assignment)">
                  Complete
                </button>
              }
            </div>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    h1 { margin-bottom: var(--spacing-lg); }
    h2 { margin: var(--spacing-xl) 0 var(--spacing-md); }

    .courses-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: var(--spacing-md);
    }

    .course-card {
      .course-header {
        margin-bottom: var(--spacing-md);

        .course-code {
          font-size: var(--font-size-sm);
          color: var(--color-primary);
          font-weight: 600;
        }

        h3 { margin-top: var(--spacing-xs); }
      }

      .course-schedule {
        display: flex;
        gap: var(--spacing-md);
        color: var(--text-secondary);
        font-size: var(--font-size-sm);
      }

      .course-location {
        margin-top: var(--spacing-sm);
        font-size: var(--font-size-sm);
        color: var(--text-muted);
      }
    }

    .assignments-list {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
    }

    .assignment-card {
      display: flex;
      justify-content: space-between;
      align-items: center;

      &.overdue {
        border-left: 3px solid var(--color-danger);
      }

      .assignment-info {
        h4 { margin-bottom: var(--spacing-xs); }
        .due-date { font-size: var(--font-size-sm); color: var(--text-secondary); }
      }

      .assignment-actions {
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
      }

      .days-badge {
        padding: 4px 12px;
        border-radius: 4px;
        font-size: var(--font-size-sm);
        background: var(--bg-tertiary);

        &.urgent {
          background: rgba(239, 68, 68, 0.1);
          color: var(--color-danger);
        }
      }
    }

    .btn-sm {
      padding: 4px 12px;
      font-size: var(--font-size-sm);
    }
  `]
})
export class CoursesComponent implements OnInit {
  private api = inject(ApiService);

  courses: any[] = [];
  assignments: any[] = [];

  ngOnInit() {
    this.api.getCourses().subscribe({
      next: (data) => (this.courses = data),
      error: (err) => console.error('Failed to load courses', err),
    });

    this.api.getUpcomingAssignments(30).subscribe({
      next: (data) => (this.assignments = data),
      error: (err) => console.error('Failed to load assignments', err),
    });
  }

  getDayName(day: number): string {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    return days[day] || '';
  }

  formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  }

  complete(assignment: any) {
    // Would call API to mark complete
    console.log('Complete assignment:', assignment.id);
  }
}
