import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-rules',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="rules-page">
      <header class="page-header">
        <h1>Scheduling Rules</h1>
      </header>

      <div class="rules-section">
        <h2>Rule Templates</h2>
        <p class="text-muted">Click to add a pre-configured rule</p>
        <div class="templates-grid">
          @for (template of templates; track template.name) {
            <div class="card template-card" (click)="addFromTemplate(template.name)">
              <h4>{{ template.name }}</h4>
              <p>{{ template.description }}</p>
            </div>
          }
        </div>
      </div>

      <div class="rules-section">
        <h2>Active Rules</h2>
        @if (rules.length === 0) {
          <p class="empty-state">No rules configured. Add from templates above.</p>
        } @else {
          <div class="rules-list">
            @for (rule of rules; track rule.id) {
              <div class="card rule-card">
                <div class="rule-header">
                  <h4>{{ rule.name }}</h4>
                  <span class="priority-badge">Priority: {{ rule.priority }}</span>
                </div>
                @if (rule.description) {
                  <p class="rule-description">{{ rule.description }}</p>
                }
                <div class="rule-details">
                  <div class="conditions">
                    <strong>When:</strong>
                    @for (condition of rule.conditions; track $index) {
                      <span class="condition-tag">
                        {{ condition.condition_type }}: {{ condition.value }}
                      </span>
                    }
                  </div>
                  <div class="actions">
                    <strong>Then:</strong>
                    @for (action of rule.actions; track $index) {
                      <span class="action-tag">
                        {{ action.action_type }}: {{ formatActionValue(action.value) }}
                      </span>
                    }
                  </div>
                </div>
              </div>
            }
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .page-header {
      margin-bottom: var(--spacing-lg);
    }

    .rules-section {
      margin-bottom: var(--spacing-xl);

      h2 {
        margin-bottom: var(--spacing-sm);
      }
    }

    .templates-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: var(--spacing-md);
      margin-top: var(--spacing-md);
    }

    .template-card {
      cursor: pointer;
      transition: all 0.2s ease;

      &:hover {
        border-color: var(--color-primary);
        box-shadow: var(--shadow-md);
      }

      h4 { margin-bottom: var(--spacing-sm); }
      p { font-size: var(--font-size-sm); color: var(--text-secondary); }
    }

    .rules-list {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-md);
    }

    .rule-card {
      .rule-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--spacing-sm);
      }

      .priority-badge {
        font-size: var(--font-size-xs);
        padding: 2px 8px;
        background: var(--bg-tertiary);
        border-radius: 4px;
      }

      .rule-description {
        font-size: var(--font-size-sm);
        color: var(--text-secondary);
        margin-bottom: var(--spacing-md);
      }

      .rule-details {
        display: flex;
        flex-direction: column;
        gap: var(--spacing-sm);
        font-size: var(--font-size-sm);

        strong {
          margin-right: var(--spacing-sm);
        }
      }

      .condition-tag, .action-tag {
        display: inline-block;
        padding: 2px 8px;
        margin-right: var(--spacing-xs);
        border-radius: 4px;
        font-size: var(--font-size-xs);
      }

      .condition-tag {
        background: rgba(59, 130, 246, 0.1);
        color: var(--color-primary);
      }

      .action-tag {
        background: rgba(34, 197, 94, 0.1);
        color: var(--color-success);
      }
    }

    .empty-state {
      text-align: center;
      padding: var(--spacing-xl);
      color: var(--text-muted);
    }
  `]
})
export class RulesComponent implements OnInit {
  private api = inject(ApiService);

  templates: any[] = [];
  rules: any[] = [];

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.api.getRuleTemplates().subscribe({
      next: (data) => (this.templates = data),
      error: (err) => console.error('Failed to load templates', err),
    });

    this.api.getRules(true).subscribe({
      next: (data) => (this.rules = data),
      error: (err) => console.error('Failed to load rules', err),
    });
  }

  addFromTemplate(templateName: string) {
    this.api.createRuleFromTemplate(templateName).subscribe({
      next: () => this.loadData(),
      error: (err) => console.error('Failed to create rule', err),
    });
  }

  formatActionValue(value: any): string {
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    if (Array.isArray(value)) {
      return value.join(', ');
    }
    return String(value);
  }
}
