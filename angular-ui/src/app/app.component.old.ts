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
  initialized: boolean;
  models_loaded: string[];
  config: any;
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
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatToolbarModule,
    MatCardModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatProgressBarModule,
    MatSnackBarModule,
    MatTabsModule,
    MatExpansionModule,
    MatIconModule,
    MatChipsModule
  ],
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
              <span [ngClass]="systemStatus.initialized ? 'status-ok' : 'status-error'">
                {{ systemStatus.initialized ? 'Ready' : 'Not Initialized' }}
              </span>
            </p>
            <p><strong>Models Loaded:</strong> {{ systemStatus.models_loaded.length || 0 }}</p>
            <div *ngIf="systemStatus.config">
              <p><strong>Max Rounds:</strong> {{ systemStatus.config.max_rounds }}</p>
              <p><strong>Orchestrator:</strong> {{ systemStatus.config.orchestrator_model }}</p>
            </div>
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
                [disabled]="!debateForm.valid || !systemStatus?.initialized || isDebating">
                <mat-icon>play_arrow</mat-icon>
                Start Debate
              </button>
              
              <!-- Debug Info -->
              <div class="debug-info" style="margin-top: 10px; font-size: 12px; color: #666;">
                <p>Form Valid: {{ debateForm.valid ? '✅' : '❌' }}</p>
                <p>System Initialized: {{ systemStatus?.initialized ? '✅' : '❌' }}</p>
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
          <mat-card-subtitle>{{ debateResult.question }}</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <mat-tab-group>
            <!-- Summary Tab -->
            <mat-tab label="Summary">
              <div class="tab-content">
                <div class="summary-stats">
                  <p><strong>Status:</strong> {{ debateResult.final_status }}</p>
                  <p><strong>Total Rounds:</strong> {{ debateResult.total_rounds }}</p>
                  <p><strong>Consensus Reached:</strong> {{ debateResult.consensus_reached ? 'Yes' : 'No' }}</p>
                </div>
                
                <div class="final-summary">
                  <h3>Final Summary</h3>
                  <div class="summary-text">{{ debateResult.final_summary }}</div>
                </div>
              </div>
            </mat-tab>

            <!-- Rounds Tab -->
            <mat-tab label="Debate Rounds">
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
        if (!status.initialized) {
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
    if (!this.debateForm.valid || !this.systemStatus?.initialized) {
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
    this.pollSubscription = interval(2000).pipe(
      switchMap(() => this.http.get<DebateStatus>(`${this.apiUrl}/debate/${debateId}/status`)),
      takeWhile(status => status.status === 'running' || status.status === 'starting', true)
    ).subscribe({
      next: (status) => {
        this.currentDebate = status;
        
        if (status.status === 'completed') {
          this.debateResult = status.result;
          this.currentDebate = null;
          this.isDebating = false;
          this.snackBar.open('Debate completed!', 'OK', { duration: 3000 });
        } else if (status.status === 'failed') {
          this.currentDebate = null;
          this.isDebating = false;
          this.snackBar.open('Debate failed', 'OK', { duration: 5000 });
        }
      },
      error: (error) => {
        console.error('Failed to get debate status:', error);
        this.isDebating = false;
        this.currentDebate = null;
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
