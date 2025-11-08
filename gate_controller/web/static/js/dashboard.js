// Gate Controller Dashboard

class Dashboard {
    constructor() {
        this.ws = null;
        this.reconnectInterval = null;
        this.init();
    }

    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadInitialData();
    }

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
        console.log('WebSocket message:', message);
        
        switch (message.type) {
            case 'status':
                this.updateGateStatus(message.data);
                break;
            case 'gate_opened':
                this.showToast('Gate opened: ' + (message.data.reason || 'Unknown'), 'success');
                this.loadActivity();
                this.loadStatus();
                break;
            case 'gate_closed':
                this.showToast('Gate closed: ' + (message.data.reason || 'Unknown'), 'success');
                this.loadActivity();
                this.loadStatus();
                break;
            case 'token_detected':
                this.showToast(`Token detected: ${message.data.name}`, 'success');
                this.loadTokens();
                this.loadActivity();
                break;
            case 'token_registered':
                this.showToast(`Token registered: ${message.data.name}`, 'success');
                this.loadTokens();
                this.loadActivity();
                break;
            case 'token_unregistered':
                this.showToast('Token unregistered', 'success');
                this.loadTokens();
                this.loadActivity();
                break;
            case 'activity_cleared':
                this.loadActivity();
                break;
        }
    }

    setupEventListeners() {
        // Gate controls
        document.getElementById('btn-open-gate').addEventListener('click', () => this.openGate());
        document.getElementById('btn-close-gate').addEventListener('click', () => this.closeGate());
        
        // Token management
        document.getElementById('btn-add-token').addEventListener('click', () => this.showAddTokenModal());
        
        // Modal controls
        document.getElementById('modal-close').addEventListener('click', () => this.hideAddTokenModal());
        document.getElementById('modal-cancel').addEventListener('click', () => this.hideAddTokenModal());
        document.getElementById('modal-save').addEventListener('click', () => this.saveToken());
        
        // Activity log
        document.getElementById('btn-clear-log').addEventListener('click', () => this.clearActivity());
        
        // Modal backdrop click
        document.getElementById('add-token-modal').addEventListener('click', (e) => {
            if (e.target.id === 'add-token-modal') {
                this.hideAddTokenModal();
            }
        });
        
        // Enter key in modal
        document.getElementById('token-name').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.saveToken();
            }
        });
    }

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
            document.getElementById('token-list').innerHTML = '<div class="empty-state">Failed to load tokens</div>';
        }
    }

    async loadActivity() {
        try {
            const response = await fetch('/api/activity?limit=50');
            const data = await response.json();
            this.renderActivity(data.entries);
        } catch (error) {
            console.error('Failed to load activity:', error);
            document.getElementById('activity-log').innerHTML = '<div class="empty-state">Failed to load activity</div>';
        }
    }

    updateControllerStatus(online) {
        const badge = document.getElementById('controller-status');
        const text = badge.querySelector('.status-text');
        
        if (online) {
            badge.classList.add('online');
            badge.classList.remove('offline');
            text.textContent = 'Connected';
        } else {
            badge.classList.remove('online');
            badge.classList.add('offline');
            text.textContent = 'Disconnected';
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
        
        if (!tokens || tokens.length === 0) {
            container.innerHTML = '<div class="empty-state">No tokens registered</div>';
            return;
        }
        
        container.innerHTML = tokens.map(token => `
            <div class="token-item">
                <div class="token-info">
                    <div class="token-name">${this.escapeHtml(token.name)}</div>
                    <div class="token-uuid">${this.escapeHtml(token.uuid)}</div>
                </div>
                <button class="btn-delete" onclick="dashboard.deleteToken('${this.escapeHtml(token.uuid)}')">Delete</button>
            </div>
        `).join('');
    }

    renderActivity(entries) {
        const container = document.getElementById('activity-log');
        
        if (!entries || entries.length === 0) {
            container.innerHTML = '<div class="empty-state">No activity logged</div>';
            return;
        }
        
        container.innerHTML = entries.map(entry => {
            const time = new Date(entry.timestamp).toLocaleString();
            return `
                <div class="activity-item ${entry.type}">
                    <div class="activity-time">${time}</div>
                    <div class="activity-message">
                        ${this.escapeHtml(entry.message)}
                        <span class="activity-type">${entry.type}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    async openGate() {
        try {
            const btn = document.getElementById('btn-open-gate');
            btn.disabled = true;
            
            const response = await fetch('/api/gate/open', { method: 'POST' });
            const data = await response.json();
            
            if (response.ok) {
                this.showToast(data.message, 'success');
            } else {
                this.showToast(data.detail || 'Failed to open gate', 'error');
            }
        } catch (error) {
            console.error('Failed to open gate:', error);
            this.showToast('Failed to open gate', 'error');
        } finally {
            setTimeout(() => {
                document.getElementById('btn-open-gate').disabled = false;
            }, 2000);
        }
    }

    async closeGate() {
        try {
            const btn = document.getElementById('btn-close-gate');
            btn.disabled = true;
            
            const response = await fetch('/api/gate/close', { method: 'POST' });
            const data = await response.json();
            
            if (response.ok) {
                this.showToast(data.message, 'success');
            } else {
                this.showToast(data.detail || 'Failed to close gate', 'error');
            }
        } catch (error) {
            console.error('Failed to close gate:', error);
            this.showToast('Failed to close gate', 'error');
        } finally {
            setTimeout(() => {
                document.getElementById('btn-close-gate').disabled = false;
            }, 2000);
        }
    }

    showAddTokenModal() {
        document.getElementById('add-token-modal').classList.add('active');
        document.getElementById('token-uuid').value = '';
        document.getElementById('token-name').value = '';
        document.getElementById('token-uuid').focus();
    }

    hideAddTokenModal() {
        document.getElementById('add-token-modal').classList.remove('active');
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
            
            if (response.ok) {
                this.showToast(data.message, 'success');
                this.hideAddTokenModal();
                this.loadTokens();
            } else {
                this.showToast(data.detail || 'Failed to register token', 'error');
            }
        } catch (error) {
            console.error('Failed to register token:', error);
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
            
            if (response.ok) {
                this.showToast(data.message, 'success');
                this.loadTokens();
            } else {
                this.showToast(data.detail || 'Failed to delete token', 'error');
            }
        } catch (error) {
            console.error('Failed to delete token:', error);
            this.showToast('Failed to delete token', 'error');
        }
    }

    async clearActivity() {
        if (!confirm('Are you sure you want to clear the activity log?')) {
            return;
        }
        
        try {
            const response = await fetch('/api/activity', { method: 'DELETE' });
            const data = await response.json();
            
            if (response.ok) {
                this.showToast(data.message, 'success');
                this.loadActivity();
            } else {
                this.showToast(data.detail || 'Failed to clear activity', 'error');
            }
        } catch (error) {
            console.error('Failed to clear activity:', error);
            this.showToast('Failed to clear activity', 'error');
        }
    }

    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type} show`;
        
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

// Initialize dashboard
const dashboard = new Dashboard();

