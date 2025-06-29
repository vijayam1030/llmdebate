import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { interval, Subscription } from 'rxjs';
import { switchMap, takeWhile } from 'rxjs/operators';

interface SystemStatus {
  system_initialized: boolean;
  available_models: string[];
  missing_models: string[];
  ollama_connected: boolean;
}

interface DebateRequest {
  question: string;
  max_rounds?: number;
}

interface DebateResponse {
  debate_id: string;
  status: string;
  message: string;
}

interface DebateStatus {
  debate_id: string;
  status: string;
  progress: number;
  current_round?: number;
  total_rounds?: number;
  question?: string;
  result?: any;
}

@Component({
  selector: 'app-root',
  template: `
    <mat-toolbar color="primary">
      <span>LLM Debate System</span>
      <span class="spacer"></span>
      <mat-icon>psychology</mat-icon>
    </mat-toolbar>

    <div class="container">
      <!-- System Status Card -->
      <mat-card class="status-card">
        <mat-card-header>
          <mat-card-title>System Status</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div *ngIf="systemStatus">
            <p><strong>Status:</strong> 
              <span [ngClass]="systemStatus.system_initialized ? 'status-ok' : 'status-error'">
                {{ systemStatus.system_initialized ? 'Ready' : 'Not Initialized' }}
              </span>
            </p>
            <p><strong>Ollama Connected:</strong> 
              <span [ngClass]="systemStatus.ollama_connected ? 'status-ok' : 'status-error'">
                {{ systemStatus.ollama_connected ? 'Yes' : 'No' }}
              </span>
            </p>
            <p><strong>Models Available:</strong> {{ systemStatus.available_models.length || 0 }}</p>
            <p *ngIf="systemStatus.available_models.length > 0"><strong>Available Models:</strong></p>
            <ul *ngIf="systemStatus.available_models.length > 0">
              <li *ngFor="let model of systemStatus.available_models">{{ model }}</li>
            </ul>
            <p *ngIf="systemStatus.missing_models.length > 0" class="status-error">
              <strong>Missing Models:</strong> {{ systemStatus.missing_models.join(', ') }}
            </p>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Debate Form -->
      <mat-card class="debate-card">
        <mat-card-header>
          <mat-card-title>Start New Debate</mat-card-title>
          <mat-card-subtitle>Enter a question for AI agents to debate</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <form [formGroup]="debateForm" (ngSubmit)="startDebate()">
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Debate Question</mat-label>
              <textarea
                matInput
                formControlName="question"
                placeholder="e.g., Should AI be regulated?"
                rows="3">
              </textarea>
              <mat-error *ngIf="debateForm.get('question')?.hasError('required')">
                Question is required
              </mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>Max Rounds</mat-label>
              <input matInput type="number" formControlName="maxRounds" min="1" max="5">
            </mat-form-field>

            <div class="actions">
              <button 
                mat-raised-button 
                color="primary" 
                type="submit"
                [disabled]="!debateForm.valid || !systemStatus?.system_initialized || isDebating">
                <mat-icon>{{ isDebating ? 'hourglass_empty' : 'play_arrow' }}</mat-icon>
                {{ isDebating ? 'Debating...' : 'Start Debate' }}
              </button>
              
              <!-- Debug Info -->
              <div class="debug-info" style="margin-top: 10px; font-size: 12px; color: #666;">
                <p>Form Valid: {{ debateForm.valid ? '✅' : '❌' }}</p>
                <p>System Initialized: {{ systemStatus?.system_initialized ? '✅' : '❌' }}</p>
                <p>Is Debating: {{ isDebating ? '❌' : '✅' }}</p>
                <p *ngIf="!debateForm.valid">
                  Form Errors: 
                  <span *ngIf="debateForm.get('question')?.errors?.['required']">Question required</span>
                  <span *ngIf="debateForm.get('question')?.errors?.['minlength']">Question too short (min 10 chars)</span>
                </p>
              </div>
            </div>
          </form>
        </mat-card-content>
      </mat-card>

      <!-- Active Debate Progress -->
      <mat-card *ngIf="currentDebate" class="progress-card">
        <mat-card-header>
          <mat-card-title>Debate in Progress</mat-card-title>
          <mat-card-subtitle>{{ currentQuestion }}</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <div class="progress-info">
            <p><strong>Status:</strong> {{ currentDebate.status }}</p>
            <p *ngIf="currentDebate.current_round">
              <strong>Round:</strong> {{ currentDebate.current_round }} / {{ currentDebate.total_rounds }}
            </p>
          </div>
          <mat-progress-bar 
            mode="determinate" 
            [value]="currentDebate.progress * 100">
          </mat-progress-bar>
          <p class="progress-text">{{ (currentDebate.progress * 100).toFixed(0) }}% Complete</p>
        </mat-card-content>
      </mat-card>

      <!-- Results -->
      <mat-card *ngIf="debateResult" class="results-card">
        <mat-card-header>
          <mat-card-title>Debate Results</mat-card-title>
          <mat-card-subtitle>{{ currentQuestion }}</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <mat-tab-group>
            <!-- Summary Tab -->
            <mat-tab label="Summary">
              <div class="tab-content">
                <div class="summary-stats">
                  <p><strong>Status:</strong> {{ debateResult.status }}</p>
                  <p><strong>Total Rounds:</strong> {{ debateResult.total_rounds }}</p>
                  <p><strong>Current Round:</strong> {{ debateResult.current_round }}</p>
                  <p><strong>Progress:</strong> {{ debateResult.progress }}%</p>
                  <p *ngIf="debateResult.duration"><strong>Duration:</strong> {{ debateResult.duration?.toFixed(2) }}s</p>
                </div>
                
                <div class="final-summary" *ngIf="debateResult.final_summary">
                  <h3>Final Summary</h3>
                  <div class="summary-text">{{ debateResult.final_summary }}</div>
                </div>
                
                <div *ngIf="!debateResult.final_summary && debateResult.status === 'in_progress'">
                  <p><em>Debate is still in progress...</em></p>
                </div>
              </div>
            </mat-tab>

            <!-- Rounds Tab -->
            <mat-tab label="Debate Rounds" *ngIf="debateResult.rounds && debateResult.rounds.length > 0">
              <div class="tab-content">
                <mat-accordion>
                  <mat-expansion-panel *ngFor="let round of debateResult.rounds">
                    <mat-expansion-panel-header>
                      <mat-panel-title>
                        Round {{ round.round_number }}
                      </mat-panel-title>
                      <mat-panel-description>
                        Consensus: {{ (round.consensus_analysis.average_similarity * 100).toFixed(1) }}%
                      </mat-panel-description>
                    </mat-expansion-panel-header>
                    
                    <div class="round-content">
                      <!-- Agent Responses -->
                      <div class="responses">
                        <h4>Agent Responses</h4>
                        <div *ngFor="let response of round.responses" class="response">
                          <h5>{{ response.agent_name }}</h5>
                          <p>{{ response.response }}</p>
                          <small>Tokens: {{ response.token_count }} | {{ response.timestamp | date:'short' }}</small>
                        </div>
                      </div>

                      <!-- Orchestrator Feedback -->
                      <div class="feedback" *ngIf="round.orchestrator_feedback">
                        <h4>Orchestrator Feedback</h4>
                        <p>{{ round.orchestrator_feedback }}</p>
                      </div>
                    </div>
                  </mat-expansion-panel>
                </mat-accordion>
              </div>
            </mat-tab>
          </mat-tab-group>

          <div class="actions">
            <button mat-raised-button (click)="clearResults()">
              <mat-icon>clear</mat-icon>
              Clear Results
            </button>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .container {
      max-width: 1200px;
      margin: 20px auto;
      padding: 0 20px;
    }

    .spacer {
      flex: 1 1 auto;
    }

    mat-card {
      margin: 20px 0;
    }

    .full-width {
      width: 100%;
    }

    .actions {
      margin-top: 20px;
      display: flex;
      gap: 10px;
    }

    .status-ok {
      color: #4caf50;
      font-weight: bold;
    }

    .status-error {
      color: #f44336;
      font-weight: bold;
    }

    .progress-info {
      margin-bottom: 15px;
    }

    .progress-text {
      text-align: center;
      margin-top: 8px;
      font-size: 14px;
      color: #666;
    }

    .tab-content {
      padding: 20px 0;
    }

    .summary-stats {
      background: #f5f5f5;
      padding: 15px;
      border-radius: 8px;
      margin-bottom: 20px;
    }

    .final-summary {
      margin-top: 20px;
    }

    .summary-text {
      background: #fff;
      padding: 15px;
      border-left: 4px solid #2196f3;
      border-radius: 4px;
      white-space: pre-wrap;
      line-height: 1.6;
    }

    .round-content {
      padding: 15px 0;
    }

    .responses {
      margin-bottom: 25px;
    }

    .response {
      background: #f9f9f9;
      padding: 15px;
      margin: 10px 0;
      border-radius: 8px;
      border-left: 4px solid #4caf50;
    }

    .response h5 {
      margin: 0 0 10px 0;
      color: #333;
      font-weight: 500;
    }

    .response p {
      margin: 0 0 8px 0;
      line-height: 1.5;
    }

    .response small {
      color: #666;
      font-size: 12px;
    }

    .feedback {
      background: #e3f2fd;
      padding: 15px;
      border-radius: 8px;
      border-left: 4px solid #2196f3;
    }

    .feedback h4 {
      margin: 0 0 10px 0;
      color: #1976d2;
    }

    .feedback p {
      margin: 0;
      line-height: 1.5;
    }

    mat-expansion-panel {
      margin: 8px 0;
    }
  `]
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'LLM Debate System';
  
  debateForm: FormGroup;
  systemStatus: SystemStatus | null = null;
  currentDebate: DebateStatus | null = null;
  currentQuestion: string = '';
  debateResult: any = null;
  isDebating = false;
  
  private apiUrl = 'http://localhost:8000/api';
  private pollSubscription?: Subscription;

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private snackBar: MatSnackBar
  ) {
    this.debateForm = this.fb.group({
      question: ['', [Validators.required, Validators.minLength(10)]],
      maxRounds: [3, [Validators.min(1), Validators.max(5)]]
    });
  }

  ngOnInit() {
    this.loadSystemStatus();
  }

  ngOnDestroy() {
    if (this.pollSubscription) {
      this.pollSubscription.unsubscribe();
    }
  }

  loadSystemStatus() {
    this.http.get<SystemStatus>(`${this.apiUrl}/status`).subscribe({
      next: (status) => {
        this.systemStatus = status;
        if (!status.system_initialized) {
          this.snackBar.open('System not initialized. Please check the backend.', 'OK', {
            duration: 5000
          });
        }
      },
      error: (error) => {
        console.error('Failed to load system status:', error);
        this.snackBar.open('Failed to connect to backend API', 'OK', {
          duration: 5000
        });
      }
    });
  }

  startDebate() {
    if (!this.debateForm.valid || !this.systemStatus?.system_initialized) {
      return;
    }

    const request: DebateRequest = {
      question: this.debateForm.value.question,
      max_rounds: this.debateForm.value.maxRounds
    };

    this.isDebating = true;
    this.currentDebate = null;
    this.debateResult = null;
    this.currentQuestion = this.debateForm.value.question;

    // Show immediate feedback
    this.snackBar.open('Starting debate...', 'OK', { duration: 2000 });

    this.http.post<DebateResponse>(`${this.apiUrl}/debate/start`, request).subscribe({
      next: (response) => {
        this.snackBar.open('Debate started successfully!', 'OK', { duration: 3000 });
        this.startPollingDebateStatus(response.debate_id);
      },
      error: (error) => {
        console.error('Failed to start debate:', error);
        this.snackBar.open('Failed to start debate', 'OK', { duration: 5000 });
        this.isDebating = false;
      }
    });
  }

  startPollingDebateStatus(debateId: string) {
    // Poll more frequently to catch fast debates (every 500ms)
    this.pollSubscription = interval(500).pipe(
      switchMap(() => this.http.get<DebateStatus>(`${this.apiUrl}/debate/${debateId}/status`)),
      takeWhile(status => status.status === 'in_progress' || status.status === 'starting', true)
    ).subscribe({
      next: (status) => {
        this.currentDebate = status;
        
        // Keep isDebating true while status is in_progress
        if (status.status === 'in_progress') {
          this.isDebating = true;
        } else {
          // Handle all completion statuses
          const completedStatuses = ['consensus_reached', 'max_rounds_exceeded', 'error'];
          if (completedStatuses.includes(status.status)) {
            // Add a minimum delay for better UX (so users see that something happened)
            setTimeout(() => {
              // For completed debates, fetch full results
              this.fetchFullDebateResults(debateId, status);
              this.currentDebate = null;
              this.isDebating = false;
              
              // Show appropriate message based on completion status
              if (status.status === 'consensus_reached') {
                this.snackBar.open('Debate completed - Consensus reached!', 'OK', { duration: 3000 });
              } else if (status.status === 'max_rounds_exceeded') {
                this.snackBar.open('Debate completed - Maximum rounds reached!', 'OK', { duration: 3000 });
              } else if (status.status === 'error') {
                this.snackBar.open('Debate failed with error', 'OK', { duration: 5000 });
              }
            }, 3000); // Minimum 3 second delay for UX
          }
        }
      },
      error: (error) => {
        console.error('Failed to get debate status:', error);
        this.isDebating = false;
        this.currentDebate = null;
      }
    });
  }

  fetchFullDebateResults(debateId: string, statusInfo: DebateStatus) {
    this.http.get(`${this.apiUrl.replace('/api', '')}/debates/${debateId}/full`).subscribe({
      next: (fullResult: any) => {
        // Merge status info with full results
        this.debateResult = {
          ...fullResult,
          status: statusInfo.status,
          progress: statusInfo.progress || 100
        };
      },
      error: (error) => {
        console.error('Failed to fetch full debate results:', error);
        // Fallback to just the status info
        this.debateResult = statusInfo;
      }
    });
  }

  clearResults() {
    this.debateResult = null;
    this.currentQuestion = '';
    this.debateForm.reset({
      question: '',
      maxRounds: 3
    });
  }
}
