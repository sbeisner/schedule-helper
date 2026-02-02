import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';

interface TimeBlock {
  id: string;
  task_type: string;
  task_id: string;
  task_name: string;
  start_time: string;
  end_time: string;
  status: string;
  duration_hours: number;
  is_external?: boolean;
  is_completed?: boolean;
  title?: string;
}

interface DaySchedule {
  date: Date;
  dayName: string;
  blocks: TimeBlock[];
}

@Component({
  selector: 'app-calendar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="calendar">
      <header class="calendar-header">
        <h1>Weekly Schedule</h1>
        <div class="header-actions">
          <button class="btn btn-secondary" (click)="previousWeek()">← Previous</button>
          <span class="week-label">{{ weekLabel }}</span>
          <button class="btn btn-secondary" (click)="nextWeek()">Next →</button>
          <button class="btn btn-primary" (click)="generateSchedule()" [disabled]="isGenerating">
            @if (isGenerating) {
              <span class="spinner"></span> Generating...
            } @else {
              Regenerate Schedule
            }
          </button>
        </div>
      </header>

      <div class="calendar-grid">
        <!-- Time column -->
        <div class="time-column">
          <div class="time-header">Time</div>
          @for (hour of hours; track hour) {
            <div class="time-slot">
              {{ formatHour(hour) }}
            </div>
          }
        </div>

        <!-- Day columns -->
        @for (day of weekDays; track day.date.toISOString()) {
          <div class="day-column" [class.today]="isToday(day.date)">
            <div class="day-header">
              <div class="day-name">{{ day.dayName }}</div>
              <div class="day-date">{{ formatDate(day.date) }}</div>
            </div>
            <div class="day-grid">
              @for (hour of hours; track hour) {
                <div class="hour-slot"></div>
              }
              <!-- Time blocks -->
              @for (block of day.blocks; track block.id) {
                <div
                  class="time-block"
                  [class]="'type-' + block.task_type + (block.is_completed ? ' completed' : '')"
                  [style.top.px]="getBlockTop(block.start_time)"
                  [style.height.px]="getBlockHeight(block.duration_hours)"
                >
                  <div class="block-content">
                    <div class="block-header">
                      <div class="block-time">
                        {{ formatTime(block.start_time) }} - {{ formatTime(block.end_time) }}
                      </div>
                      @if (block.task_type === 'assignment' && !block.is_completed) {
                        <button class="complete-btn" (click)="completeAssignment($event, block)" title="Mark as complete">
                          ✓
                        </button>
                      }
                      @if (block.is_completed) {
                        <span class="completed-icon" title="Completed">✓</span>
                      }
                    </div>
                    <div class="block-title">{{ block.task_name }}</div>
                    <span class="block-badge">{{ block.task_type }}</span>
                  </div>
                </div>
              }
            </div>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .calendar {
      padding: var(--spacing-lg);
      height: 100%;
      display: flex;
      flex-direction: column;
    }

    .calendar-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--spacing-lg);
    }

    .header-actions {
      display: flex;
      gap: var(--spacing-md);
      align-items: center;
    }

    .week-label {
      font-weight: 600;
      min-width: 200px;
      text-align: center;
    }

    .calendar-grid {
      display: grid;
      grid-template-columns: 80px repeat(7, 1fr);
      gap: 1px;
      background: var(--border-color);
      border: 1px solid var(--border-color);
      flex: 1;
      overflow: auto;
    }

    .time-column {
      background: var(--bg-primary);
    }

    .time-header {
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      border-bottom: 1px solid var(--border-color);
      background: var(--bg-secondary);
    }

    .time-slot {
      height: 60px;
      display: flex;
      align-items: flex-start;
      justify-content: center;
      padding-top: 4px;
      font-size: var(--font-size-sm);
      color: var(--text-secondary);
      border-bottom: 1px solid var(--border-color);
      background: var(--bg-primary);
    }

    .day-column {
      background: var(--bg-primary);
      position: relative;
    }

    .day-column.today {
      background: rgba(59, 130, 246, 0.05);
    }

    .day-header {
      height: 60px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      border-bottom: 1px solid var(--border-color);
      background: var(--bg-secondary);
    }

    .day-column.today .day-header {
      background: var(--color-primary);
      color: white;
    }

    .day-name {
      font-weight: 600;
      font-size: var(--font-size-sm);
    }

    .day-date {
      font-size: var(--font-size-xs);
      color: var(--text-secondary);
    }

    .day-column.today .day-date {
      color: rgba(255, 255, 255, 0.9);
    }

    .day-grid {
      position: relative;
      height: 100%;
    }

    .hour-slot {
      height: 60px;
      border-bottom: 1px solid var(--border-color);
    }

    .time-block {
      position: absolute;
      left: 6px;
      right: 6px;
      border-radius: 6px;
      padding: 10px;
      overflow: visible;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
      z-index: 1;
      min-height: 60px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      margin: 2px 0;
    }

    .time-block:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
      z-index: 2;
      border-color: rgba(255, 255, 255, 0.5);
    }

    .time-block.type-project {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }

    .time-block.type-household {
      background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      color: white;
    }

    .time-block.type-assignment {
      background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
      color: white;
    }

    .time-block.type-personal {
      background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
      color: white;
    }

    .time-block.type-external {
      background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
      color: #2d3436;
      border-left: 4px solid #e17055;
    }

    .block-content {
      display: flex;
      flex-direction: column;
      gap: 4px;
      height: 100%;
    }

    .block-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }

    .block-time {
      font-size: var(--font-size-xs);
      opacity: 0.9;
      font-weight: 500;
      flex: 1;
    }

    .block-title {
      font-weight: 600;
      font-size: var(--font-size-sm);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.2;
      max-width: 100%;
    }

    .block-badge {
      font-size: 10px;
      text-transform: uppercase;
      opacity: 0.8;
      letter-spacing: 0.5px;
    }

    .complete-btn {
      background: rgba(255, 255, 255, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.5);
      color: white;
      border-radius: 50%;
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 14px;
      font-weight: bold;
      transition: all 0.2s;
      padding: 0;
      flex-shrink: 0;
    }

    .complete-btn:hover {
      background: rgba(255, 255, 255, 0.5);
      transform: scale(1.1);
    }

    .completed-icon {
      background: rgba(34, 197, 94, 0.9);
      border: 2px solid white;
      color: white;
      border-radius: 50%;
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: bold;
      flex-shrink: 0;
    }

    .time-block.completed {
      opacity: 0.7;
      filter: grayscale(0.3);
    }

    .time-block.completed .block-title {
      text-decoration: line-through;
    }

    .spinner {
      display: inline-block;
      width: 14px;
      height: 14px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      border-top-color: white;
      animation: spin 0.8s linear infinite;
      margin-right: 8px;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  `]
})
export class CalendarComponent implements OnInit {
  private api = inject(ApiService);

  weekDays: DaySchedule[] = [];
  hours: number[] = Array.from({ length: 16 }, (_, i) => i + 6); // 6 AM to 10 PM
  weekStart: Date = new Date();
  weekLabel: string = '';
  isGenerating: boolean = false;

  ngOnInit() {
    this.setWeekStart(new Date());
    this.loadSchedule();
  }

  setWeekStart(date: Date) {
    // Set to Monday of the week
    const day = date.getDay();
    const diff = date.getDate() - day + (day === 0 ? -6 : 1);
    this.weekStart = new Date(date.setDate(diff));
    this.weekStart.setHours(0, 0, 0, 0);

    this.generateWeekDays();
    this.updateWeekLabel();
  }

  generateWeekDays() {
    this.weekDays = [];
    const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

    for (let i = 0; i < 7; i++) {
      const date = new Date(this.weekStart);
      date.setDate(this.weekStart.getDate() + i);

      this.weekDays.push({
        date,
        dayName: dayNames[i],
        blocks: []
      });
    }
  }

  updateWeekLabel() {
    const end = new Date(this.weekStart);
    end.setDate(this.weekStart.getDate() + 6);

    const options: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };
    const startStr = this.weekStart.toLocaleDateString('en-US', options);
    const endStr = end.toLocaleDateString('en-US', options);

    this.weekLabel = `${startStr} - ${endStr}, ${this.weekStart.getFullYear()}`;
  }

  loadSchedule() {
    const startDate = this.weekStart.toISOString().split('T')[0];
    const endDate = new Date(this.weekStart);
    endDate.setDate(this.weekStart.getDate() + 6);
    const endDateStr = endDate.toISOString().split('T')[0];

    // First sync calendar events
    this.api.syncCalendarEvents(startDate, endDateStr).subscribe({
      next: () => {
        // Then load time blocks
        this.api.getTimeBlocks(startDate, endDateStr).subscribe({
          next: (blocks: TimeBlock[]) => {
            // Distribute blocks to their respective days
            blocks.forEach(block => {
              const blockDate = new Date(block.start_time);
              const dayIndex = this.weekDays.findIndex(day =>
                day.date.toDateString() === blockDate.toDateString()
              );

              if (dayIndex !== -1) {
                this.weekDays[dayIndex].blocks.push(block);
              }
            });
          },
          error: (err) => console.error('Failed to load schedule', err)
        });

        // Load external events
        this.api.getExternalEvents(startDate, endDateStr).subscribe({
          next: (events: any[]) => {
            // Convert external events to time blocks for display
            events.forEach(event => {
              const eventDate = new Date(event.start_time);
              const dayIndex = this.weekDays.findIndex(day =>
                day.date.toDateString() === eventDate.toDateString()
              );

              if (dayIndex !== -1) {
                // Calculate duration
                const start = new Date(event.start_time);
                const end = new Date(event.end_time);
                const durationHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);

                this.weekDays[dayIndex].blocks.push({
                  id: event.id,
                  task_type: 'external',
                  task_id: event.id,
                  task_name: event.title,
                  start_time: event.start_time,
                  end_time: event.end_time,
                  status: 'external',
                  duration_hours: durationHours,
                  is_external: true,
                  title: event.title
                });
              }
            });
          },
          error: (err) => console.error('Failed to load external events', err)
        });
      },
      error: (err) => {
        console.warn('Failed to sync calendar (may need re-authentication)', err);
        // Still try to load existing data
        this.api.getTimeBlocks(startDate, endDateStr).subscribe({
          next: (blocks: TimeBlock[]) => {
            blocks.forEach(block => {
              const blockDate = new Date(block.start_time);
              const dayIndex = this.weekDays.findIndex(day =>
                day.date.toDateString() === blockDate.toDateString()
              );
              if (dayIndex !== -1) {
                this.weekDays[dayIndex].blocks.push(block);
              }
            });
          },
          error: (err) => console.error('Failed to load schedule', err)
        });
      }
    });
  }

  generateSchedule() {
    this.isGenerating = true;
    this.api.generateSchedule(undefined, undefined, false).subscribe({
      next: () => {
        // Clear existing blocks
        this.weekDays.forEach(day => day.blocks = []);
        // Reload schedule
        this.loadSchedule();
        this.isGenerating = false;
      },
      error: (err) => {
        console.error('Failed to generate schedule', err);
        this.isGenerating = false;
      }
    });
  }

  previousWeek() {
    const newStart = new Date(this.weekStart);
    newStart.setDate(this.weekStart.getDate() - 7);
    this.setWeekStart(newStart);
    this.weekDays.forEach(day => day.blocks = []);
    this.loadSchedule();
  }

  nextWeek() {
    const newStart = new Date(this.weekStart);
    newStart.setDate(this.weekStart.getDate() + 7);
    this.setWeekStart(newStart);
    this.weekDays.forEach(day => day.blocks = []);
    this.loadSchedule();
  }

  formatDate(date: Date): string {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  formatHour(hour: number): string {
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    return `${displayHour} ${period}`;
  }

  formatTime(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  }

  isToday(date: Date): boolean {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  }

  getBlockTop(startTime: string): number {
    const date = new Date(startTime);
    const hour = date.getHours();
    const minute = date.getMinutes();

    // Calculate position from 6 AM (first hour shown)
    const hoursFrom6AM = hour - 6;
    const pixelsPerHour = 60;

    return (hoursFrom6AM * pixelsPerHour) + (minute / 60 * pixelsPerHour) + 60; // +60 for header
  }

  getBlockHeight(durationHours: number): number {
    const pixelsPerHour = 60;
    return durationHours * pixelsPerHour;
  }

  completeAssignment(event: Event, block: TimeBlock) {
    // Prevent event bubbling
    event.stopPropagation();

    if (block.task_type !== 'assignment') {
      return;
    }

    // Call the API to mark assignment as complete
    this.api.completeAssignment(block.task_id).subscribe({
      next: () => {
        // Update the block's completion status locally
        block.is_completed = true;
        console.log('Assignment marked as complete:', block.task_name);
      },
      error: (err) => {
        console.error('Failed to complete assignment', err);
        alert('Failed to mark assignment as complete. Please try again.');
      }
    });
  }
}
