import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="app-container">
      <nav class="sidebar">
        <div class="sidebar-header">
          <h1 class="app-title">Schedule Manager</h1>
        </div>
        <ul class="nav-links">
          <li>
            <a routerLink="/dashboard" routerLinkActive="active">
              <span class="nav-icon">📊</span>
              Dashboard
            </a>
          </li>
          <li>
            <a routerLink="/calendar" routerLinkActive="active">
              <span class="nav-icon">📅</span>
              Calendar
            </a>
          </li>
          <li>
            <a routerLink="/projects" routerLinkActive="active">
              <span class="nav-icon">📁</span>
              Projects
            </a>
          </li>
          <li>
            <a routerLink="/courses" routerLinkActive="active">
              <span class="nav-icon">📚</span>
              Courses
            </a>
          </li>
          <li>
            <a routerLink="/rules" routerLinkActive="active">
              <span class="nav-icon">⚙️</span>
              Rules
            </a>
          </li>
          <li>
            <a routerLink="/settings" routerLinkActive="active">
              <span class="nav-icon">🔧</span>
              Settings
            </a>
          </li>
        </ul>
      </nav>
      <main class="main-content">
        <router-outlet></router-outlet>
      </main>
    </div>
  `,
  styles: [`
    .app-container {
      display: flex;
      height: 100vh;
    }

    .sidebar {
      width: 240px;
      background: var(--bg-primary);
      border-right: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
    }

    .sidebar-header {
      padding: var(--spacing-lg);
      border-bottom: 1px solid var(--border-color);
    }

    .app-title {
      font-size: var(--font-size-lg);
      font-weight: 700;
      color: var(--color-primary);
    }

    .nav-links {
      list-style: none;
      padding: var(--spacing-md);
      flex: 1;
    }

    .nav-links li {
      margin-bottom: var(--spacing-xs);
    }

    .nav-links a {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      padding: var(--spacing-sm) var(--spacing-md);
      border-radius: var(--border-radius);
      color: var(--text-secondary);
      font-weight: 500;
      transition: all 0.2s ease;
    }

    .nav-links a:hover {
      background: var(--bg-tertiary);
      color: var(--text-primary);
    }

    .nav-links a.active {
      background: rgba(59, 130, 246, 0.1);
      color: var(--color-primary);
    }

    .nav-icon {
      font-size: 18px;
    }

    .main-content {
      flex: 1;
      overflow-y: auto;
      padding: var(--spacing-lg);
    }
  `]
})
export class AppComponent {
  title = 'Schedule Manager';
}
