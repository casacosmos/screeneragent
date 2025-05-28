/**
 * Environmental Screening Platform
 * Advanced Frontend Application with Full Integration
 */

class EnvironmentalScreeningApp {
    constructor() {
        this.currentSection = 'dashboard';
        this.projects = [];
        this.reports = [];
        this.activeScreenings = new Map();
        this.map = null;
        this.selectedCoordinates = null;
        
        // Batch screening properties
        this.batchItems = [];
        this.currentBatch = null;
        this.batchPollingInterval = null;
        this.batchProcessingMode = 'sequential';
        
        this.currentScreening = null;
        this.progressPollingInterval = null;
        this.selectedLocation = null;
        
        // Flag to track if screening is in progress
        this.screeningInProgress = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboardData();
        this.initializeMap();
        this.setupFormValidation();
        this.startPeriodicUpdates();
        
        // Load initial data
        this.loadProjects();
        this.loadReports();
        
        // Show dashboard by default
        this.showSection('dashboard');

        // Initialize batch screening
        this.initializeBatchScreening();
    }

    initializeBatchScreening() {
        // Initialize batch counter
        this.updateBatchCounter();
        
        // Set up processing mode change listener
        const processingModeSelect = document.getElementById('batchProcessingMode');
        if (processingModeSelect) {
            processingModeSelect.addEventListener('change', () => this.updateProcessingModeUI());
        }
        
        // Initialize UI state
        this.updateProcessingModeUI();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const section = e.currentTarget.dataset.section;
                this.showSection(section);
            });
        });

        // Screening form
        const screeningForm = document.getElementById('screeningForm');
        if (screeningForm) {
            screeningForm.addEventListener('submit', this.handleScreeningSubmit.bind(this));
        }

        // Location tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.currentTarget.dataset.tab;
                this.switchLocationTab(tab);
            });
        });

        // Search and filter
        const projectSearch = document.getElementById('projectSearch');
        if (projectSearch) {
            projectSearch.addEventListener('input', this.filterProjects.bind(this));
        }

        const reportSearch = document.getElementById('reportSearch');
        if (reportSearch) {
            reportSearch.addEventListener('input', this.filterReports.bind(this));
        }

        // Modal close
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                // Don't close progress modal if screening is in progress
                if (this.screeningInProgress && e.target.id === 'progressModal') {
                    return;
                }
                this.closeModal();
            }
        });

        // Toast close
        document.addEventListener('click', (e) => {
            if (e.target.closest('.toast-close')) {
                this.hideToast();
            }
        });

        // Cancel screening
        const cancelBtn = document.getElementById('cancelScreening');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', this.cancelCurrentScreening.bind(this));
        }
    }

    showSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        // Update sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionName).classList.add('active');

        this.currentSection = sectionName;

        // Load section-specific data
        switch (sectionName) {
            case 'dashboard':
                this.updateDashboardStats();
                break;
            case 'projects':
                this.loadProjects();
                break;
            case 'reports':
                this.loadReports();
                break;
        }
    }

    // Dashboard Management
    async loadDashboardData() {
        try {
            const response = await fetch('/api/dashboard');
            if (response.ok) {
                const data = await response.json();
                this.updateDashboardStats(data);
                this.updateRecentActivity(data.recent_activity || []);
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showToast('error', 'Failed to load dashboard data');
        }
    }

    updateDashboardStats(data = {}) {
        document.getElementById('totalProjects').textContent = data.total_projects || this.projects.length;
        document.getElementById('reportsGenerated').textContent = data.reports_generated || this.reports.length;
        document.getElementById('riskAreas').textContent = data.risk_areas || 0;
        document.getElementById('compliantProjects').textContent = data.compliant_projects || 0;
    }

    updateRecentActivity(activities) {
        const activityList = document.getElementById('recentActivity');
        activityList.innerHTML = '';

        if (activities.length === 0) {
            activityList.innerHTML = '<p style="color: var(--text-secondary); font-style: italic;">No recent activity</p>';
            return;
        }

        activities.forEach(activity => {
            const activityItem = document.createElement('div');
            activityItem.className = 'activity-item';
            activityItem.innerHTML = `
                <div class="activity-time">${this.formatTime(activity.timestamp)}</div>
                <div class="activity-description">${activity.description}</div>
            `;
            activityList.appendChild(activityItem);
        });
    }

    // Screening Form Management
    switchLocationTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Initialize map if map tab is selected
        if (tabName === 'map' && !this.map) {
            setTimeout(() => this.initializeMap(), 100);
        }
    }

    initializeMap() {
        const mapContainer = document.getElementById('locationMap');
        if (!mapContainer || this.map) return;

        // Initialize Leaflet map
        this.map = L.map('locationMap').setView([18.4155, -66.0663], 9); // Puerto Rico center

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);

        // Add click handler
        this.map.on('click', (e) => {
            const { lat, lng } = e.latlng;
            this.selectMapLocation(lat, lng);
        });
    }

    selectMapLocation(lat, lng) {
        // Update coordinates in form
        document.getElementById('latitude').value = lat.toFixed(6);
        document.getElementById('longitude').value = lng.toFixed(6);

        // Clear existing markers
        this.map.eachLayer(layer => {
            if (layer instanceof L.Marker) {
                this.map.removeLayer(layer);
            }
        });

        // Add new marker
        const marker = L.marker([lat, lng]).addTo(this.map);
        marker.bindPopup(`Selected Location<br>Lat: ${lat.toFixed(6)}<br>Lng: ${lng.toFixed(6)}`).openPopup();

        this.selectedCoordinates = [lng, lat]; // Store as [longitude, latitude]
        this.showToast('success', `Location selected: ${lat.toFixed(4)}, ${lng.toFixed(4)}`);
    }

    setupFormValidation() {
        const form = document.getElementById('screeningForm');
        if (!form) return;

        // Real-time validation
        const requiredFields = form.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            field.addEventListener('blur', () => this.validateField(field));
            field.addEventListener('input', () => this.clearFieldError(field));
        });

        // Cadastral format validation
        const cadastralInput = document.getElementById('cadastralNumber');
        if (cadastralInput) {
            cadastralInput.addEventListener('input', (e) => {
                let value = e.target.value.replace(/[^\d]/g, '');
                if (value.length >= 3) value = value.slice(0, 3) + '-' + value.slice(3);
                if (value.length >= 7) value = value.slice(0, 7) + '-' + value.slice(7);
                if (value.length >= 11) value = value.slice(0, 11) + '-' + value.slice(11, 13);
                e.target.value = value;
            });
        }
    }

    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';

        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        } else if (field.type === 'email' && value && !this.isValidEmail(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        } else if (field.pattern && value && !new RegExp(field.pattern).test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid format';
        }

        this.setFieldValidation(field, isValid, errorMessage);
        return isValid;
    }

    setFieldValidation(field, isValid, errorMessage = '') {
        const group = field.closest('.form-group');
        if (!group) return;

        // Remove existing error
        const existingError = group.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }

        // Update field styling
        field.style.borderColor = isValid ? '' : 'var(--danger-color)';

        // Add error message if invalid
        if (!isValid && errorMessage) {
            const errorElement = document.createElement('div');
            errorElement.className = 'field-error';
            errorElement.style.color = 'var(--danger-color)';
            errorElement.style.fontSize = '0.8rem';
            errorElement.style.marginTop = '0.25rem';
            errorElement.textContent = errorMessage;
            group.appendChild(errorElement);
        }
    }

    clearFieldError(field) {
        field.style.borderColor = '';
        const group = field.closest('.form-group');
        const error = group?.querySelector('.field-error');
        if (error) {
            error.remove();
        }
    }

    // Screening Submission
    async handleScreeningSubmit(e) {
        e.preventDefault();

        // Validate form
        if (!this.validateForm()) {
            this.showToast('error', 'Please fix form errors before submitting');
            return;
        }

        // Collect form data
        const formData = this.collectFormData();
        
        // Validate location data
        if (!this.hasValidLocation(formData)) {
            this.showToast('error', 'Please specify a location using cadastral number or coordinates');
            return;
        }

        // Show progress modal
        this.showProgressModal();

        try {
            // Start screening
            const response = await fetch('/api/environmental-screening', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            // Backend returns ScreeningResponse with screening_id, status, message
            if (result.screening_id && result.status === 'pending') {
                // Start monitoring progress
                this.monitorScreeningProgress(result.screening_id);
                this.showToast('success', result.message || 'Environmental screening started successfully');
            } else {
                throw new Error(result.message || 'Failed to start screening');
            }

        } catch (error) {
            console.error('Screening submission error:', error);
            this.closeModal();
            this.showToast('error', `Failed to start screening: ${error.message}`);
        }
    }

    collectFormData() {
        const form = document.getElementById('screeningForm');
        const formData = new FormData(form);
        
        // Convert to object with proper structure matching backend ScreeningRequest model
        const data = {
            projectName: formData.get('projectName') || document.getElementById('projectName').value,
            locationName: document.getElementById('locationName').value || null,
            
            // Location data
            cadastralNumber: document.getElementById('cadastralNumber').value || null,
            coordinates: this.getCoordinatesObject(), // Changed to return object format
            
            // Analysis options
            analyses: Array.from(document.querySelectorAll('input[name="analyses"]:checked')).map(cb => cb.value),
            
            // Report options
            includeComprehensiveReport: document.getElementById('includeComprehensiveReport').checked,
            includePdf: document.getElementById('includePdf').checked,
            useLlmEnhancement: document.getElementById('useLlmEnhancement').checked
        };

        return data;
    }

    getCoordinates() {
        const lat = document.getElementById('latitude').value;
        const lng = document.getElementById('longitude').value;
        
        if (lat && lng) {
            return [parseFloat(lng), parseFloat(lat)]; // [longitude, latitude]
        }
        
        return this.selectedCoordinates;
    }

    getCoordinatesObject() {
        const lat = document.getElementById('latitude').value;
        const lng = document.getElementById('longitude').value;
        
        if (lat && lng) {
            return {
                latitude: parseFloat(lat),
                longitude: parseFloat(lng)
            };
        }
        
        if (this.selectedCoordinates && this.selectedCoordinates.length === 2) {
            return {
                latitude: this.selectedCoordinates[1],
                longitude: this.selectedCoordinates[0]
            };
        }
        
        return null;
    }

    hasValidLocation(formData) {
        return formData.cadastralNumber || 
               (formData.coordinates && formData.coordinates.latitude && formData.coordinates.longitude);
    }

    validateForm() {
        const form = document.getElementById('screeningForm');
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        return isValid;
    }

    // Progress Monitoring
    showProgressModal() {
        const modal = document.getElementById('progressModal');
        modal.classList.add('active');
        
        // Set flag to prevent modal dismissal
        this.screeningInProgress = true;
        
        // Reset progress
        this.updateProgress(0, 'Initializing screening...');
        this.resetProgressSteps();
        this.clearProgressLog();
    }

    async monitorScreeningProgress(screeningId) {
        const maxAttempts = 120; // 10 minutes max
        let attempts = 0;
        
        const checkProgress = async () => {
            try {
                const response = await fetch(`/api/environmental-screening/${screeningId}/status`);
                const data = await response.json();
                
                this.updateProgressFromStatus(data);
                
                if (data.status === 'completed') {
                    await this.handleScreeningComplete(screeningId);
                    return;
                } else if (data.status === 'failed') {
                    this.handleScreeningFailed(data.error);
                    return;
                }
                
                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(checkProgress, 5000); // Check every 5 seconds
                } else {
                    this.handleScreeningTimeout();
                }
                
            } catch (error) {
                console.error('Progress monitoring error:', error);
                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(checkProgress, 5000);
                } else {
                    this.handleScreeningError(error);
                }
            }
        };
        
        // Start monitoring
        setTimeout(checkProgress, 2000); // Wait 2 seconds before first check
    }

    updateProgressFromStatus(statusData) {
        const progress = statusData.progress || 0;
        const currentStep = statusData.current_step || 'setup';
        const message = statusData.message || 'Processing...';
        
        this.updateProgress(progress, message);
        this.updateProgressStep(currentStep);
        
        if (statusData.log_entries) {
            statusData.log_entries.forEach(entry => {
                this.addProgressLogEntry(entry.timestamp, entry.message);
            });
        }
    }

    updateProgress(percentage, message) {
        document.getElementById('progressFill').style.width = `${percentage}%`;
        document.getElementById('progressPercentage').textContent = `${Math.round(percentage)}%`;
        document.getElementById('progressStatus').textContent = message;
    }

    updateProgressStep(stepName) {
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active', 'completed');
        });
        
        const stepElement = document.querySelector(`[data-step="${stepName}"]`);
        if (stepElement) {
            stepElement.classList.add('active');
            
            // Mark previous steps as completed
            const steps = ['setup', 'property', 'environmental', 'reports'];
            const currentIndex = steps.indexOf(stepName);
            for (let i = 0; i < currentIndex; i++) {
                const prevStep = document.querySelector(`[data-step="${steps[i]}"]`);
                if (prevStep) {
                    prevStep.classList.add('completed');
                }
            }
        }
    }

    resetProgressSteps() {
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active', 'completed');
        });
    }

    addProgressLogEntry(timestamp, message) {
        const log = document.getElementById('progressLog');
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.innerHTML = `
            <span class="log-timestamp">${this.formatTime(timestamp)}</span>
            <span class="log-message">${message}</span>
        `;
        log.appendChild(entry);
        log.scrollTop = log.scrollHeight;
    }

    clearProgressLog() {
        document.getElementById('progressLog').innerHTML = '';
    }

    async handleScreeningComplete(screeningId) {
        this.updateProgress(100, 'Screening completed successfully!');
        this.updateProgressStep('reports');
        
        // Clear the screening in progress flag
        this.screeningInProgress = false;
        
        // Wait a moment to show completion
        setTimeout(async () => {
            this.closeModal();
            
            // Refresh data
            await this.loadProjects();
            await this.loadReports();
            
            // Show success message
            this.showToast('success', 'Environmental screening completed! Check the reports section for results.');
            
            // Switch to reports section
            this.showSection('reports');
            
        }, 2000);
    }

    handleScreeningFailed(error) {
        // Clear the screening in progress flag
        this.screeningInProgress = false;
        this.closeModal();
        this.showToast('error', `Screening failed: ${error || 'Unknown error'}`);
    }

    handleScreeningTimeout() {
        // Clear the screening in progress flag
        this.screeningInProgress = false;
        this.closeModal();
        this.showToast('warning', 'Screening is taking longer than expected. Please check the projects section for updates.');
    }

    handleScreeningError(error) {
        // Clear the screening in progress flag
        this.screeningInProgress = false;
        this.closeModal();
        this.showToast('error', `Screening error: ${error.message}`);
    }

    cancelCurrentScreening() {
        // Clear the screening in progress flag
        this.screeningInProgress = false;
        // TODO: Implement screening cancellation
        this.closeModal();
        this.showToast('info', 'Screening cancelled');
    }

    // Project Management
    async loadProjects() {
        try {
            const response = await fetch('/api/projects');
            if (response.ok) {
                const data = await response.json();
                this.projects = data.projects || [];
                this.renderProjects();
                this.updateDashboardStats();
            }
        } catch (error) {
            console.error('Error loading projects:', error);
            this.showToast('error', 'Failed to load projects');
        }
    }

    renderProjects(filteredProjects = null) {
        const projectsList = document.getElementById('projectsList');
        const projects = filteredProjects || this.projects;
        
        if (projects.length === 0) {
            projectsList.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-secondary);">
                    <i class="fas fa-folder-open" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                    <h3>No Projects Found</h3>
                    <p>Start by creating a new environmental screening</p>
                    <button class="action-btn" onclick="app.showSection('new-screening')" style="margin-top: 1rem; display: inline-flex;">
                        <i class="fas fa-plus"></i>
                        <span>Create New Screening</span>
                    </button>
                </div>
            `;
            return;
        }

        projectsList.innerHTML = projects.map(project => this.createProjectCard(project)).join('');
    }

    createProjectCard(project) {
        const statusClass = this.getStatusClass(project.status);
        const riskClass = this.getRiskClass(project.risk_level);
        
        return `
            <div class="project-card">
                <div class="project-header">
                    <div class="project-title">
                        <i class="fas fa-project-diagram"></i>
                        ${project.name}
                    </div>
                    <div class="project-meta">${this.formatDate(project.created_date)}</div>
                </div>
                <div class="project-body">
                    <div class="project-status ${statusClass}">${project.status}</div>
                    <div class="project-stats">
                        <div class="stat">
                            <div class="stat-value">${project.analyses_count || 0}</div>
                            <div class="stat-label">Analyses</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">${project.reports_count || 0}</div>
                            <div class="stat-label">Reports</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value ${riskClass}">${project.risk_level || 'N/A'}</div>
                            <div class="stat-label">Risk Level</div>
                        </div>
                    </div>
                    <div class="project-actions">
                        <button class="action-btn-small" onclick="app.viewProject('${project.id}')">
                            <i class="fas fa-eye"></i>
                            View Details
                        </button>
                        <button class="action-btn-small" onclick="app.downloadProjectReports('${project.id}')">
                            <i class="fas fa-download"></i>
                            Download Reports
                        </button>
                        ${project.status === 'completed' ? `
                            <button class="action-btn-small" onclick="app.shareProject('${project.id}')">
                                <i class="fas fa-share"></i>
                                Share
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    // Report Management
    async loadReports() {
        try {
            const response = await fetch('/api/reports');
            if (response.ok) {
                const data = await response.json();
                this.reports = data.reports || [];
                this.renderReports();
            }
        } catch (error) {
            console.error('Error loading reports:', error);
            this.showToast('error', 'Failed to load reports');
        }
    }

    renderReports(filteredReports = null) {
        const reportsList = document.getElementById('reportsList');
        const reports = filteredReports || this.reports;
        
        if (reports.length === 0) {
            reportsList.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-secondary);">
                    <i class="fas fa-file-pdf" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                    <h3>No Reports Available</h3>
                    <p>Reports will appear here after completing environmental screenings</p>
                </div>
            `;
            return;
        }

        // Sort reports: comprehensive PDFs first, then by date
        const sortedReports = [...reports].sort((a, b) => {
            // First, prioritize comprehensive PDFs
            const aIsComprehensive = a.category === 'comprehensive_pdf';
            const bIsComprehensive = b.category === 'comprehensive_pdf';
            
            if (aIsComprehensive && !bIsComprehensive) return -1;
            if (!aIsComprehensive && bIsComprehensive) return 1;
            
            // Then sort by creation date (newest first)
            return new Date(b.created_date) - new Date(a.created_date);
        });

        // Group reports by type
        const comprehensiveReports = sortedReports.filter(r => r.category === 'comprehensive_pdf');
        const otherReports = sortedReports.filter(r => r.category !== 'comprehensive_pdf');

        let html = '';

        // Add comprehensive reports section
        if (comprehensiveReports.length > 0) {
            html += `
                <div style="grid-column: 1 / -1; margin-bottom: 1rem;">
                    <h3 style="color: var(--primary-color); display: flex; align-items: center; gap: 0.5rem; margin: 0;">
                        <i class="fas fa-award"></i>
                        Comprehensive Environmental Reports (${comprehensiveReports.length})
                    </h3>
                    <p style="color: var(--text-secondary); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                        Complete 11-section environmental screening reports with embedded maps and analysis
                    </p>
                </div>
            `;
            html += comprehensiveReports.map(report => this.createReportCard(report)).join('');
        }

        // Add other reports section
        if (otherReports.length > 0) {
            if (comprehensiveReports.length > 0) {
                html += `
                    <div style="grid-column: 1 / -1; margin: 2rem 0 1rem 0;">
                        <h3 style="color: var(--text-secondary); display: flex; align-items: center; gap: 0.5rem; margin: 0;">
                            <i class="fas fa-file-alt"></i>
                            Supporting Documents & Reports (${otherReports.length})
                        </h3>
                    </div>
                `;
            }
            html += otherReports.map(report => this.createReportCard(report)).join('');
        }

        reportsList.innerHTML = html;
    }

    createReportCard(report) {
        const fileType = report.file_type || this.getFileType(report.filename);
        const fileIcon = report.file_icon || this.getFileIcon(fileType);
        const isComprehensivePDF = report.category === 'comprehensive_pdf';
        
        // Determine the best download URL
        const downloadUrl = report.pdf_download_url || report.download_url || `/files/${report.filename}`;
        const previewUrl = report.preview_url || `/preview/${report.filename}`;
        
        return `
            <div class="report-card ${isComprehensivePDF ? 'comprehensive-pdf' : ''}">
                <div class="report-header">
                    <div class="report-title">
                        <i class="${fileIcon}"></i>
                        ${report.title || report.filename}
                        ${isComprehensivePDF ? '<span class="comprehensive-badge">Comprehensive Report</span>' : ''}
                    </div>
                    <div class="report-meta">${this.formatDate(report.created_date)}</div>
                </div>
                <div class="report-body">
                    <div class="report-stats">
                        <div class="stat">
                            <div class="stat-value">${this.formatFileSize(report.size)}</div>
                            <div class="stat-label">File Size</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">${fileType.toUpperCase()}</div>
                            <div class="stat-label">Format</div>
                        </div>
                        ${report.category ? `
                        <div class="stat">
                            <div class="stat-value">${this.getCategoryDisplay(report.category)}</div>
                            <div class="stat-label">Type</div>
                        </div>
                        ` : ''}
                    </div>
                    <div class="report-actions">
                        <button class="action-btn-small primary" onclick="window.open('${downloadUrl}', '_blank')">
                            <i class="fas fa-download"></i>
                            ${isComprehensivePDF ? 'Download PDF' : 'Download'}
                        </button>
                        ${report.is_pdf ? `
                        <button class="action-btn-small" onclick="window.open('${previewUrl}', '_blank')">
                            <i class="fas fa-eye"></i>
                            Preview
                        </button>
                        ` : ''}
                        <button class="action-btn-small" onclick="app.copyDownloadLink('${downloadUrl}')">
                            <i class="fas fa-link"></i>
                            Copy Link
                        </button>
                        ${isComprehensivePDF ? `
                        <button class="action-btn-small success" onclick="app.shareComprehensiveReport('${report.filename}')">
                            <i class="fas fa-share-alt"></i>
                            Share Report
                        </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    getCategoryDisplay(category) {
        const categoryMap = {
            'comprehensive_pdf': 'Comprehensive',
            'pdf': 'PDF Report',
            'data': 'Data File',
            'report': 'Report'
        };
        return categoryMap[category] || category;
    }

    copyDownloadLink(url) {
        const fullUrl = window.location.origin + url;
        navigator.clipboard.writeText(fullUrl).then(() => {
            this.showToast('success', 'Download link copied to clipboard');
        }).catch(() => {
            this.showToast('error', 'Failed to copy link');
        });
    }

    shareComprehensiveReport(filename) {
        const downloadUrl = window.location.origin + `/pdfs/${filename}`;
        if (navigator.share) {
            navigator.share({
                title: 'Environmental Screening Report',
                text: 'Comprehensive Environmental Screening Report',
                url: downloadUrl
            }).then(() => {
                this.showToast('success', 'Report shared successfully');
            }).catch(() => {
                this.copyDownloadLink(`/pdfs/${filename}`);
            });
        } else {
            this.copyDownloadLink(`/pdfs/${filename}`);
        }
    }

    // Utility Functions
    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString();
    }

    formatDate(timestamp) {
        return new Date(timestamp).toLocaleDateString();
    }

    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return Math.round(bytes / 1024) + ' KB';
        return Math.round(bytes / (1024 * 1024)) + ' MB';
    }

    getStatusClass(status) {
        const statusMap = {
            'completed': 'status-completed',
            'in-progress': 'status-in-progress',
            'failed': 'status-failed'
        };
        return statusMap[status] || 'status-in-progress';
    }

    getRiskClass(riskLevel) {
        const riskMap = {
            'Low': 'success',
            'Moderate': 'warning',
            'High': 'danger'
        };
        return riskMap[riskLevel] || '';
    }

    getFileType(filename) {
        const extension = filename.split('.').pop().toLowerCase();
        return extension;
    }

    getFileIcon(fileType) {
        const iconMap = {
            'pdf': 'fas fa-file-pdf',
            'json': 'fas fa-file-code',
            'md': 'fas fa-file-alt',
            'png': 'fas fa-file-image',
            'jpg': 'fas fa-file-image',
            'jpeg': 'fas fa-file-image'
        };
        return iconMap[fileType] || 'fas fa-file';
    }

    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    // UI Actions
    resetForm() {
        document.getElementById('screeningForm').reset();
        this.selectedCoordinates = null;
        if (this.map) {
            this.map.eachLayer(layer => {
                if (layer instanceof L.Marker) {
                    this.map.removeLayer(layer);
                }
            });
        }
        this.showToast('info', 'Form reset');
    }

    loadExampleProjects() {
        const examples = [
            {
                name: "Industrial Development Assessment",
                cadastral: "060-000-009-58",
                location: "Toa Baja, Puerto Rico"
            },
            {
                name: "Marina Construction Screening", 
                coordinates: { latitude: 18.4154, longitude: -66.2097 },
                location: "Dorado, Puerto Rico"
            }
        ];

        // Populate example dropdown
        const exampleSelect = document.getElementById('exampleProjects');
        if (exampleSelect) {
            examples.forEach((example, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = example.name;
                exampleSelect.appendChild(option);
            });

            exampleSelect.addEventListener('change', (e) => {
                if (e.target.value !== '') {
                    const example = examples[parseInt(e.target.value)];
                    document.getElementById('projectName').value = example.name;
                    document.getElementById('locationName').value = example.location;
                    
                    if (example.cadastral) {
                        document.getElementById('cadastralNumber').value = example.cadastral;
                        this.switchLocationTab('cadastral');
                    } else if (example.coordinates) {
                        document.getElementById('latitude').value = example.coordinates.latitude;
                        document.getElementById('longitude').value = example.coordinates.longitude;
                        this.switchLocationTab('coordinates');
                    }
                }
            });
        }
    }

    openHelp() {
        window.open('/help', '_blank');
    }

    // Filter and Search
    filterProjects() {
        const searchTerm = document.getElementById('projectSearch').value.toLowerCase();
        const filterValue = document.getElementById('projectFilter').value;
        
        let filtered = this.projects;
        
        if (searchTerm) {
            filtered = filtered.filter(project => 
                project.name.toLowerCase().includes(searchTerm) ||
                project.description?.toLowerCase().includes(searchTerm)
            );
        }
        
        if (filterValue) {
            filtered = filtered.filter(project => project.status === filterValue);
        }
        
        this.renderProjects(filtered);
    }

    filterReports() {
        const searchTerm = document.getElementById('reportSearch').value.toLowerCase();
        const typeFilter = document.getElementById('reportTypeFilter').value;
        
        let filtered = this.reports;
        
        if (searchTerm) {
            filtered = filtered.filter(report => 
                report.filename.toLowerCase().includes(searchTerm) ||
                report.title?.toLowerCase().includes(searchTerm)
            );
        }
        
        if (typeFilter) {
            filtered = filtered.filter(report => 
                this.getFileType(report.filename) === typeFilter
            );
        }
        
        this.renderReports(filtered);
    }

    // Modal Management
    closeModal() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    }

    // Toast Notifications
    showToast(type, message) {
        const toast = document.getElementById('toast');
        const icon = toast.querySelector('.toast-icon');
        const messageElement = toast.querySelector('.toast-message');
        
        // Set content
        messageElement.textContent = message;
        
        // Set icon based on type
        const icons = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle'
        };
        
        icon.className = `toast-icon ${icons[type] || icons.info}`;
        
        // Set type class
        toast.className = `toast ${type} active`;
        
        // Auto hide after 5 seconds
        setTimeout(() => this.hideToast(), 5000);
    }

    hideToast() {
        document.getElementById('toast').classList.remove('active');
    }

    // Periodic Updates
    startPeriodicUpdates() {
        // Update dashboard every 30 seconds
        setInterval(() => {
            if (this.currentSection === 'dashboard') {
                this.loadDashboardData();
            }
        }, 30000);

        // Check for new reports every 60 seconds
        setInterval(() => {
            this.loadReports();
        }, 60000);
    }

    // Project Actions
    async viewProject(projectId) {
        // TODO: Implement project detail view
        this.showToast('info', 'Project details view coming soon');
    }

    async downloadProjectReports(projectId) {
        try {
            const response = await fetch(`/api/projects/${projectId}/download`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `project-${projectId}-reports.zip`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                this.showToast('success', 'Reports downloaded successfully');
            } else {
                throw new Error('Download failed');
            }
        } catch (error) {
            this.showToast('error', 'Failed to download reports');
        }
    }

    async shareProject(projectId) {
        // TODO: Implement project sharing
        this.showToast('info', 'Project sharing feature coming soon');
    }

    // Report Action Methods - Updated for new PDF structure
    async downloadReport(filename) {
        // Legacy method - now handled directly by download URLs
        window.open(`/files/${filename}`, '_blank');
    }

    async previewReport(filename) {
        // Legacy method - now handled directly by preview URLs
        window.open(`/preview/${filename}`, '_blank');
    }

    async shareReport(filename) {
        // Legacy method - now handled by shareComprehensiveReport or copyDownloadLink
        this.copyDownloadLink(`/files/${filename}`);
    }

    // Batch Screening Methods
    addBatchItem() {
        // Create new batch item with default values
        const newItem = {
            id: Date.now().toString(),
            projectName: '',
            locationName: '',
            cadastralNumber: '',
            coordinates: null,
            analyses: this.getGlobalBatchAnalyses(),
            reportOptions: this.getGlobalBatchReportOptions(),
            status: 'pending'
        };

        this.batchItems.push(newItem);
        this.renderBatchItems();
        this.updateBatchCounter();
        this.showBatchItemForm(newItem.id);
    }

    showBatchItemForm(itemId) {
        const item = this.batchItems.find(i => i.id === itemId);
        if (!item) return;

        // Create a modal form for editing the batch item
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-edit"></i> Edit Batch Item</h3>
                    <button class="modal-close" onclick="this.parentElement.parentElement.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <form id="batchItemForm">
                        <div class="form-group">
                            <label for="batchItemName">Project Name *</label>
                            <input type="text" id="batchItemName" value="${item.projectName}" required>
                        </div>
                        <div class="form-group">
                            <label for="batchItemLocation">Location Name</label>
                            <input type="text" id="batchItemLocation" value="${item.locationName}">
                        </div>
                        <div class="form-group">
                            <label for="batchItemCadastral">Cadastral Number</label>
                            <input type="text" id="batchItemCadastral" value="${item.cadastralNumber}" 
                                   placeholder="XXX-XXX-XXX-XX" pattern="[0-9]{3}-[0-9]{3}-[0-9]{3}-[0-9]{2}">
                        </div>
                        <div class="form-grid">
                            <div class="form-group">
                                <label for="batchItemLng">Longitude</label>
                                <input type="number" id="batchItemLng" step="any" value="${item.coordinates?.longitude || ''}">
                            </div>
                            <div class="form-group">
                                <label for="batchItemLat">Latitude</label>
                                <input type="number" id="batchItemLat" step="any" value="${item.coordinates?.latitude || ''}">
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="submit-btn" onclick="app.saveBatchItem('${itemId}')">
                        <i class="fas fa-save"></i> Save Item
                    </button>
                    <button type="button" class="cancel-btn" onclick="this.parentElement.parentElement.parentElement.remove()">
                        Cancel
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.style.display = 'flex';
    }

    saveBatchItem(itemId) {
        const item = this.batchItems.find(i => i.id === itemId);
        if (!item) return;

        // Get form values
        item.projectName = document.getElementById('batchItemName').value;
        item.locationName = document.getElementById('batchItemLocation').value;
        item.cadastralNumber = document.getElementById('batchItemCadastral').value;
        item.coordinates = {
            longitude: parseFloat(document.getElementById('batchItemLng').value) || null,
            latitude: parseFloat(document.getElementById('batchItemLat').value) || null
        };

        // Apply global settings if not individually set
        if (!item.projectName) {
            item.projectName = `Environmental Screening ${item.id}`;
        }

        // Validation
        if (!item.projectName) {
            alert('Project name is required');
            return;
        }

        if (!item.cadastralNumber && (!item.coordinates?.longitude || !item.coordinates?.latitude)) {
            alert('Either cadastral number or coordinates must be provided');
            return;
        }

        // Close modal and update display
        document.querySelector('.modal').remove();
        this.renderBatchItems();
        this.updateBatchCounter();
    }

    getGlobalBatchAnalyses() {
        const analyses = [];
        if (document.getElementById('batchProperty')?.checked) analyses.push('property');
        if (document.getElementById('batchKarst')?.checked) analyses.push('karst');
        if (document.getElementById('batchFlood')?.checked) analyses.push('flood');
        if (document.getElementById('batchWetland')?.checked) analyses.push('wetland');
        if (document.getElementById('batchHabitat')?.checked) analyses.push('habitat');
        if (document.getElementById('batchAirQuality')?.checked) analyses.push('air_quality');
        return analyses;
    }

    getGlobalBatchReportOptions() {
        return {
            comprehensive: document.getElementById('batchComprehensiveReport')?.checked || false,
            pdf: document.getElementById('batchPdf')?.checked || false,
            llmEnhancement: document.getElementById('batchLlmEnhancement')?.checked || false
        };
    }

    deleteBatchItem(itemId) {
        this.batchItems = this.batchItems.filter(item => item.id !== itemId);
        this.renderBatchItems();
        this.updateBatchCounter();
    }

    clearBatchItems() {
        if (this.batchItems.length === 0) return;
        
        if (confirm('Are you sure you want to clear all batch items?')) {
            this.batchItems = [];
            this.renderBatchItems();
            this.updateBatchCounter();
            this.showToast('All batch items cleared', 'info');
        }
    }

    renderBatchItems() {
        const container = document.getElementById('batchItemsList');
        
        if (this.batchItems.length === 0) {
            container.innerHTML = `
                <div class="no-items-placeholder">
                    <i class="fas fa-inbox"></i>
                    <h4>No items in queue</h4>
                    <p>Click "Add Item" to start building your batch screening queue</p>
                </div>
            `;
        } else {
            container.innerHTML = this.batchItems.map((item, index) => `
                <div class="batch-item">
                    <div class="batch-item-header">
                        <div class="batch-item-title">
                            <i class="fas fa-project-diagram"></i>
                            <span>${item.projectName || `Item ${item.id}`}</span>
                        </div>
                        <div class="batch-item-actions">
                            <button class="batch-item-edit" onclick="app.showBatchItemForm('${item.id}')" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="batch-item-delete" onclick="app.deleteBatchItem('${item.id}')" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="batch-item-details">
                        <div class="detail-row">
                            <label>Status</label>
                            <span class="status ${this.getStatusClass(item.status)}">
                                ${this.getStatusIcon(item.status)} ${this.getStatusText(item.status)}
                            </span>
                        </div>
                        <div class="detail-row">
                            <label>Location</label>
                            <span>${item.locationName || item.cadastralNumber || 
                                (item.coordinates?.longitude && item.coordinates?.latitude ? 
                                `${item.coordinates.longitude}, ${item.coordinates.latitude}` : 'Not specified')}</span>
                        </div>
                        <div class="detail-row">
                            <label>Analyses</label>
                            <span>${item.analyses?.length || 0} selected</span>
                        </div>
                    </div>
                </div>
            `).join('');
        }
    }

    getStatusIcon(status) {
        const icons = {
            pending: 'fa-clock',
            processing: 'fa-spinner',
            completed: 'fa-check-circle',
            failed: 'fa-exclamation-circle'
        };
        return icons[status] || 'fa-question-circle';
    }

    getStatusText(status) {
        const texts = {
            pending: 'Pending',
            processing: 'Processing',
            completed: 'Completed',
            failed: 'Failed'
        };
        return texts[status] || 'Unknown';
    }

    async processBatchSequential() {
        for (let i = 0; i < this.currentBatch.items.length; i++) {
            if (this.currentBatch.status === 'cancelled') break;
            
            const item = this.currentBatch.items[i];
            await this.processBatchItem(item, i);
        }
        this.completeBatch();
    }

    async processBatchParallel() {
        const promises = this.currentBatch.items.map((item, index) => 
            this.processBatchItem(item, index)
        );
        
        await Promise.allSettled(promises);
        this.completeBatch();
    }

    async processBatchTimed() {
        const delay = (document.getElementById('batchDelay').value || 5) * 60000; // Convert to milliseconds
        
        for (let i = 0; i < this.currentBatch.items.length; i++) {
            if (this.currentBatch.status === 'cancelled') break;
            
            const item = this.currentBatch.items[i];
            await this.processBatchItem(item, i);
            
            // Add delay between items (except for the last one)
            if (i < this.currentBatch.items.length - 1) {
                this.logBatchMessage(`Waiting ${delay / 60000} minutes before next item...`);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
        this.completeBatch();
    }

    async processBatchItem(item, index) {
        try {
            // Update item status
            item.status = 'processing';
            this.updateBatchItemStatus(item.id, 'processing');
            this.logBatchMessage(`Starting screening for: ${item.projectName}`);

            // Prepare request data
            const requestData = {
                projectName: item.projectName,
                locationName: item.locationName,
                cadastralNumber: item.cadastralNumber,
                coordinates: item.coordinates,
                analyses: item.analyses,
                includeComprehensiveReport: item.reportOptions.comprehensive,
                includePdf: item.reportOptions.pdf,
                useLlmEnhancement: item.reportOptions.llmEnhancement
            };

            // Submit screening request
            const response = await fetch('/api/environmental-screening', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            item.screeningId = result.screening_id;

            // Monitor progress
            await this.monitorBatchItemProgress(item);

        } catch (error) {
            console.error('Batch item error:', error);
            item.status = 'failed';
            item.error = error.message;
            this.updateBatchItemStatus(item.id, 'failed');
            this.currentBatch.failedItems++;
            this.logBatchMessage(`Failed: ${item.projectName} - ${error.message}`, 'error');
        }

        this.updateBatchProgress();
    }

    async monitorBatchItemProgress(item) {
        return new Promise((resolve) => {
            const checkProgress = async () => {
                try {
                    const response = await fetch(`/api/environmental-screening/${item.screeningId}/status`);
                    const status = await response.json();

                    if (status.status === 'completed') {
                        item.status = 'completed';
                        this.updateBatchItemStatus(item.id, 'completed');
                        this.currentBatch.completedItems++;
                        this.logBatchMessage(`Completed: ${item.projectName}`, 'success');
                        resolve();
                    } else if (status.status === 'failed') {
                        item.status = 'failed';
                        item.error = status.error || 'Unknown error';
                        this.updateBatchItemStatus(item.id, 'failed');
                        this.currentBatch.failedItems++;
                        this.logBatchMessage(`Failed: ${item.projectName} - ${item.error}`, 'error');
                        resolve();
                    } else {
                        // Still processing, check again in 5 seconds
                        setTimeout(checkProgress, 5000);
                    }
                } catch (error) {
                    item.status = 'failed';
                    item.error = error.message;
                    this.updateBatchItemStatus(item.id, 'failed');
                    this.currentBatch.failedItems++;
                    resolve();
                }
            };

            checkProgress();
        });
    }

    updateBatchItemStatus(itemId, status) {
        const element = document.getElementById(`batchItem_${itemId}`);
        if (element) {
            element.className = `batch-item-progress ${status}`;
            
            const statusElement = element.querySelector('.batch-item-status');
            statusElement.className = `batch-item-status ${status}`;
            statusElement.innerHTML = `
                <i class="fas ${this.getStatusIcon(status)}"></i>
                <span>${this.getStatusText(status)}</span>
            `;
        }
    }

    updateBatchProgress() {
        const completed = this.currentBatch.completedItems;
        const failed = this.currentBatch.failedItems;
        const total = this.currentBatch.totalItems;
        const remaining = total - completed - failed;
        const percentage = Math.round(((completed + failed) / total) * 100);

        document.getElementById('batchCompletedItems').textContent = completed;
        document.getElementById('batchFailedItems').textContent = failed;
        document.getElementById('batchRemainingItems').textContent = remaining;
        document.getElementById('batchProgressPercentage').textContent = `${percentage}%`;
        document.getElementById('batchProgressFill').style.width = `${percentage}%`;

        if (remaining > 0) {
            document.getElementById('batchProgressStatus').textContent = 
                `Processing... ${completed + failed} of ${total} items processed`;
        }
    }

    completeBatch() {
        this.currentBatch.status = 'completed';
        this.currentBatch.endTime = new Date();
        
        const completed = this.currentBatch.completedItems;
        const failed = this.currentBatch.failedItems;
        const total = this.currentBatch.totalItems;

        document.getElementById('batchProgressStatus').textContent = 
            `Batch completed! ${completed} successful, ${failed} failed out of ${total} total`;

        this.logBatchMessage(`Batch processing completed. ${completed}/${total} items successful.`, 'success');

        // Show notification based on settings
        const notificationMode = document.getElementById('batchNotifications').value;
        if (notificationMode === 'batch' || notificationMode === 'each') {
            this.showToast(`Batch completed: ${completed}/${total} successful`, 'success');
        }

        // Auto-refresh projects and reports
        setTimeout(() => {
            this.loadProjects();
            this.loadReports();
        }, 2000);
    }

    pauseBatch() {
        this.currentBatch.status = 'paused';
        this.logBatchMessage('Batch processing paused by user.', 'warning');
        document.getElementById('pauseBatchScreening').innerHTML = 
            '<i class="fas fa-play"></i> Resume Batch';
        document.getElementById('pauseBatchScreening').onclick = () => this.resumeBatch();
    }

    resumeBatch() {
        this.currentBatch.status = 'running';
        this.logBatchMessage('Batch processing resumed.', 'info');
        document.getElementById('pauseBatchScreening').innerHTML = 
            '<i class="fas fa-pause"></i> Pause Batch';
        document.getElementById('pauseBatchScreening').onclick = () => this.pauseBatch();
    }

    cancelBatch() {
        if (confirm('Are you sure you want to cancel the batch processing?')) {
            this.currentBatch.status = 'cancelled';
            this.logBatchMessage('Batch processing cancelled by user.', 'warning');
            this.closeBatchProgress();
        }
    }

    closeBatchProgress() {
        document.getElementById('batchProgressModal').style.display = 'none';
        this.currentBatch = null;
    }

    logBatchMessage(message, type = 'info') {
        const logContainer = document.getElementById('batchProgressLog');
        const timestamp = new Date().toLocaleTimeString();
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.innerHTML = `
            <span class="log-time">${timestamp}</span>
            <span class="log-message">${message}</span>
        `;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    resetBatchForm() {
        if (this.batchItems.length > 0 && !confirm('Are you sure you want to reset the batch form? All items will be lost.')) {
            return;
        }

        this.batchItems = [];
        this.renderBatchItems();
        this.updateBatchCounter();

        // Reset global settings
        document.getElementById('batchProjectType').value = '';
        document.getElementById('batchLocationRegion').value = '';
        document.getElementById('batchProcessingMode').value = 'sequential';
        document.getElementById('batchDelay').value = '5';
        document.getElementById('batchNotifications').value = 'each';

        // Reset checkboxes
        ['batchProperty', 'batchKarst', 'batchFlood', 'batchWetland', 'batchHabitat', 'batchAirQuality',
         'batchComprehensiveReport', 'batchPdf', 'batchLlmEnhancement'].forEach(id => {
            const checkbox = document.getElementById(id);
            if (checkbox) checkbox.checked = true;
        });

        this.showToast('Batch form reset successfully', 'info');
    }

    // Helper method to update UI based on processing mode
    updateProcessingModeUI() {
        const mode = document.getElementById('batchProcessingMode').value;
        const delayGroup = document.getElementById('batchDelayGroup');
        
        if (mode === 'timed') {
            delayGroup.style.display = 'block';
        } else {
            delayGroup.style.display = 'none';
        }
    }

    updateBatchCounter() {
        const count = this.batchItems.length;
        console.log('📊 Updating batch counter, count:', count);
        
        // Update all counter elements
        document.getElementById('batchItemCount').textContent = count;
        document.getElementById('batchButtonCount').textContent = count;
        
        // Update queue status
        const queueStatus = document.getElementById('batchQueueStatus');
        if (queueStatus) {
            queueStatus.textContent = count === 0 ? 'Empty' : `${count} item${count === 1 ? '' : 's'}`;
        }
        
        // Update start button state
        const startBtn = document.getElementById('startBatchBtn');
        if (startBtn) {
            startBtn.disabled = count === 0;
            
            if (count === 0) {
                startBtn.classList.add('disabled');
                startBtn.title = 'Add items to the batch queue first, then this button will become enabled';
            } else {
                startBtn.classList.remove('disabled');
                startBtn.title = `Start batch screening for ${count} item${count === 1 ? '' : 's'}`;
            }
        }
        
        // Hide/show instructions based on whether there are items
        const instructions = document.getElementById('batchInstructions');
        if (instructions) {
            instructions.style.display = count === 0 ? 'block' : 'none';
        }
        
        console.log('✅ Batch counter updated, button disabled:', count === 0);
    }

    parseCSVToBatchItems(csvText) {
        const lines = csvText.split('\n');
        const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
        
        return lines.slice(1)
            .filter(line => line.trim())
            .map((line, index) => {
                const values = line.split(',').map(v => v.trim());
                const item = {
                    id: Date.now() + index,
                    projectName: '',
                    locationName: '',
                    cadastralNumber: '',
                    coordinates: { longitude: null, latitude: null },
                    analyses: this.getGlobalBatchAnalyses(),
                    reportOptions: this.getGlobalBatchReportOptions(),
                    status: 'pending'
                };

                headers.forEach((header, i) => {
                    const value = values[i] || '';
                    switch (header) {
                        case 'project_name':
                        case 'name':
                            item.projectName = value;
                            break;
                        case 'cadastral':
                        case 'cadastral_number':
                            item.cadastralNumber = value;
                            break;
                        case 'location':
                        case 'location_name':
                            item.locationName = value;
                            break;
                        case 'longitude':
                        case 'lng':
                            item.coordinates.longitude = parseFloat(value) || null;
                            break;
                        case 'latitude':
                        case 'lat':
                            item.coordinates.latitude = parseFloat(value) || null;
                            break;
                    }
                });

                if (!item.projectName) {
                    item.projectName = `Imported Project ${index + 1}`;
                }

                return item;
            });
    }
}

// Initialize the application
const app = new EnvironmentalScreeningApp();

// Export for global access
window.app = app; 