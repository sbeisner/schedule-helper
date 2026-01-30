import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-calendar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="calendar-page">
      <h1>Calendar</h1>
      <p class="text-muted">Weekly calendar view coming in Phase 4</p>
      <div class="card">
        <p>This page will show:</p>
        <ul>
          <li>Weekly time grid with scheduled blocks</li>
          <li>External calendar events (meetings)</li>
          <li>Drag-and-drop rescheduling</li>
          <li>Color-coded task types</li>
        </ul>
      </div>
    </div>
  `,
  styles: [`
    .calendar-page {
      h1 { margin-bottom: var(--spacing-md); }
      .card { margin-top: var(--spacing-lg); }
      ul { margin-left: var(--spacing-lg); margin-top: var(--spacing-md); }
      li { margin-bottom: var(--spacing-sm); }
    }
  `]
})
export class CalendarComponent {}
