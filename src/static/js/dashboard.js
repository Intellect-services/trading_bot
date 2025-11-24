// Dashboard functionality
let socket;  // Global socket variable

// Chart instances
let portfolioChart = null;
let returnsChart = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing dashboard...');

    // Initialize UI elements
    const startButton = document.getElementById('startBot');
    const stopButton = document.getElementById('stopBot');
    const botStatusElement = document.getElementById('bot-status');
    const marketStatusElement = document.getElementById('market-status');
    const lastAnalysisElement = document.getElementById('last-analysis');
    const lastSignalElement = document.getElementById('last-signal');
    const activityLog = document.getElementById('activity-log');

    // Initialize Socket.IO connection
    socket = io();

    // Initialize charts
    initCharts();

    // Socket event handlers
    socket.on('connect', function() {
        console.log('Connected to server');
        socket.emit('get_initial_status');
    });

    socket.on('disconnect', function() {
        console.log('Disconnected from server');
    });

    socket.on('status_update', function(data) {
        console.log('Received status update:', data);
        try {
            if (data.error) {
                console.error('Error in status update:', data.error);
                return;
            }
            updateDashboard(data);
        } catch (error) {
            console.error('Error updating UI:', error);
        }
    });

    socket.on('error', function(data) {
        console.error('Socket error:', data);
        alert('Error: ' + data.message);
    });

    // Start/Stop button handlers
    startButton.addEventListener('click', function() {
        console.log('Starting bot...');
        fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Start response:', data);
            if (data.status === 'success') {
                startButton.disabled = true;
                stopButton.disabled = false;
                botStatusElement.textContent = 'RUNNING';
                botStatusElement.className = 'badge bg-success';
            } else {
                alert('Error starting bot: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error starting bot:', error);
            alert('Error starting bot: ' + error.message);
        });
    });

    stopButton.addEventListener('click', function() {
        console.log('Stopping bot...');
        fetch('/api/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Stop response:', data);
            if (data.status === 'success') {
                startButton.disabled = false;
                stopButton.disabled = true;
                botStatusElement.textContent = 'STOPPED';
                botStatusElement.className = 'badge bg-secondary';
            } else {
                alert('Error stopping bot: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error stopping bot:', error);
            alert('Error stopping bot: ' + error.message);
        });
    });
});

function initCharts() {
    // Portfolio Value Chart
    const portfolioCtx = document.getElementById('portfolioChart').getContext('2d');
    portfolioChart = new Chart(portfolioCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Portfolio Value',
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
                    beginAtZero: false
                }
            }
        }
    });

    // Returns Chart
    const returnsCtx = document.getElementById('returnsChart').getContext('2d');
    returnsChart = new Chart(returnsCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Daily Returns',
                data: [],
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgb(75, 192, 192)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
        statusElement.textContent = connected ? 'Connected' : 'Disconnected';
        statusElement.className = connected ? 'status-connected' : 'status-disconnected';
    }
}

function updateAccountInfo(account) {
    if (!account) return;

    console.log('Updating account info:', account);

    const elements = {
        'account-balance': account.portfolio_value || 0,
        'buying-power': account.buying_power || 0,
        'equity': account.equity || 0,
        'cash-balance': account.cash || 0
    };

    for (const [id, value] of Object.entries(elements)) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = formatCurrency(value);
            console.log(`Updated ${id} with value:`, value);
        } else {
            console.warn(`Element with id ${id} not found`);
        }
    }
}

function updatePositions(positions) {
    console.log('Updating positions:', positions);
    const tableBody = document.querySelector('#positionsTable tbody');
    if (!tableBody) {
        console.error('Positions table body not found');
        return;
    }

    if (!positions || positions.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" class="text-center">No open positions</td></tr>';
        return;
    }

    const rows = positions.map(position => {
        const unrealizedPl = parseFloat(position.unrealized_pl);
        const unrealizedPlPc = parseFloat(position.unrealized_plpc);
        return `
            <tr>
                <td>${position.symbol}</td>
                <td>${position.qty}</td>
                <td>${formatCurrency(position.current_price)}</td>
                <td>${formatCurrency(position.market_value)}</td>
                <td class="${unrealizedPl >= 0 ? 'text-success' : 'text-danger'}">
                    ${formatCurrency(unrealizedPl)} (${(unrealizedPlPc * 100).toFixed(2)}%)
                </td>
            </tr>
        `;
    }).join('');

    tableBody.innerHTML = rows;
}

function updateBotStatus(status) {
    if (!status) return;

    console.log('Updating bot status:', status);

    // Update bot status indicator
    const botStatusElement = document.getElementById('bot-status');
    if (botStatusElement) {
        botStatusElement.textContent = (status.status || 'stopped').toUpperCase();
        botStatusElement.className = `badge ${status.status === 'running' ? 'bg-success' : 'bg-danger'}`;
    }

    // Update market status
    const marketStatusElement = document.getElementById('market-status');
    if (marketStatusElement) {
        marketStatusElement.textContent = (status.market_status || 'closed').toUpperCase();
        marketStatusElement.className = `badge ${status.market_status === 'open' ? 'bg-success' : 'bg-danger'}`;
    }

    // Update last analysis time
    const lastAnalysisElement = document.getElementById('last-analysis');
    if (lastAnalysisElement) {
        lastAnalysisElement.textContent = status.last_analysis_time || 'Never';
    }

    // Update last signal time
    const lastSignalElement = document.getElementById('last-signal');
    if (lastSignalElement) {
        lastSignalElement.textContent = status.last_signal_time || 'Never';
    }

    // Update activity log
    const activityLog = document.getElementById('activity-log');
    if (activityLog) {
        if (!status.status_messages || status.status_messages.length === 0) {
            activityLog.innerHTML = '<div class="alert alert-info">Waiting for bot activity...</div>';
        } else {
            // Clear existing messages if this is the first update
            if (!activityLog.hasChildNodes()) {
                activityLog.innerHTML = '';
            }

            // Add new messages
            status.status_messages.forEach(message => {
                const messageElement = document.createElement('div');
                messageElement.className = `alert alert-${getAlertClass(message.level)} mb-2`;
                messageElement.innerHTML = `
                    <small class="text-muted">${message.timestamp}</small>
                    <div>${message.message}</div>
                `;
                activityLog.appendChild(messageElement);
            });

            // Scroll to bottom
            activityLog.scrollTop = activityLog.scrollHeight;
        }
    }

    // Update button states
    const startButton = document.getElementById('startBot');
    const stopButton = document.getElementById('stopBot');
    if (startButton && stopButton) {
        startButton.disabled = status.status === 'running';
        stopButton.disabled = status.status !== 'running';
    }
}

function getAlertClass(level) {
    switch (level.toLowerCase()) {
        case 'error':
            return 'danger';
        case 'warning':
            return 'warning';
        case 'signal':
            return 'info';
        case 'trade':
            return 'success';
        default:
            return 'secondary';
    }
}

function updatePerformance(performance) {
    if (!performance) return;

    console.log('Updating performance metrics:', performance);

    const elements = {
        'total-pnl': performance.total_pnl || 0,
        'daily-pnl': performance.daily_pnl || 0,
        'win-rate': performance.win_rate || 0
    };

    for (const [id, value] of Object.entries(elements)) {
        const element = document.getElementById(id);
        if (element) {
            if (id === 'win-rate') {
                element.textContent = `${(value * 100).toFixed(2)}%`;
            } else {
                element.textContent = formatCurrency(value);
            }
            console.log(`Updated ${id} with value:`, value);
        } else {
            console.warn(`Element with id ${id} not found`);
        }
    }
}

function updateCharts(performance) {
    if (!performance || !performance.history) return;

    // Update Portfolio Value Chart
    const portfolioData = performance.history.map(h => ({
        x: new Date(h.timestamp),
        y: h.portfolio_value
    }));
    portfolioChart.data.labels = portfolioData.map(d => d.x);
    portfolioChart.data.datasets[0].data = portfolioData.map(d => d.y);
    portfolioChart.update();

    // Update Returns Chart
    const returnsData = performance.history.map(h => ({
        x: new Date(h.timestamp),
        y: h.daily_return
    }));
    returnsChart.data.labels = returnsData.map(d => d.x);
    returnsChart.data.datasets[0].data = returnsData.map(d => d.y);
    returnsChart.update();
}

function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function updateDashboard(data) {
    if (!data) return;

    console.log('Updating dashboard with data:', data);

    // Update bot status
    if (data.status) {
        const botStatusElement = document.getElementById('bot-status');
        const startButton = document.getElementById('startBot');
        const stopButton = document.getElementById('stopBot');
        const marketStatusElement = document.getElementById('market-status');
        const lastAnalysisElement = document.getElementById('last-analysis');
        const lastSignalElement = document.getElementById('last-signal');

        // Update bot status
        botStatusElement.textContent = data.status.toUpperCase();
        botStatusElement.className = `badge bg-${data.status === 'running' ? 'success' : 'secondary'}`;

        // Update button states
        startButton.disabled = data.status === 'running';
        stopButton.disabled = data.status !== 'running';

        // Update market status
        if (data.market_status) {
            marketStatusElement.textContent = data.market_status.toUpperCase();
            marketStatusElement.className = `badge bg-${data.market_status === 'open' ? 'success' : 'secondary'}`;
        }

        // Update last analysis and signal times
        if (data.last_analysis_time) {
            lastAnalysisElement.textContent = new Date(data.last_analysis_time).toLocaleString();
        }
        if (data.last_signal_time) {
            lastSignalElement.textContent = new Date(data.last_signal_time).toLocaleString();
        }

        // Update activity log
        const activityLog = document.getElementById('activity-log');
        if (data.status_messages && data.status_messages.length > 0) {
            activityLog.innerHTML = '';  // Clear existing messages
            data.status_messages.forEach(msg => {
                const alertClass = getAlertClass(msg.level);
                const messageHtml = `
                    <div class="alert ${alertClass} mb-2">
                        <small class="text-muted">${msg.timestamp}</small>
                        <div>${msg.message}</div>
                    </div>
                `;
                activityLog.insertAdjacentHTML('afterbegin', messageHtml);
            });
        } else {
            activityLog.innerHTML = '<div class="alert alert-info">Waiting for bot activity...</div>';
        }
    }

    // Update account info
    if (data.account) {
        updateAccountInfo(data.account);
    }

    // Update performance metrics
    if (data.performance) {
        updatePerformance(data.performance);
        updateCharts(data.performance);
    }

    // Update positions
    if (data.positions) {
        updatePositions(data.positions);
    }
}
