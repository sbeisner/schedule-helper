import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="settings-page">
      <h1>Settings</h1>

      <div class="settings-grid">
        <!-- Work Schedule -->
        <div class="card">
          <h2>Work Schedule</h2>
          <p class="text-muted">Configure your standard working hours</p>

          <div class="schedule-grid">
            @for (day of days; track day.value) {
              <div class="day-row">
                <label class="day-label">
                  <input
                    type="checkbox"
                    [checked]="isWorkingDay(day.value)"
                    (change)="toggleWorkingDay(day.value)"
                  />
                  {{ day.name }}
                </label>
                @if (isWorkingDay(day.value)) {
                  <div class="time-inputs">
                    <input
                      type="time"
                      class="form-control"
                      [value]="getStartTime(day.value)"
                      (change)="updateStartTime(day.value, $event)"
                    />
                    <span>to</span>
                    <input
                      type="time"
                      class="form-control"
                      [value]="getEndTime(day.value)"
                      (change)="updateEndTime(day.value, $event)"
                    />
                  </div>
                }
              </div>
            }
          </div>
        </div>

        <!-- Google Integration -->
        <div class="card">
          <h2>Google Integration</h2>
          <p class="text-muted">Connect your Google Calendar and Sheets</p>

          <div class="integration-section">
            <h3>Google Calendar</h3>
            <div class="integration-status">
              <span class="status-dot" [class.connected]="config?.google_calendar_id"></span>
              {{ config?.google_calendar_id ? 'Connected' : 'Not connected' }}
            </div>
            <button class="btn btn-secondary">Connect Google Account</button>
          </div>

          <div class="integration-section">
            <h3>Projects Sheet</h3>
            <div class="form-group">
              <label>Spreadsheet ID</label>
              <input
                class="form-control"
                [(ngModel)]="projectsSheetId"
                placeholder="Enter Google Sheets ID"
              />
            </div>
            <button class="btn btn-secondary" (click)="saveProjectsSheet()">
              Save
            </button>
          </div>

          <div class="integration-section">
            <h3>Household Tasks Sheet</h3>
            <div class="form-group">
              <label>Spreadsheet ID</label>
              <input
                class="form-control"
                [(ngModel)]="householdSheetId"
                placeholder="Enter Google Sheets ID"
              />
            </div>
            <button class="btn btn-secondary" (click)="saveHouseholdSheet()">
              Save
            </button>
          </div>
        </div>

        <!-- Scheduling Preferences -->
        <div class="card">
          <h2>Scheduling Preferences</h2>

          <div class="form-group">
            <label>Preferred Block Duration (minutes)</label>
            <input
              type="number"
              class="form-control"
              [(ngModel)]="config.preferred_block_duration_minutes"
              min="15"
              max="240"
            />
          </div>

          <div class="form-group">
            <label>Min Break Between Blocks (minutes)</label>
            <input
              type="number"
              class="form-control"
              [(ngModel)]="config.min_break_between_blocks_minutes"
              min="0"
              max="60"
            />
          </div>

          <div class="form-group">
            <label>Schedule Horizon (days)</label>
            <input
              type="number"
              class="form-control"
              [(ngModel)]="config.schedule_horizon_days"
              min="1"
              max="90"
            />
          </div>

          <button class="btn btn-primary" (click)="saveConfig()">
            Save Preferences
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    h1 { margin-bottom: var(--spacing-lg); }

    .settings-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: var(--spacing-lg);
    }

    .card {
      h2 {
        margin-bottom: var(--spacing-xs);
      }

      > p {
        margin-bottom: var(--spacing-lg);
      }
    }

    .schedule-grid {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
    }

    .day-row {
      display: flex;
      align-items: center;
      gap: var(--spacing-md);
      padding: var(--spacing-sm) 0;
      border-bottom: 1px solid var(--border-color);
    }

    .day-label {
      min-width: 120px;
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      cursor: pointer;
    }

    .time-inputs {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);

      input {
        width: 120px;
      }
    }

    .integration-section {
      margin-bottom: var(--spacing-lg);
      padding-bottom: var(--spacing-lg);
      border-bottom: 1px solid var(--border-color);

      h3 {
        font-size: var(--font-size-md);
        margin-bottom: var(--spacing-sm);
      }

      &:last-child {
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
      }
    }

    .integration-status {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      margin-bottom: var(--spacing-md);
      font-size: var(--font-size-sm);
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--color-danger);

      &.connected {
        background: var(--color-success);
      }
    }

    .form-group {
      margin-bottom: var(--spacing-md);
    }
  `]
})
export class SettingsComponent implements OnInit {
  private api = inject(ApiService);

  config: any = {};
  projectsSheetId = '';
  householdSheetId = '';

  days = [
    { value: 0, name: 'Monday' },
    { value: 1, name: 'Tuesday' },
    { value: 2, name: 'Wednesday' },
    { value: 3, name: 'Thursday' },
    { value: 4, name: 'Friday' },
    { value: 5, name: 'Saturday' },
    { value: 6, name: 'Sunday' },
  ];

  ngOnInit() {
    this.api.getConfig().subscribe({
      next: (data) => {
        this.config = data;
        this.projectsSheetId = data.google_sheets_projects_id || '';
        this.householdSheetId = data.google_sheets_household_id || '';
      },
      error: (err) => console.error('Failed to load config', err),
    });
  }

  isWorkingDay(day: number): boolean {
    const schedule = this.config.work_schedules?.find((s: any) => s.day_of_week === day);
    return schedule?.is_working_day ?? day < 5;
  }

  getStartTime(day: number): string {
    const schedule = this.config.work_schedules?.find((s: any) => s.day_of_week === day);
    return schedule?.start_time || '08:00';
  }

  getEndTime(day: number): string {
    const schedule = this.config.work_schedules?.find((s: any) => s.day_of_week === day);
    return schedule?.end_time || '16:00';
  }

  toggleWorkingDay(day: number) {
    // Would update config
    console.log('Toggle working day:', day);
  }

  updateStartTime(day: number, event: Event) {
    const value = (event.target as HTMLInputElement).value;
    console.log('Update start time:', day, value);
  }

  updateEndTime(day: number, event: Event) {
    const value = (event.target as HTMLInputElement).value;
    console.log('Update end time:', day, value);
  }

  saveProjectsSheet() {
    if (this.projectsSheetId) {
      this.api.setProjectsSheet(this.projectsSheetId).subscribe({
        next: () => console.log('Projects sheet saved'),
        error: (err) => console.error('Failed to save projects sheet', err),
      });
    }
  }

  saveHouseholdSheet() {
    if (this.householdSheetId) {
      this.api.setHouseholdSheet(this.householdSheetId).subscribe({
        next: () => console.log('Household sheet saved'),
        error: (err) => console.error('Failed to save household sheet', err),
      });
    }
  }

  saveConfig() {
    this.api.updateConfig(this.config).subscribe({
      next: () => console.log('Config saved'),
      error: (err) => console.error('Failed to save config', err),
    });
  }
}
