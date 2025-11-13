// Gate Controller Dashboard - Phase 4

class Dashboard {
    constructor() {
        this.ws = null;
        this.reconnectInterval = null;
        this.detectedTokens = new Map(); // Track detected tokens with timestamps
        this.filteredTokens = [];
        this.config = null;
        this.isScanning = false;
        this.isEditingConfig = false;
        this.refreshIntervals = {};
        this.scannedDevices = { ibeacons: [], devices: [] }; // Full scan results
        this.isScanningAll = false;
        this.editingToken = null;
        this.init();
    }

    init() {
        this.setupTabs();
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadInitialData();
        this.startPeriodicRefresh();
        
        // Restore last active tab from localStorage
        const savedTab = localStorage.getItem('activeTab');
        if (savedTab) {
            this.switchTab(savedTab);
        }
    }

    // Tab Management
    setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabName = btn.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab panes
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        document.getElementById(`${tabName}-pane`).classList.add('active');

        // Save to localStorage
        localStorage.setItem('activeTab', tabName);

        // Load tab-specific data
        if (tabName === 'config') {
            this.loadConfig();
        } else if (tabName === 'tokens') {
            this.loadTokens();
        } else if (tabName === 'activity') {
            this.loadActivity();
        }
    }

    // WebSocket Setup
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateControllerStatus(true);
            if (this.reconnectInterval) {
                clearInterval(this.reconnectInterval);
                this.reconnectInterval = null;
            }
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateControllerStatus(false);
            this.reconnect();
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleWebSocketMessage(message);
        };
        
        // Keep-alive ping
        setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send('ping');
            }
        }, 30000);
    }

    reconnect() {
        if (!this.reconnectInterval) {
            this.reconnectInterval = setInterval(() => {
                console.log('Attempting to reconnect...');
                this.setupWebSocket();
            }, 5000);
        }
    }

    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'status':
                this.updateGateStatus(message.data);
                break;
            case 'token_detected':
                this.handleTokenDetected(message.data);
                break;
            case 'gate_opened':
            case 'gate_closed':
                this.loadActivity();
                break;
            case 'token_registered':
            case 'token_unregistered':
                this.loadTokens();
                break;
        }
    }

    handleTokenDetected(data) {
        // Add to detected tokens map
        this.detectedTokens.set(data.uuid, {
            name: data.name,
            uuid: data.uuid,
            timestamp: new Date(),
            rssi: data.rssi || null,
            distance: data.distance || null
        });

        // Update detected tokens count
        document.getElementById('detected-count').textContent = this.detectedTokens.size;

        // Render detected tokens
        this.renderDetectedTokens();
        this.loadActivity();
    }

    renderDetectedTokens() {
        const container = document.getElementById('detected-token-list');
        const tokens = Array.from(this.detectedTokens.values())
            .sort((a, b) => b.timestamp - a.timestamp);

        if (tokens.length === 0) {
            container.innerHTML = '<div class="empty-state">No tokens detected yet</div>';
            return;
        }

        container.innerHTML = tokens.map(token => {
            const timeAgo = this.formatTimeAgo(token.timestamp);
            const signalInfo = token.rssi ? `RSSI: ${token.rssi} dBm` : '';
            const distanceInfo = token.distance ? ` | ~${token.distance}m` : '';

            return `
                <div class="detected-token-item">
                    <div class="detected-token-info">
                        <div class="detected-token-name">${this.escapeHtml(token.name)}</div>
                        <div class="detected-token-details">${this.escapeHtml(token.uuid)}</div>
                        ${signalInfo || distanceInfo ? `<div class="detected-token-details">${signalInfo}${distanceInfo}</div>` : ''}
                    </div>
                    <div class="detected-token-time">${timeAgo}</div>
                </div>
            `;
        }).join('');
    }

    formatTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        if (seconds < 60) return `${seconds}s ago`;
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        return `${hours}h ago`;
    }

    // Event Listeners
    setupEventListeners() {
        // Gate control buttons
        document.getElementById('btn-open-gate').addEventListener('click', () => this.openGate());
        document.getElementById('btn-close-gate').addEventListener('click', () => this.closeGate());
        document.getElementById('btn-refresh-token').addEventListener('click', () => this.refreshC4Token());

        // Token management
        document.getElementById('btn-add-token').addEventListener('click', () => this.showAddTokenModal());
        document.getElementById('btn-scan-all').addEventListener('click', () => this.scanAllDevices());
        document.getElementById('modal-close').addEventListener('click', () => this.hideAddTokenModal());
        document.getElementById('modal-cancel').addEventListener('click', () => this.hideAddTokenModal());
        document.getElementById('modal-save').addEventListener('click', () => this.saveToken());
        document.getElementById('btn-scan-beacons').addEventListener('click', () => this.scanBeaconsForAdd());

        // Edit token modal
        document.getElementById('edit-modal-close').addEventListener('click', () => this.hideEditTokenModal());
        document.getElementById('edit-modal-cancel').addEventListener('click', () => this.hideEditTokenModal());
        document.getElementById('edit-modal-save').addEventListener('click', () => this.saveTokenEdit());

        // Scan results modal
        document.getElementById('scan-results-close').addEventListener('click', () => this.hideScanResultsModal());

        // Token filter
        const filterInput = document.getElementById('token-filter');
        filterInput.addEventListener('input', (e) => this.filterTokens(e.target.value));
        document.getElementById('btn-clear-filter').addEventListener('click', () => {
            filterInput.value = '';
            this.filterTokens('');
        });

        // Scan controls
        document.getElementById('btn-start-scan').addEventListener('click', () => this.startScan());
        document.getElementById('btn-stop-scan').addEventListener('click', () => this.stopScan());

        // Config edit buttons
        document.getElementById('btn-save-config').addEventListener('click', () => this.saveConfig());
        document.getElementById('btn-cancel-config').addEventListener('click', () => this.cancelConfigEdit());

        // Activity log
        document.getElementById('btn-clear-log').addEventListener('click', () => this.clearLog());
        document.getElementById('activity-mode-toggle').addEventListener('change', (e) => this.toggleActivityMode(e.target.checked));

        // Statistics
        document.getElementById('btn-run-stats').addEventListener('click', () => this.runStats());
        document.getElementById('btn-add-note').addEventListener('click', () => this.showAddNoteModal());
        document.getElementById('note-modal-close').addEventListener('click', () => this.hideAddNoteModal());
        document.getElementById('note-modal-cancel').addEventListener('click', () => this.hideAddNoteModal());
        document.getElementById('note-modal-save').addEventListener('click', () => this.saveNote());

        // Close modals on outside click
        document.getElementById('add-token-modal').addEventListener('click', (e) => {
            if (e.target.id === 'add-token-modal') {
                this.hideAddTokenModal();
            }
        });
        document.getElementById('edit-token-modal').addEventListener('click', (e) => {
            if (e.target.id === 'edit-token-modal') {
                this.hideEditTokenModal();
            }
        });
        document.getElementById('scan-results-modal').addEventListener('click', (e) => {
            if (e.target.id === 'scan-results-modal') {
                this.hideScanResultsModal();
            }
        });
        document.getElementById('add-note-modal').addEventListener('click', (e) => {
            if (e.target.id === 'add-note-modal') {
                this.hideAddNoteModal();
            }
        });
    }

    // Data Loading
    async loadInitialData() {
        await Promise.all([
            this.loadStatus(),
            this.loadTokens(),
            this.loadActivity(),
            this.loadActivityMode(),
            this.loadNotes()
        ]);
    }

    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            this.updateGateStatus(data);
        } catch (error) {
            console.error('Failed to load status:', error);
        }
    }

    async loadTokens() {
        try {
            const response = await fetch('/api/tokens');
            const data = await response.json();
            this.renderTokens(data.tokens);
        } catch (error) {
            console.error('Failed to load tokens:', error);
        }
    }

    async loadActivity() {
        try {
            const response = await fetch('/api/activity');
            const data = await response.json();
            this.renderActivity(data.activity);
        } catch (error) {
            console.error('Failed to load activity:', error);
        }
    }

    async loadConfig() {
        if (this.config) {
            this.renderConfig(this.config);
            return;
        }

        try {
            const response = await fetch('/api/config');
            const data = await response.json();
            this.config = data;
            this.renderConfig(data);
        } catch (error) {
            console.error('Failed to load config:', error);
        }
    }

    // UI Updates
    updateControllerStatus(online) {
        const badge = document.getElementById('controller-status');
        const text = badge.querySelector('.status-text');
        
        badge.classList.remove('online', 'offline');
        if (online) {
            badge.classList.add('online');
            text.textContent = 'Online';
        } else {
            badge.classList.add('offline');
            text.textContent = 'Offline';
        }
    }

    updateGateStatus(data) {
        const stateEl = document.getElementById('gate-state');
        const sessionEl = document.getElementById('session-info');
        
        // Update gate state
        if (data.gate_status) {
            stateEl.textContent = data.gate_status.charAt(0).toUpperCase() + data.gate_status.slice(1);
        }
        
        // Update session info
        if (data.active_session) {
            const start = new Date(data.session_start);
            const duration = Math.floor((new Date() - start) / 1000);
            const minutes = Math.floor(duration / 60);
            const seconds = duration % 60;
            sessionEl.textContent = `Active session: ${minutes}m ${seconds}s`;
            sessionEl.classList.add('active');
        } else {
            sessionEl.textContent = 'No active session';
            sessionEl.classList.remove('active');
        }
    }

    renderTokens(tokens) {
        const container = document.getElementById('token-list');
        
        // Store all tokens for filtering
        this.filteredTokens = tokens;
        
        if (tokens.length === 0) {
            container.innerHTML = '<div class="empty-state">No tokens registered</div>';
            return;
        }

        container.innerHTML = tokens.map(token => {
            // Check if token is detected (online)
            const detected = this.detectedTokens.get(token.uuid);
            const isOnline = detected && (new Date() - detected.timestamp) < 30000; // 30 seconds
            const statusClass = isOnline ? 'online' : 'offline';
            const statusText = isOnline ? '🟢 Online' : '⚪ Offline';
            
            // Check active status (default true if not present)
            const isActive = token.active !== undefined ? token.active : true;
            const activeClass = isActive ? 'active' : 'inactive';
            const activeIcon = isActive ? '✅' : '⏸️';
            const activeText = isActive ? 'Active' : 'Paused';
            
            let signalInfo = '';
            if (isOnline && detected) {
                if (detected.rssi) signalInfo += `RSSI: ${detected.rssi} dBm`;
                if (detected.distance && detected.distance > 0) {
                    if (signalInfo) signalInfo += ' | ';
                    signalInfo += `~${detected.distance}m`;
                }
            }

            return `
                <div class="token-item ${statusClass} ${activeClass}">
                    <div class="token-info">
                        <div class="token-name">
                            ${this.escapeHtml(token.name)}
                            <span class="token-active-badge ${activeClass}">${activeIcon} ${activeText}</span>
                        </div>
                        <div class="token-uuid">${this.escapeHtml(token.uuid)}</div>
                    </div>
                    <div class="token-status">
                        <div class="token-status-badge ${statusClass}">${statusText}</div>
                        ${signalInfo ? `<div class="token-signal">${signalInfo}</div>` : ''}
                    </div>
                    <div class="token-actions">
                        <button class="btn-edit" data-uuid="${this.escapeHtml(token.uuid)}" title="Edit token">
                            ✏️
                        </button>
                        <button class="btn-delete" data-uuid="${this.escapeHtml(token.uuid)}" title="Delete token">
                            🗑️
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // Add edit event listeners
        container.querySelectorAll('.btn-edit').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const uuid = e.currentTarget.dataset.uuid;
                const token = tokens.find(t => t.uuid === uuid);
                this.showEditTokenModal(token);
            });
        });

        // Add delete event listeners
        container.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const uuid = e.currentTarget.dataset.uuid;
                this.deleteToken(uuid);
            });
        });
    }

    filterTokens(query) {
        if (!query) {
            this.renderTokens(this.filteredTokens);
            return;
        }

        const lowercaseQuery = query.toLowerCase();
        const filtered = this.filteredTokens.filter(token =>
            token.name.toLowerCase().includes(lowercaseQuery) ||
            token.uuid.toLowerCase().includes(lowercaseQuery)
        );

        this.renderTokens(filtered);
    }

    renderActivity(activities) {
        const container = document.getElementById('activity-log');
        
        if (activities.length === 0) {
            container.innerHTML = '<div class="empty-state">No activity recorded</div>';
            return;
        }

        container.innerHTML = activities.map(activity => {
            const time = new Date(activity.timestamp).toLocaleString();
            const typeClass = activity.type.replace('_', '-');
            
            // Show update indicator for suppressed entries
            const updateIndicator = activity.update_count > 0 
                ? `<span class="update-badge" title="Updated ${activity.update_count} time(s)">🔄 ${activity.update_count}</span>` 
                : '';
            
            return `
                <div class="activity-item activity-${typeClass}">
                    <div class="activity-time">${time} ${updateIndicator}</div>
                    <div class="activity-message">${this.escapeHtml(activity.message)}</div>
                </div>
            `;
        }).join('');
    }

    renderConfig(config) {
        // Control4 settings
        document.getElementById('config-c4-ip').textContent = config.c4.ip || '-';
        document.getElementById('config-gate-device-id').textContent = config.c4.gate_device_id || '-';
        document.getElementById('config-open-scenario').textContent = config.c4.open_gate_scenario || '-';
        document.getElementById('config-close-scenario').textContent = config.c4.close_gate_scenario || '-';

        // Gate behavior (display values)
        document.getElementById('config-auto-close').textContent = 
            config.gate.auto_close_timeout ? `${config.gate.auto_close_timeout}s (${Math.floor(config.gate.auto_close_timeout / 60)}m)` : '-';
        document.getElementById('config-session-timeout').textContent = 
            config.gate.session_timeout ? `${config.gate.session_timeout}s (${Math.floor(config.gate.session_timeout / 60)}m)` : '-';
        document.getElementById('config-status-interval').textContent = 
            config.gate.status_check_interval ? `${config.gate.status_check_interval}s` : '-';
        document.getElementById('config-scan-interval').textContent = 
            config.gate.ble_scan_interval ? `${config.gate.ble_scan_interval}s` : '-';

        // Set up edit button click handler
        const editBtn = document.getElementById('btn-edit-config');
        editBtn.style.display = 'none'; // Hide for now (config editing disabled in this version)
        
        // Enable edit mode on double-click of gate behavior card header
        const gateBehaviorHeader = document.querySelector('#config-pane .card:nth-child(2) .card-header h2');
        if (gateBehaviorHeader) {
            gateBehaviorHeader.style.cursor = 'pointer';
            gateBehaviorHeader.title = 'Double-click to edit';
            gateBehaviorHeader.ondblclick = () => {
                this.isEditingConfig = true;
                this.toggleConfigEdit(true);
            };
        }
    }

    // Gate Actions
    async openGate() {
        try {
            const response = await fetch('/api/gate/open', { method: 'POST' });
            const data = await response.json();
            this.showToast(data.success ? 'Gate opening...' : 'Failed to open gate', data.success ? 'success' : 'error');
        } catch (error) {
            this.showToast('Failed to open gate', 'error');
        }
    }

    async closeGate() {
        try {
            const response = await fetch('/api/gate/close', { method: 'POST' });
            const data = await response.json();
            this.showToast(data.success ? 'Gate closing...' : 'Failed to close gate', data.success ? 'success' : 'error');
        } catch (error) {
            this.showToast('Failed to close gate', 'error');
        }
    }
    
    async refreshC4Token() {
        if (!confirm('Refresh Control4 director token from cloud? This requires internet connection.')) {
            return;
        }
        
        const button = document.getElementById('btn-refresh-token');
        button.disabled = true;
        button.textContent = '🔄 Refreshing...';
        
        try {
            const response = await fetch('/api/c4/refresh-token', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showToast(`Token refreshed successfully (${data.controller})`, 'success');
            } else {
                this.showToast(data.message || 'Failed to refresh token', 'error');
            }
        } catch (error) {
            this.showToast('Failed to refresh token: ' + error.message, 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = '<span class="btn-icon">🔄</span> Refresh C4 Token';
        }
    }

    // Token Management
    hideAddTokenModal() {
        document.getElementById('add-token-modal').style.display = 'none';
    }

    async saveToken() {
        const uuid = document.getElementById('token-uuid').value.trim();
        const name = document.getElementById('token-name').value.trim();

        if (!uuid || !name) {
            this.showToast('Please fill in all fields', 'error');
            return;
        }

        try {
            const response = await fetch('/api/tokens', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ uuid, name, active: true })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('Token registered successfully', 'success');
                this.hideAddTokenModal();
                await this.loadTokens();
            } else {
                this.showToast(data.message || 'Failed to register token', 'error');
            }
        } catch (error) {
            this.showToast('Failed to register token', 'error');
        }
    }

    async deleteToken(uuid) {
        if (!confirm('Are you sure you want to delete this token?')) {
            return;
        }

        try {
            const response = await fetch(`/api/tokens/${encodeURIComponent(uuid)}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('Token deleted successfully', 'success');
                await this.loadTokens();
            } else {
                this.showToast(data.message || 'Failed to delete token', 'error');
            }
        } catch (error) {
            this.showToast('Failed to delete token', 'error');
        }
    }

    // Activity Log
    async clearLog() {
        if (!confirm('Are you sure you want to clear the activity log?')) {
            return;
        }

        try {
            const response = await fetch('/api/activity', {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('Activity log cleared', 'success');
                await this.loadActivity();
            } else {
                this.showToast('Failed to clear log', 'error');
            }
        } catch (error) {
            this.showToast('Failed to clear log', 'error');
        }
    }
    
    async loadActivityMode() {
        try {
            const response = await fetch('/api/activity/mode');
            const data = await response.json();
            
            const toggle = document.getElementById('activity-mode-toggle');
            const label = document.getElementById('activity-mode-label');
            const hint = document.getElementById('activity-mode-hint');
            
            toggle.checked = data.suppress_mode;
            
            if (data.suppress_mode) {
                label.textContent = 'Suppress Mode';
                hint.textContent = 'Updates existing token entries';
            } else {
                label.textContent = 'Extended Mode';
                hint.textContent = 'Shows all token detection events';
            }
        } catch (error) {
            console.error('Failed to load activity mode:', error);
        }
    }
    
    async toggleActivityMode(suppressMode) {
        try {
            const response = await fetch('/api/activity/mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ suppress_mode: suppressMode })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const label = document.getElementById('activity-mode-label');
                const hint = document.getElementById('activity-mode-hint');
                
                if (suppressMode) {
                    label.textContent = 'Suppress Mode';
                    hint.textContent = 'Updates existing token entries';
                } else {
                    label.textContent = 'Extended Mode';
                    hint.textContent = 'Shows all token detection events';
                }
                
                this.showToast(`Activity log mode: ${data.mode}`, 'success');
                await this.loadActivity();
            } else {
                this.showToast('Failed to toggle activity mode', 'error');
            }
        } catch (error) {
            this.showToast('Failed to toggle activity mode', 'error');
        }
    }

    // Statistics
    async runStats() {
        const button = document.getElementById('btn-run-stats');
        const container = document.getElementById('stats-container');
        
        button.disabled = true;
        button.textContent = '⏳ Gathering stats...';
        container.innerHTML = '<div class="loading">Gathering statistics from logs... This may take a few seconds...</div>';
        
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            if (data.success) {
                this.renderStats(data.stats);
                this.showToast('Statistics loaded successfully', 'success');
            } else {
                this.showToast('Failed to load statistics', 'error');
            }
        } catch (error) {
            console.error('Failed to run stats:', error);
            this.showToast('Failed to run statistics', 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = '<span class="btn-icon">📊</span> Run Detection Stats';
        }
    }
    
    renderStats(stats) {
        const container = document.getElementById('stats-container');
        
        const bleTotal = stats.ble_scanner.total;
        const bcgTotal = stats.bcg04.total_requests;
        const gateOpens = stats.gate_opens.total;
        
        let html = `
            <div class="stats-summary">
                <h3>Summary for ${stats.date}</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">BLE Scanner</div>
                        <div class="stat-value">${bleTotal}</div>
                        <div class="stat-desc">Total Detections</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">BCG04 Gateway</div>
                        <div class="stat-value">${bcgTotal}</div>
                        <div class="stat-desc">Total Requests</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Gate Opens</div>
                        <div class="stat-value">${gateOpens}</div>
                        <div class="stat-desc">Successful Opens</div>
                    </div>
                </div>
            </div>
            
            <div class="stats-comparison">
                <h3>📊 Comparison: BLE vs BCG04 (Today)</h3>
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>BLE Scanner</th>
                            <th>BCG04 Gateway</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Total Activity</strong></td>
                            <td>${bleTotal} detections</td>
                            <td>${bcgTotal} requests</td>
                        </tr>
                        <tr>
                            <td><strong>Gate Triggers</strong></td>
                            <td>✅ ${gateOpens}</td>
                            <td>❌ 0</td>
                        </tr>
                        <tr>
                            <td><strong>Success Rate</strong></td>
                            <td>${bleTotal > 0 ? '100%' : '0%'}</td>
                            <td>${stats.bcg04.empty_batches === bcgTotal ? '0% (filtered)' : 'N/A'}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
        
        // Add BLE scanner by token
        if (Object.keys(stats.ble_scanner.by_token).length > 0) {
            html += `
                <div class="stats-detail">
                    <h4>BLE Scanner Detections by Token</h4>
                    <table class="stats-table">
                        <thead>
                            <tr>
                                <th>Token</th>
                                <th>Detections</th>
                                <th>% of Total</th>
                            </tr>
                        </thead>
                        <tbody>`;
            
            for (const [token, count] of Object.entries(stats.ble_scanner.by_token)) {
                const percent = ((count / bleTotal) * 100).toFixed(1);
                html += `
                    <tr>
                        <td>${this.escapeHtml(token)}</td>
                        <td>${count}</td>
                        <td>${percent}%</td>
                    </tr>`;
            }
            
            html += `
                        </tbody>
                    </table>
                </div>`;
        }
        
        // Add gate opens by token
        if (Object.keys(stats.gate_opens.by_token).length > 0) {
            html += `
                <div class="stats-detail">
                    <h4>Gate Opens by Token</h4>
                    <table class="stats-table">
                        <thead>
                            <tr>
                                <th>Token</th>
                                <th>Opens</th>
                            </tr>
                        </thead>
                        <tbody>`;
            
            for (const [token, count] of Object.entries(stats.gate_opens.by_token)) {
                html += `
                    <tr>
                        <td>${this.escapeHtml(token)}</td>
                        <td>${count}</td>
                    </tr>`;
            }
            
            html += `
                        </tbody>
                    </table>
                </div>`;
        }
        
        container.innerHTML = html;
    }
    
    async loadNotes() {
        try {
            const response = await fetch('/api/stats/notes');
            const data = await response.json();
            
            if (data.success) {
                this.renderNotes(data.notes);
            }
        } catch (error) {
            console.error('Failed to load notes:', error);
        }
    }
    
    renderNotes(notes) {
        const container = document.getElementById('notes-container');
        
        if (notes.length === 0) {
            container.innerHTML = '<div class="empty-state">No notes yet. Add a note to mark BCG04 location changes or other important events.</div>';
            return;
        }
        
        container.innerHTML = notes.reverse().map(note => {
            const time = new Date(note.timestamp).toLocaleString();
            return `
                <div class="note-item">
                    <div class="note-header">
                        <strong>${this.escapeHtml(note.label)}</strong>
                        <span class="note-time">${time}</span>
                    </div>
                    <div class="note-body">${this.escapeHtml(note.note)}</div>
                </div>
            `;
        }).join('');
    }
    
    showAddNoteModal() {
        document.getElementById('note-label').value = '';
        document.getElementById('note-text').value = '';
        document.getElementById('add-note-modal').style.display = 'flex';
    }
    
    hideAddNoteModal() {
        document.getElementById('add-note-modal').style.display = 'none';
    }
    
    async saveNote() {
        const label = document.getElementById('note-label').value.trim();
        const note = document.getElementById('note-text').value.trim();
        
        if (!label) {
            this.showToast('Please enter a label', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/stats/notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ label, note })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Note added successfully', 'success');
                this.hideAddNoteModal();
                await this.loadNotes();
            } else {
                this.showToast('Failed to add note', 'error');
            }
        } catch (error) {
            console.error('Failed to save note:', error);
            this.showToast('Failed to add note', 'error');
        }
    }

    // Utilities
    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast toast-${type} show`;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    // Scan Controls
    startScan() {
        this.isScanning = true;
        document.getElementById('btn-start-scan').disabled = true;
        document.getElementById('btn-stop-scan').disabled = false;
        this.showToast('Manual scan started', 'info');
    }

    stopScan() {
        this.isScanning = false;
        document.getElementById('btn-start-scan').disabled = false;
        document.getElementById('btn-stop-scan').disabled = true;
        this.showToast('Manual scan stopped', 'info');
    }

    // Config Edit/Save
    async saveConfig() {
        const config = {
            auto_close_timeout: parseInt(document.getElementById('input-auto-close').value),
            session_timeout: parseInt(document.getElementById('input-session-timeout').value),
            status_check_interval: parseInt(document.getElementById('input-status-interval').value),
            ble_scan_interval: parseInt(document.getElementById('input-scan-interval').value)
        };

        try {
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('Configuration saved successfully', 'success');
                this.isEditingConfig = false;
                this.toggleConfigEdit(false);
                this.config = null; // Clear cached config to force reload
                await this.loadConfig();
                
                // Ask user if they want to restart the service
                if (confirm('Configuration saved. Would you like to restart the service now for changes to take effect?')) {
                    await this.restartService();
                }
            } else {
                this.showToast(data.message || 'Failed to save configuration', 'error');
            }
        } catch (error) {
            this.showToast('Failed to save configuration', 'error');
        }
    }

    async restartService() {
        try {
            const response = await fetch('/api/service/restart', {
                method: 'POST'
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('Service restart initiated. Dashboard will reconnect automatically.', 'success');
            } else {
                this.showToast(data.message || 'Failed to restart service', 'error');
            }
        } catch (error) {
            this.showToast('Failed to restart service. Please restart manually.', 'error');
        }
    }

    cancelConfigEdit() {
        this.isEditingConfig = false;
        this.toggleConfigEdit(false);
        this.renderConfig(this.config);
    }

    toggleConfigEdit(enable) {
        // Toggle visibility of edit/save buttons
        document.getElementById('btn-save-config').style.display = enable ? 'inline-flex' : 'none';
        document.getElementById('btn-cancel-config').style.display = enable ? 'inline-block' : 'none';

        // Toggle visibility of values and inputs
        const configValues = document.querySelectorAll('.config-value');
        const configInputs = document.querySelectorAll('.config-input');
        
        configValues.forEach(el => el.style.display = enable ? 'none' : 'block');
        configInputs.forEach(el => el.style.display = enable ? 'block' : 'none');

        if (enable) {
            // Populate inputs with current values
            document.getElementById('input-auto-close').value = this.config.gate.auto_close_timeout;
            document.getElementById('input-session-timeout').value = this.config.gate.session_timeout;
            document.getElementById('input-status-interval').value = this.config.gate.status_check_interval;
            document.getElementById('input-scan-interval').value = this.config.gate.ble_scan_interval;
        }
    }

    // Periodic Refresh
    startPeriodicRefresh() {
        // Refresh token status every 5 seconds
        this.refreshIntervals.tokens = setInterval(() => {
            this.loadTokens();
        }, 5000);

        // Refresh activity log every 10 seconds
        this.refreshIntervals.activity = setInterval(() => {
            this.loadActivity();
        }, 10000);

        // Update detected tokens display every 5 seconds
        this.refreshIntervals.detected = setInterval(() => {
            if (this.detectedTokens.size > 0) {
                this.renderDetectedTokens();
            }
        }, 5000);
    }

    // Scan All Devices
    async scanAllDevices() {
        if (this.isScanningAll) {
            this.showToast('Scan already in progress', 'warning');
            return;
        }

        const btn = document.getElementById('btn-scan-all');
        const originalText = btn.innerHTML;
        
        try {
            this.isScanningAll = true;
            btn.disabled = true;
            btn.innerHTML = '<span class="btn-icon">🔄</span> Scanning...';
            
            this.showToast('Scanning for all BLE devices...', 'info');
            
            const response = await fetch('/api/scan/all?duration=10', {
                method: 'GET'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.scannedDevices = {
                    ibeacons: data.ibeacons || [],
                    devices: data.devices || []
                };
                this.showScanResultsModal();
                this.showToast(`Found ${data.total} device(s)`, 'success');
            } else {
                this.showToast('Scan failed', 'error');
            }
        } catch (error) {
            console.error('Scan error:', error);
            this.showToast('Failed to scan devices', 'error');
        } finally {
            this.isScanningAll = false;
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }

    showScanResultsModal() {
        const modal = document.getElementById('scan-results-modal');
        const ibeaconList = document.getElementById('scan-ibeacon-list');
        const deviceList = document.getElementById('scan-device-list');

        // Render iBeacons
        if (this.scannedDevices.ibeacons.length === 0) {
            ibeaconList.innerHTML = '<div class="empty-state">No iBeacons found</div>';
        } else {
            ibeaconList.innerHTML = this.scannedDevices.ibeacons.map(beacon => `
                <div class="scan-result-item">
                    <div class="scan-result-info">
                        <div class="scan-result-name">${this.escapeHtml(beacon.name || 'Unknown iBeacon')}</div>
                        <div class="scan-result-details">
                            UUID: ${this.escapeHtml(beacon.uuid)}<br>
                            ${beacon.rssi ? `RSSI: ${beacon.rssi} dBm` : ''}
                            ${beacon.distance ? ` | ~${beacon.distance}m` : ''}
                        </div>
                    </div>
                    <button class="btn btn-sm btn-primary" onclick="dashboard.registerScannedToken('${this.escapeHtml(beacon.uuid)}', '${this.escapeHtml(beacon.name || 'iBeacon')}')">
                        Register
                    </button>
                </div>
            `).join('');
        }

        // Render regular devices
        if (this.scannedDevices.devices.length === 0) {
            deviceList.innerHTML = '<div class="empty-state">No regular BLE devices found</div>';
        } else {
            deviceList.innerHTML = this.scannedDevices.devices.map(device => `
                <div class="scan-result-item">
                    <div class="scan-result-info">
                        <div class="scan-result-name">${this.escapeHtml(device.name || 'Unknown Device')}</div>
                        <div class="scan-result-details">
                            ${this.escapeHtml(device.address)}
                            ${device.rssi ? ` | RSSI: ${device.rssi} dBm` : ''}
                        </div>
                    </div>
                </div>
            `).join('');
        }

        modal.style.display = 'flex';
    }

    hideScanResultsModal() {
        document.getElementById('scan-results-modal').style.display = 'none';
    }

    async registerScannedToken(uuid, name) {
        // Close scan results and open add token modal with pre-filled data
        this.hideScanResultsModal();
        this.showAddTokenModal(uuid, name);
    }

    // Edit Token
    showEditTokenModal(token) {
        if (!token) return;
        
        this.editingToken = token;
        document.getElementById('edit-token-name').value = token.name;
        document.getElementById('edit-token-active').checked = token.active !== undefined ? token.active : true;
        document.getElementById('edit-token-uuid-display').textContent = token.uuid;
        document.getElementById('edit-token-modal').style.display = 'flex';
    }

    hideEditTokenModal() {
        document.getElementById('edit-token-modal').style.display = 'none';
        this.editingToken = null;
    }

    async saveTokenEdit() {
        if (!this.editingToken) return;

        const name = document.getElementById('edit-token-name').value.trim();
        const active = document.getElementById('edit-token-active').checked;

        if (!name) {
            this.showToast('Please enter a token name', 'error');
            return;
        }

        try {
            const response = await fetch(`/api/tokens/${this.editingToken.uuid}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, active })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('Token updated successfully', 'success');
                this.hideEditTokenModal();
                await this.loadTokens();
            } else {
                this.showToast(data.message || 'Failed to update token', 'error');
            }
        } catch (error) {
            console.error('Update error:', error);
            this.showToast('Failed to update token', 'error');
        }
    }

    // Smart Add Token with Scan
    async scanBeaconsForAdd() {
        const btn = document.getElementById('btn-scan-beacons');
        const scanList = document.getElementById('add-scan-list');
        const originalText = btn.innerHTML;

        try {
            btn.disabled = true;
            btn.innerHTML = '<span class="btn-icon">🔄</span> Scanning...';
            scanList.innerHTML = '<div class="empty-state">Scanning for iBeacons...</div>';

            const response = await fetch('/api/scan/all?duration=10', {
                method: 'GET'
            });

            const data = await response.json();

            if (data.success && data.ibeacons.length > 0) {
                scanList.innerHTML = data.ibeacons.map(beacon => `
                    <div class="scan-result-item scan-result-selectable" data-uuid="${this.escapeHtml(beacon.uuid)}" data-name="${this.escapeHtml(beacon.name || 'iBeacon')}">
                        <div class="scan-result-info">
                            <div class="scan-result-name">${this.escapeHtml(beacon.name || 'Unknown iBeacon')}</div>
                            <div class="scan-result-details">
                                ${this.escapeHtml(beacon.uuid)}<br>
                                ${beacon.rssi ? `RSSI: ${beacon.rssi} dBm` : ''}
                                ${beacon.distance ? ` | ~${beacon.distance}m` : ''}
                            </div>
                        </div>
                    </div>
                `).join('');

                // Add click handlers
                scanList.querySelectorAll('.scan-result-selectable').forEach(item => {
                    item.addEventListener('click', (e) => {
                        const uuid = e.currentTarget.dataset.uuid;
                        const name = e.currentTarget.dataset.name;
                        document.getElementById('token-uuid').value = uuid;
                        document.getElementById('token-name').value = name;
                    });
                });
            } else {
                scanList.innerHTML = '<div class="empty-state">No iBeacons found. You can still enter UUID manually.</div>';
            }
        } catch (error) {
            console.error('Scan error:', error);
            scanList.innerHTML = '<div class="empty-state">Scan failed. Please enter UUID manually.</div>';
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }

    // Update showAddTokenModal to support pre-filled data
    showAddTokenModal(uuid = '', name = '') {
        document.getElementById('token-uuid').value = uuid;
        document.getElementById('token-name').value = name;
        document.getElementById('add-scan-list').innerHTML = '<div class="empty-state">Click "Scan for iBeacons" to find nearby devices</div>';
        document.getElementById('add-token-modal').style.display = 'flex';
    }

    // Utilities
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
    
    // Update detected tokens display every 10 seconds
    setInterval(() => {
        if (window.dashboard.detectedTokens.size > 0) {
            window.dashboard.renderDetectedTokens();
        }
    }, 10000);
});
