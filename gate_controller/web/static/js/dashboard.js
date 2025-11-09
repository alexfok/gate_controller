// Gate Controller Dashboard - Phase 4

class Dashboard {
    constructor() {
        this.ws = null;
        this.reconnectInterval = null;
        this.detectedTokens = new Map(); // Track detected tokens with timestamps
        this.filteredTokens = [];
        this.config = null;
        this.init();
    }

    init() {
        this.setupTabs();
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadInitialData();
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

        // Load tab-specific data
        if (tabName === 'config') {
            this.loadConfig();
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

        // Token management
        document.getElementById('btn-add-token').addEventListener('click', () => this.showAddTokenModal());
        document.getElementById('modal-close').addEventListener('click', () => this.hideAddTokenModal());
        document.getElementById('modal-cancel').addEventListener('click', () => this.hideAddTokenModal());
        document.getElementById('modal-save').addEventListener('click', () => this.saveToken());

        // Token filter
        const filterInput = document.getElementById('token-filter');
        filterInput.addEventListener('input', (e) => this.filterTokens(e.target.value));
        document.getElementById('btn-clear-filter').addEventListener('click', () => {
            filterInput.value = '';
            this.filterTokens('');
        });

        // Activity log
        document.getElementById('btn-clear-log').addEventListener('click', () => this.clearLog());

        // Close modal on outside click
        document.getElementById('add-token-modal').addEventListener('click', (e) => {
            if (e.target.id === 'add-token-modal') {
                this.hideAddTokenModal();
            }
        });
    }

    // Data Loading
    async loadInitialData() {
        await Promise.all([
            this.loadStatus(),
            this.loadTokens(),
            this.loadActivity()
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

        container.innerHTML = tokens.map(token => `
            <div class="token-item">
                <div class="token-info">
                    <div class="token-name">${this.escapeHtml(token.name)}</div>
                    <div class="token-uuid">${this.escapeHtml(token.uuid)}</div>
                </div>
                <button class="btn-delete" data-uuid="${this.escapeHtml(token.uuid)}">
                    🗑️
                </button>
            </div>
        `).join('');

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
            
            return `
                <div class="activity-item activity-${typeClass}">
                    <div class="activity-time">${time}</div>
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

        // Gate behavior
        document.getElementById('config-auto-close').textContent = 
            config.gate.auto_close_timeout ? `${config.gate.auto_close_timeout}s (${Math.floor(config.gate.auto_close_timeout / 60)}m)` : '-';
        document.getElementById('config-session-timeout').textContent = 
            config.gate.session_timeout ? `${config.gate.session_timeout}s (${Math.floor(config.gate.session_timeout / 60)}m)` : '-';
        document.getElementById('config-status-interval').textContent = 
            config.gate.status_check_interval ? `${config.gate.status_check_interval}s` : '-';
        document.getElementById('config-scan-interval').textContent = 
            config.gate.ble_scan_interval ? `${config.gate.ble_scan_interval}s` : '-';
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

    // Token Management
    showAddTokenModal() {
        document.getElementById('add-token-modal').style.display = 'flex';
        document.getElementById('token-uuid').value = '';
        document.getElementById('token-name').value = '';
        document.getElementById('token-uuid').focus();
    }

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
                body: JSON.stringify({ uuid, name })
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

    // Utilities
    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast toast-${type} show`;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

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
