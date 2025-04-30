// Initialize Socket.IO connection
const socket = io();

// DOM Elements
const botStatus = document.getElementById('bot-status');
const botRuntime = document.getElementById('bot-runtime');
const marketStatus = document.getElementById('market-status');
const alpacaAccountId = document.getElementById('alpaca-account-id');
const alpacaBuyingPower = document.getElementById('alpaca-buying-power');
const alpacaEquity = document.getElementById('alpaca-equity');
const alpacaLastUpdate = document.getElementById('alpaca-last-update');
const totalTrades = document.getElementById('total-trades');
const winRate = document.getElementById('win-rate');
const avgReturn = document.getElementById('avg-return');
const currentStrategy = document.getElementById('current-strategy');
const initialCapital = document.getElementById('initial-capital');
const currentCapital = document.getElementById('current-capital');
const activePositions = document.getElementById('active-positions');
const totalReturn = document.getElementById('total-return');
const positionsContainer = document.getElementById('positions-container');
const logs = document.getElementById('logs');
const startBotBtn = document.getElementById('start-bot');
const stopBotBtn = document.getElementById('stop-bot');
const errorMessage = document.getElementById('error-message');

// Charts
let returnsChart = null;
let positionsChart = null;

// Bot state
let botRunning = false;
let botStartTime = null;
let runtimeInterval = null;

// Utility Functions
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
}

function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', { style: 'percent', minimumFractionDigits: 2 }).format(value / 100);
}

function formatDateTime(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'short'
    }).format(new Date(date));
}

function formatRuntime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Logging Functions
function addLog(message, type = 'info') {
    if (!logs) return;
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.innerHTML = `
        <span class="log-timestamp">${formatDateTime(new Date())}</span>
        <span class="log-message">${message}</span>
    `;
    logs.insertBefore(logEntry, logs.firstChild);
    if (logs.children.length > 100) {
        logs.removeChild(logs.lastChild);
    }
}

function logRequest(method, url, data) {
    addLog(`${method} ${url} ${JSON.stringify(data)}`, 'request');
}

function logResponse(method, url, response, data) {
    addLog(`${method} ${url} Response: ${JSON.stringify(data)}`, 'response');
}

function logError(method, url, error) {
    addLog(`Error in ${method} ${url}: ${error.message}`, 'error');
    showError(error.message);
}

function showError(message) {
    if (!errorMessage) return;
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

// Chart Initialization
function initializeCharts() {
    try {
        addLog('Initializing charts...');
        const returnsCtx = document.getElementById('returns-chart');
        const positionsCtx = document.getElementById('positions-chart');

        if (!returnsCtx || !positionsCtx) {
            addLog('Chart elements not found', 'error');
            return;
        }

        // Returns Chart
        returnsChart = new Chart(returnsCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Returns',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: value => formatPercentage(value)
                        }
                    }
                }
            }
        });

        // Positions Chart
        positionsChart = new Chart(positionsCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: []
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });

        addLog('Charts initialized successfully');
    } catch (error) {
        addLog(`Error initializing charts: ${error.message}`, 'error');
    }
}

function updateBotRuntime(runtime) {
    if (!botRuntime) return;
    if (typeof runtime === 'string') {
        botRuntime.textContent = runtime;
    } else {
        const hours = Math.floor(runtime / 3600);
        const minutes = Math.floor((runtime % 3600) / 60);
        const seconds = runtime % 60;
        botRuntime.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}

function updateAlpacaAccountInfo(data) {
    if (!data) return;
    
    if (alpacaAccountId) alpacaAccountId.textContent = data.account_id || 'N/A';
    if (alpacaBuyingPower) alpacaBuyingPower.textContent = formatCurrency(parseFloat(data.buying_power || 0));
    if (alpacaEquity) alpacaEquity.textContent = formatCurrency(parseFloat(data.equity || 0));
    if (alpacaLastUpdate) alpacaLastUpdate.textContent = formatDateTime(new Date());

    // Update performance metrics
    if (initialCapital) initialCapital.textContent = formatCurrency(parseFloat(data.equity || 0));
    if (currentCapital) currentCapital.textContent = formatCurrency(parseFloat(data.equity || 0));
    
    if (totalReturn && data.equity && data.cash) {
        const returnValue = ((parseFloat(data.equity) - parseFloat(data.cash)) / parseFloat(data.cash)) * 100;
        totalReturn.textContent = formatPercentage(returnValue);
    }
}

function updatePositions(positions) {
    if (!positions) return;
    
    // Update active positions count
    if (activePositions) activePositions.textContent = positions.length;

    // Clear and update positions container
    if (positionsContainer) {
        positionsContainer.innerHTML = '';
        
        if (positions.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'text-muted text-center p-3';
            emptyMessage.textContent = 'No active positions';
            positionsContainer.appendChild(emptyMessage);
        } else {
            positions.forEach((position, index) => {
                const card = document.createElement('div');
                card.className = 'position-card mb-3';
                const unrealizedPL = parseFloat(position.unrealized_pl || 0);
                const plClass = unrealizedPL >= 0 ? 'text-success' : 'text-danger';
                
                card.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">${position.symbol}</h6>
                        <span class="badge ${position.quantity > 0 ? 'bg-success' : 'bg-danger'}">
                            ${position.quantity > 0 ? 'LONG' : 'SHORT'}
                        </span>
                    </div>
                    <div class="position-details">
                        <div class="row">
                            <div class="col">
                                <small>Quantity</small>
                                <div>${Math.abs(position.quantity)}</div>
                            </div>
                            <div class="col">
                                <small>Market Value</small>
                                <div>${formatCurrency(parseFloat(position.market_value || 0))}</div>
                            </div>
                            <div class="col">
                                <small>Current Price</small>
                                <div>${formatCurrency(parseFloat(position.current_price || 0))}</div>
                            </div>
                            <div class="col">
                                <small>P/L</small>
                                <div class="${plClass}">${formatCurrency(unrealizedPL)}</div>
                            </div>
                        </div>
                    </div>
                `;
                positionsContainer.appendChild(card);
            });
        }
    }

    // Update positions chart
    if (positionsChart) {
        const labels = positions.map(p => p.symbol);
        const values = positions.map(p => Math.abs(parseFloat(p.market_value || 0)));
        const colors = positions.map((_, i) => `hsl(${(i * 360) / positions.length}, 70%, 50%)`);

        positionsChart.data.labels = labels;
        positionsChart.data.datasets[0].data = values;
        positionsChart.data.datasets[0].backgroundColor = colors;
        positionsChart.update();
    }
}

function updateMarketStatus(status) {
    if (!marketStatus || !status) return;
    const isOpen = status === 'open' || status.is_open;
    marketStatus.textContent = isOpen ? 'OPEN' : 'CLOSED';
    marketStatus.className = `status-badge ${isOpen ? 'bg-success' : 'bg-danger'}`;
}

function updateBotStatus(status) {
    if (!botStatus || !status) return;
    const isRunning = status === 'running' || status === 'RUNNING';
    botStatus.textContent = isRunning ? 'RUNNING' : 'STOPPED';
    botStatus.className = `status-badge ${isRunning ? 'bg-success' : 'bg-secondary'}`;
    
    if (startBotBtn) startBotBtn.disabled = isRunning;
    if (stopBotBtn) stopBotBtn.disabled = !isRunning;
}

function updateMarketHours(marketStatus) {
    const marketHoursInfo = document.getElementById('market-hours-info');
    if (!marketHoursInfo) return;
    
    if (marketStatus.is_open) {
        const closeTime = new Date(marketStatus.next_close);
        if (closeTime instanceof Date && !isNaN(closeTime)) {
            marketHoursInfo.textContent = `Market is open until ${closeTime.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit',
                timeZoneName: 'short'
            })}`;
            marketHoursInfo.className = 'text-success';
        } else {
            marketHoursInfo.textContent = 'Market is open';
            marketHoursInfo.className = 'text-success';
        }
    } else {
        const nextOpen = new Date(marketStatus.next_open);
        if (nextOpen instanceof Date && !isNaN(nextOpen)) {
            marketHoursInfo.textContent = `Market opens at ${nextOpen.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit',
                timeZoneName: 'short'
            })} on ${nextOpen.toLocaleDateString('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric'
            })}`;
            marketHoursInfo.className = 'text-danger';
        } else {
            marketHoursInfo.textContent = 'Market is closed';
            marketHoursInfo.className = 'text-danger';
        }
    }
}

function updateRuntime() {
    if (botStartTime) {
        const runtimeElement = document.getElementById('runtime-counter');
        const now = new Date();
        const runtime = Math.floor((now - botStartTime) / 1000);
        runtimeElement.querySelector('span').textContent = formatRuntime(runtime);
    }
}

// Socket Event Handlers
socket.on('connect', () => {
    addLog('Connected to server');
    socket.emit('get_initial_status');
});

socket.on('disconnect', () => {
    addLog('Disconnected from server', 'error');
    updateBotStatus('stopped');
});

socket.on('status_update', (data) => {
    if (!data) return;
    
    updateBotStatus(data.status);
    updateMarketStatus(data.market_status);
    if (data.runtime) updateBotRuntime(data.runtime);
    if (data.account) updateAlpacaAccountInfo(data.account);
    if (data.positions) updatePositions(data.positions);
    if (data.error) showError(data.error);
    
    // Update metrics if available
    if (data.metrics) {
        if (totalTrades) totalTrades.textContent = data.metrics.total_trades || '0';
        if (winRate) winRate.textContent = `${data.metrics.win_rate || 0}%`;
        if (avgReturn) avgReturn.textContent = `${data.metrics.avg_return || 0}%`;
    }
    
    // Update portfolio history chart if available
    if (data.portfolio_history && returnsChart) {
        returnsChart.data.labels = data.portfolio_history.timestamp || [];
        returnsChart.data.datasets[0].data = data.portfolio_history.profit_loss_pct || [];
        returnsChart.update();
    }

    if (data.market_status) {
        updateMarketHours(data.market_status);
    }
});

// Event Listeners
if (startBotBtn) {
    startBotBtn.addEventListener('click', () => {
        fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addLog(`Error: ${data.error}`, 'error');
                showError(data.error);
                if (data.market_status) {
                    updateMarketStatus(data.market_status.is_open ? 'open' : 'closed');
                    updateMarketHours(data.market_status);
                }
            } else {
                addLog('Bot started successfully');
                botRunning = true;
                botStartTime = new Date();
                startBotBtn.disabled = true;
                stopBotBtn.disabled = false;
                updateBotStatus('RUNNING');
                const runtimeElement = document.getElementById('runtime-counter');
                runtimeElement.style.display = 'flex';
                runtimeInterval = setInterval(updateRuntime, 1000);
                updateRuntime();
            }
        })
        .catch(error => {
            addLog(`Error starting bot: ${error.message}`, 'error');
            showError('Failed to start bot');
        });
    });
}

if (stopBotBtn) {
    stopBotBtn.addEventListener('click', () => {
        fetch('/api/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addLog('Bot stopped successfully');
                updateBotStatus('stopped');
                botStartTime = null;
                const runtimeElement = document.getElementById('runtime-counter');
                runtimeElement.style.display = 'none';
                if (runtimeInterval) {
                    clearInterval(runtimeInterval);
                    runtimeInterval = null;
                }
            } else {
                throw new Error(data.error || 'Failed to stop bot');
            }
        })
        .catch(error => {
            addLog(`Failed to stop bot: ${error.message}`, 'error');
            showError(error.message);
        });
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    try {
        addLog('Initializing application...');
        initializeCharts();
        
        // Initial data fetch
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateBotStatus(data.status);
                    updateMarketStatus(data.market_status);
                    if (data.account) updateAlpacaAccountInfo(data.account);
                    if (data.positions) updatePositions(data.positions);
                    addLog('Initial status loaded successfully');
                } else {
                    throw new Error(data.error || 'Failed to load initial status');
                }
            })
            .catch(error => {
                addLog(`Error loading initial status: ${error.message}`, 'error');
                showError(error.message);
            });
        
        // Set up periodic data refresh
        setInterval(() => {
            if (socket.connected) {
                socket.emit('get_initial_status');
            }
        }, 5000);
    } catch (error) {
        addLog(`Error during initialization: ${error.message}`, 'error');
        showError('Error initializing application');
    }
}); 