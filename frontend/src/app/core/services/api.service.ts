import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private http = inject(HttpClient);
  private baseUrl = environment.apiUrl;

  // Projects
  getProjects(activeOnly = true): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/projects`, {
      params: { active_only: activeOnly.toString() },
    });
  }

  getProject(id: string): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/projects/${id}`);
  }

  createProject(project: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/projects`, project);
  }

  updateProject(id: string, project: any): Observable<any> {
    return this.http.put<any>(`${this.baseUrl}/projects/${id}`, project);
  }

  deleteProject(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/projects/${id}`);
  }

  logProjectHours(id: string, hours: number): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/projects/${id}/log-hours`, null, {
      params: { hours: hours.toString() },
    });
  }

  // Household Tasks
  getTasks(activeOnly = true): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/tasks`, {
      params: { active_only: activeOnly.toString() },
    });
  }

  completeTask(id: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/tasks/${id}/complete`, null);
  }

  // Courses
  getCourses(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/courses`);
  }

  getCourse(id: string): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/courses/${id}`);
  }

  createCourse(course: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/courses`, course);
  }

  getCourseAssignments(courseId: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/courses/${courseId}/assignments`);
  }

  getUpcomingAssignments(days = 14): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/courses/assignments/upcoming`, {
      params: { days: days.toString() },
    });
  }

  // Calendar / Time Blocks
  getTimeBlocks(startDate?: string, endDate?: string): Observable<any[]> {
    const params: any = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return this.http.get<any[]>(`${this.baseUrl}/calendar/blocks`, { params });
  }

  createTimeBlock(block: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/calendar/blocks`, block);
  }

  updateTimeBlock(id: string, block: any): Observable<any> {
    return this.http.put<any>(`${this.baseUrl}/calendar/blocks/${id}`, block);
  }

  completeTimeBlock(id: string, actualMinutes?: number): Observable<any> {
    const params: any = {};
    if (actualMinutes) params.actual_minutes = actualMinutes.toString();
    return this.http.post<any>(`${this.baseUrl}/calendar/blocks/${id}/complete`, null, { params });
  }

  skipTimeBlock(id: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/calendar/blocks/${id}/skip`, null);
  }

  getExternalEvents(startDate?: string, endDate?: string): Observable<any[]> {
    const params: any = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return this.http.get<any[]>(`${this.baseUrl}/calendar/events`, { params });
  }

  // Scheduling
  generateSchedule(startDate?: string, endDate?: string, previewOnly = true): Observable<any[]> {
    const params: any = { preview_only: previewOnly.toString() };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return this.http.post<any[]>(`${this.baseUrl}/schedule/generate`, null, { params });
  }

  getScheduleSummary(startDate?: string, endDate?: string): Observable<any> {
    const params: any = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return this.http.get<any>(`${this.baseUrl}/schedule/summary`, { params });
  }

  clearScheduledBlocks(startDate?: string, endDate?: string): Observable<any> {
    const params: any = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return this.http.delete<any>(`${this.baseUrl}/schedule/clear`, { params });
  }

  // Rules
  getRules(activeOnly = true): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/rules`, {
      params: { active_only: activeOnly.toString() },
    });
  }

  getRuleTemplates(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/rules/templates`);
  }

  createRuleFromTemplate(templateName: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/rules/from-template`, null, {
      params: { template_name: templateName },
    });
  }

  // Config
  getConfig(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/config`);
  }

  updateConfig(config: any): Observable<any> {
    return this.http.put<any>(`${this.baseUrl}/config`, config);
  }

  setProjectsSheet(spreadsheetId: string, rangeName?: string): Observable<any> {
    const params: any = { spreadsheet_id: spreadsheetId };
    if (rangeName) params.range_name = rangeName;
    return this.http.post<any>(`${this.baseUrl}/config/google-sheets/projects`, null, { params });
  }

  setHouseholdSheet(spreadsheetId: string, rangeName?: string): Observable<any> {
    const params: any = { spreadsheet_id: spreadsheetId };
    if (rangeName) params.range_name = rangeName;
    return this.http.post<any>(`${this.baseUrl}/config/google-sheets/household`, null, { params });
  }
}
