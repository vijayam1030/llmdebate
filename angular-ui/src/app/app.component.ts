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
import { FormsModule } from '@angular/forms';

interface SystemStatus {
  initialized: boolean;
  models_loaded: string[];
  config: any;
  ngrok_url?: string;
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
    FormsModule,
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
    <!-- SHARABLE APP LINK BAR (NEW UI) -->
    <div class="ngrok-bar" style="background:#e3f2fd;padding:8px 16px;display:flex;align-items:center;gap:12px;">
      <mat-icon color="primary">link</mat-icon>
      <span style="font-weight:600;">Sharable App Link:</span>
      <input
        matInput
        [value]="sharableUrl"
        placeholder="ngrok/public URL or localhost will appear here"
        style="min-width:260px;max-width:400px;flex:1;"
        readonly
      />
      <button mat-stroked-button color="primary" (click)="copySharableUrl()" [disabled]="!sharableUrl">
        <mat-icon>content_copy</mat-icon> Copy
      </button>
      <span *ngIf="sharableUrl" style="margin-left:8px;">
        <a [href]="sharableUrl" target="_blank" style="color:#1976d2;text-decoration:none;">
          <mat-icon style="font-size:16px;width:16px;height:16px;">open_in_new</mat-icon>
          Open
        </a>
      </span>
      <span *ngIf="systemStatus?.ngrok_url" style="margin-left:8px;color:#4caf50;font-size:12px;">
        ✓ ngrok Detected
      </span>
    </div>
    <!-- Main Container -->
    <div class="app-container">
      <!-- Header -->
      <div class="header">
        <div class="header-content">
          <h1 class="main-title">
            <mat-icon class="title-icon">forum</mat-icon>
            LLM Debate System
          </h1>
          <p class="subtitle">Intelligent Multi-Agent Debate Platform</p>
        </div>
      </div>

      <!-- Main Content -->
      <div class="main-content">
        <!-- System Status Card -->
        <mat-card class="status-card" [ngClass]="{'system-ready': systemStatus?.initialized, 'system-loading': !systemStatus?.initialized}">
          <mat-card-content>
            <div class="status-header">
              <mat-icon [ngClass]="{'status-ready': systemStatus?.initialized, 'status-loading': !systemStatus?.initialized}">
                {{ systemStatus?.initialized ? 'check_circle' : 'hourglass_empty' }}
              </mat-icon>
              <h3>System Status</h3>
            </div>
            <div class="status-details">
              <div class="status-item">
                <span class="label">Status:</span>
                <span class="value" [ngClass]="{'ready': systemStatus?.initialized, 'loading': !systemStatus?.initialized}">
                  {{ systemStatus?.initialized ? 'Ready' : 'Initializing...' }}
                </span>
              </div>
              <div class="status-item" *ngIf="systemStatus?.models_loaded?.length">
                <span class="label">Models Loaded:</span>
                <span class="value">{{ systemStatus?.models_loaded?.length }}</span>
              </div>
              <div class="models-list" *ngIf="systemStatus?.models_loaded?.length">
                <mat-chip-set>
                  <mat-chip *ngFor="let model of systemStatus?.models_loaded">{{ model }}</mat-chip>
                </mat-chip-set>
              </div>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- Debate Input Section -->
        <mat-card class="input-card" *ngIf="!currentDebate && !debateResult">
          <mat-card-header>
            <mat-card-title>
              <mat-icon>add_comment</mat-icon>
              Start New Debate
            </mat-card-title>
            <mat-card-subtitle>Enter your debate question and configure settings</mat-card-subtitle>
          </mat-card-header>
          <mat-card-content>
            <form [formGroup]="debateForm" (ngSubmit)="startDebate()" class="debate-form">
              <!-- Question Input -->
              <div class="form-section">
                <label class="section-label">Debate Question</label>
                <mat-form-field appearance="outline" class="full-width">
                  <mat-label>What would you like to debate?</mat-label>
                  <textarea
                    matInput
                    formControlName="question"
                    placeholder="e.g., Should artificial intelligence be regulated by governments?"
                    rows="4"
                    class="question-input">
                  </textarea>
                  <mat-hint>Minimum 10 characters required</mat-hint>
                  <mat-error *ngIf="debateForm.get('question')?.hasError('required')">
                    Question is required
                  </mat-error>
                  <mat-error *ngIf="debateForm.get('question')?.hasError('minlength')">
                    Question must be at least 10 characters long
                  </mat-error>
                </mat-form-field>
              </div>

              <!-- Settings Section -->
              <div class="form-section">
                <label class="section-label">Debate Settings</label>
                <div class="settings-grid">
                  <mat-form-field appearance="outline">
                    <mat-label>Maximum Rounds</mat-label>
                    <mat-select formControlName="maxRounds">
                      <mat-option value="1">1 Round (Quick)</mat-option>
                      <mat-option value="2">2 Rounds (Standard)</mat-option>
                      <mat-option value="3">3 Rounds (Thorough)</mat-option>
                      <mat-option value="4">4 Rounds (Deep)</mat-option>
                      <mat-option value="5">5 Rounds (Comprehensive)</mat-option>
                    </mat-select>
                    <mat-hint>More rounds = deeper analysis</mat-hint>
                  </mat-form-field>
                </div>
              </div>

              <!-- Start Button -->
              <div class="form-actions">
                <button 
                  mat-raised-button 
                  color="primary" 
                  type="submit"
                  class="start-button"
                  [disabled]="!debateForm.valid || !systemStatus?.initialized || isDebating">
                  <mat-icon>play_arrow</mat-icon>
                  <span>Start Debate</span>
                </button>
                
                <!-- Validation Info -->
                <div class="validation-info" *ngIf="!debateForm.valid || !systemStatus?.initialized">
                  <mat-icon class="warning-icon">info</mat-icon>
                  <span *ngIf="!systemStatus?.initialized">Please wait for system initialization</span>
                  <span *ngIf="systemStatus?.initialized && !debateForm.valid">Please complete all required fields</span>
                </div>
              </div>
            </form>
          </mat-card-content>
        </mat-card>

        <!-- Active Debate Progress -->
        <mat-card *ngIf="currentDebate" class="progress-card">
          <mat-card-header>
            <mat-card-title>
              <mat-icon class="animated-icon">psychology</mat-icon>
              Debate in Progress
            </mat-card-title>
            <mat-card-subtitle>{{ currentQuestion }}</mat-card-subtitle>
          </mat-card-header>
          <mat-card-content>
            <div class="progress-section">
              <!-- Status Info -->
              <div class="progress-info">
                <div class="info-item">
                  <span class="label">Status:</span>
                  <span class="value status-{{ currentDebate.status }}">
                    {{ currentDebate.status | titlecase }}
                  </span>
                </div>
                <div class="info-item" *ngIf="currentDebate?.current_round">
                  <span class="label">Round:</span>
                  <span class="value">{{ currentDebate.current_round }} / {{ currentDebate.total_rounds }}</span>
                </div>
                <div class="info-item">
                  <span class="label">Progress:</span>
                  <span class="value">{{ (currentDebate.progress * 100).toFixed(0) }}%</span>
                </div>
              </div>

              <!-- Progress Bar -->
              <div class="progress-bar-section">
                <mat-progress-bar 
                  mode="determinate" 
                  [value]="currentDebate.progress * 100"
                  class="custom-progress-bar">
                </mat-progress-bar>
                <div class="progress-text">
                  <span class="progress-label">Processing...</span>
                  <span class="progress-percentage">{{ (currentDebate.progress * 100).toFixed(0) }}%</span>
                </div>
              </div>

              <!-- Current Activity -->
              <div class="activity-indicator">
                <mat-icon class="spinning">sync</mat-icon>
                <span>AI agents are analyzing and debating your question</span>
              </div>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- Results Section -->
        <mat-card *ngIf="debateResult" class="results-card">
          <mat-card-header>
            <mat-card-title>
              <mat-icon>emoji_events</mat-icon>
              Debate Results
            </mat-card-title>
            <mat-card-subtitle>{{ debateResult?.question }}</mat-card-subtitle>
          </mat-card-header>
          <mat-card-content>
            <!-- Results Summary -->
            <div class="results-summary">
              <div class="summary-grid">
                <div class="summary-item">
                  <mat-icon>flag</mat-icon>
                  <div>
                    <span class="summary-label">Final Status</span>
                    <span class="summary-value status-{{ debateResult?.final_status }}">
                      {{ debateResult?.final_status | titlecase }}
                    </span>
                  </div>
                </div>
                <div class="summary-item">
                  <mat-icon>repeat</mat-icon>
                  <div>
                    <span class="summary-label">Total Rounds</span>
                    <span class="summary-value">{{ debateResult?.total_rounds }}</span>
                  </div>
                </div>
                <div class="summary-item">
                  <mat-icon>{{ debateResult?.consensus_reached ? 'check_circle' : 'radio_button_unchecked' }}</mat-icon>
                  <div>
                    <span class="summary-label">Consensus</span>
                    <span class="summary-value" [ngClass]="{'consensus-yes': debateResult?.consensus_reached, 'consensus-no': !debateResult?.consensus_reached}">
                      {{ debateResult?.consensus_reached ? 'Reached' : 'Not Reached' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Detailed Results -->
            <mat-tab-group class="results-tabs" animationDuration="300ms">
              <!-- Summary Tab -->
              <mat-tab>
                <ng-template mat-tab-label>
                  <mat-icon>summarize</mat-icon>
                  Summary
                </ng-template>
                <div class="tab-content summary-tab">
                  <div class="final-summary-card">
                    <h3>Final Summary</h3>
                    <div class="summary-content">
                      {{ debateResult?.final_summary }}
                    </div>
                  </div>
                </div>
              </mat-tab>

              <!-- Rounds Tab -->
              <mat-tab>
                <ng-template mat-tab-label>
                  <mat-icon>forum</mat-icon>
                  Debate Rounds ({{ debateResult?.rounds?.length || 0 }})
                </ng-template>
                <div class="tab-content rounds-tab">
                  <mat-accordion class="rounds-accordion">
                    <mat-expansion-panel *ngFor="let round of debateResult?.rounds; let i = index" class="round-panel">
                      <mat-expansion-panel-header>
                        <mat-panel-title>
                          <mat-icon>chat_bubble</mat-icon>
                          Round {{ round.round_number }}
                        </mat-panel-title>
                        <mat-panel-description>
                          <span class="consensus-indicator">
                            Consensus: {{ (round.consensus_analysis?.average_similarity * 100).toFixed(1) }}%
                          </span>
                          <mat-icon class="consensus-icon" [ngClass]="{'high-consensus': round.consensus_analysis?.average_similarity > 0.7, 'medium-consensus': round.consensus_analysis?.average_similarity > 0.4, 'low-consensus': round.consensus_analysis?.average_similarity <= 0.4}">
                            {{ round.consensus_analysis?.consensus_reached ? 'check_circle' : 'radio_button_unchecked' }}
                          </mat-icon>
                        </mat-panel-description>
                      </mat-expansion-panel-header>
                      
                      <div class="round-content">
                        <!-- Agent Responses -->
                        <div class="responses-section">
                          <h4>Agent Responses</h4>
                          <div class="responses-grid">
                            <mat-card *ngFor="let response of round.responses; let j = index" class="response-card">
                              <mat-card-header>
                                <mat-card-title>{{ response.agent_name }}</mat-card-title>
                                <mat-card-subtitle>{{ response.token_count }} tokens</mat-card-subtitle>
                              </mat-card-header>
                              <mat-card-content>
                                <div class="response-text">{{ response.response }}</div>
                              </mat-card-content>
                            </mat-card>
                          </div>
                        </div>

                        <!-- Orchestrator Feedback -->
                        <div class="feedback-section" *ngIf="round.orchestrator_feedback">
                          <h4>Orchestrator Analysis</h4>
                          <mat-card class="feedback-card">
                            <mat-card-content>
                              <div class="feedback-text">{{ round.orchestrator_feedback }}</div>
                            </mat-card-content>
                          </mat-card>
                        </div>
                      </div>
                    </mat-expansion-panel>
                  </mat-accordion>
                </div>
              </mat-tab>
            </mat-tab-group>

            <!-- Action Buttons -->
            <div class="results-actions">
              <button mat-raised-button color="primary" (click)="clearResults()" class="action-button">
                <mat-icon>refresh</mat-icon>
                Start New Debate
              </button>
            </div>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit, OnDestroy {
  ngrokUrl: string = '';
  sharableUrl: string = '';
  systemStatus: SystemStatus | null = null;
  debateForm: FormGroup;
  isDebating = false;
  currentDebate: DebateStatus | null = null;
  debateResult: any = null;
  currentQuestion = '';
  private pollSubscription?: Subscription;
  private apiUrl = this.getApiUrl();

  private getApiUrl(): string {
    const hostname = window.location.hostname;
    const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';
    
    if (isLocalhost) {
      console.log('🏠 Running on localhost - using local API');
      return 'http://localhost:8000/api';
    } else {
      console.log('🌐 Running on external URL - using same origin API');
      return `${window.location.origin}/api`;
    }
  }

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private snackBar: MatSnackBar
  ) {
    this.debateForm = this.fb.group({
      question: ['', [Validators.required, Validators.minLength(10)]],
      maxRounds: [3, [Validators.required, Validators.min(1), Validators.max(5)]]
    });
  }

  ngOnInit() {
    this.checkSystemStatus();
    // Poll system status every 10 seconds until initialized
    const statusInterval = interval(10000).pipe(
      takeWhile(() => !this.systemStatus?.initialized, true)
    ).subscribe(() => {
      this.checkSystemStatus();
    });

    // Clean up after 2 minutes
    setTimeout(() => statusInterval.unsubscribe(), 120000);

    // Set initial sharableUrl to window location
    this.sharableUrl = window.location.origin;
  }

  ngOnDestroy() {
    if (this.pollSubscription) {
      this.pollSubscription.unsubscribe();
    }
  }

  checkSystemStatus() {
    console.log('🔍 Checking system status...');
    console.log('📡 API URL:', this.apiUrl);
    console.log('🌐 Window location:', window.location.href);
    console.log('🏠 Window hostname:', window.location.hostname);
    
    this.http.get<SystemStatus>(`${this.apiUrl}/status`).subscribe({
      next: (status) => {
        console.log('✅ Status response received:', status);
        console.log('🏃 System initialized:', status.initialized);
        console.log('🔗 Ngrok URL from backend:', status.ngrok_url);
        
        this.systemStatus = status;
        // Auto-populate ngrok URL if available from backend
        if (status.ngrok_url) {
          this.ngrokUrl = status.ngrok_url;
          this.sharableUrl = status.ngrok_url;
          console.log('✨ Updated sharable URL to:', this.sharableUrl);
        } else {
          this.sharableUrl = window.location.origin;
          console.log('🏠 Using window origin as sharable URL:', this.sharableUrl);
        }
      },
      error: (error) => {
        console.error('❌ Failed to get system status:', error);
        console.error('🔍 Error details:', error.message);
        console.error('🌐 Request URL:', `${this.apiUrl}/status`);
        
        this.systemStatus = {
          initialized: false,
          models_loaded: [],
          config: { error: 'Failed to connect to server' }
        };
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

  copySharableUrl() {
    if (this.sharableUrl) {
      navigator.clipboard.writeText(this.sharableUrl);
      this.snackBar.open('App link copied to clipboard!', 'Close', { duration: 2000 });
    }
  }
}
