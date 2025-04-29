// Initialize Socket.IO connection
const socket = io();

// DOM Elements
const loginForm = document.getElementById('login-form');
const dashboard = document.getElementById('dashboard');
const loginContainer = document.getElementById('login-container');
const logoutBtn = document.getElementById('logout-btn');
const startBotBtn = document.getElementById('start-bot');
const stopBotBtn = document.getElementById('stop-bot');
const botStatus = document.getElementById('bot-status');
const runtime = document.getElementById('runtime');
const marketStatus = document.getElementById('market-status');
const initialCapital = document.getElementById('initial-capital');
const currentCapital = document.getElementById('current-capital');
const activePositions = document.getElementById('active-positions');
const errorMessage = document.getElementById('error-message');
const configForm = document.getElementById('config-form');
const symbolsInput = document.getElementById('symbols');
const initialCapitalInput = document.getElementById('initial-capital');
const userProfile = document.querySelector('.user-profile');
const userAvatar = document.querySelector('.user-avatar');
const userName = document.querySelector('.user-name');
const userEmail = document.querySelector('.user-email');

// Charts
let returnsChart = null;
let positionsChart = null;

// Initialize charts with descriptions
function initializeCharts() {
  // Returns Chart
  const returnsCtx = document.getElementById('returns-chart').getContext('2d');
  returnsChart = new Chart(returnsCtx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Returns (%)',
        data: [],
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
        fill: false
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `Returns: ${context.parsed.y.toFixed(2)}%`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return value + '%';
            }
          },
          title: {
            display: true,
            text: 'Returns (%)'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Time'
          }
        }
      }
    }
  });

  // Add returns chart description
  const returnsContainer = document.querySelector('#returns-chart').parentElement;
  const returnsDescription = document.createElement('div');
  returnsDescription.className = 'chart-description';
  returnsDescription.innerHTML = `
    <h6>Returns Over Time</h6>
    <p>This chart shows the percentage returns of your trading bot over time. Positive values indicate profits, while negative values show losses.</p>
  `;
  returnsContainer.appendChild(returnsDescription);

  // Positions Chart
  const positionsCtx = document.getElementById('positions-chart').getContext('2d');
  positionsChart = new Chart(positionsCtx, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [{
        label: 'Active Positions',
        data: [],
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
        borderColor: 'rgb(54, 162, 235)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `Positions: ${context.parsed.y}`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          },
          title: {
            display: true,
            text: 'Number of Positions'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Time'
          }
        }
      }
    }
  });

  // Add positions chart description
  const positionsContainer = document.querySelector('#positions-chart').parentElement;
  const positionsDescription = document.createElement('div');
  positionsDescription.className = 'chart-description';
  positionsDescription.innerHTML = `
    <h6>Active Positions</h6>
    <p>This chart displays the number of active trading positions over time. It helps you monitor the bot's trading activity and position management.</p>
  `;
  positionsContainer.appendChild(positionsDescription);
}

// Update bot status
function updateBotStatus(status) {
  const startBtn = document.getElementById('start-bot');
  const stopBtn = document.getElementById('stop-bot');
  
  botStatus.textContent = status;
  botStatus.className = `status-value bot-${status.toLowerCase()}`;
  
  // Update button states
  if (status === 'RUNNING') {
    startBtn.disabled = true;
    stopBtn.disabled = false;
  } else if (status === 'STOPPED') {
    startBtn.disabled = false;
    stopBtn.disabled = true;
  }
}

// Update market status
function updateMarketStatus(isOpen) {
  marketStatus.textContent = isOpen ? 'Open' : 'Closed';
  marketStatus.className = `status-value market-${isOpen ? 'open' : 'closed'}`;
}

// Update performance metrics
function updateMetrics(data) {
  runtime.textContent = data.runtime;
  currentCapital.textContent = `$${data.bot_status.current_capital?.toFixed(2) || '0.00'}`;
  activePositions.textContent = data.bot_status.active_positions || '0';
  
  // Update charts
  if (returnsChart && positionsChart) {
    // Add new data point to returns chart
    const timestamp = new Date().toLocaleTimeString();
    returnsChart.data.labels.push(timestamp);
    returnsChart.data.datasets[0].data.push(data.bot_status.current_capital || 0);
    
    // Keep only last 20 data points
    if (returnsChart.data.labels.length > 20) {
      returnsChart.data.labels.shift();
      returnsChart.data.datasets[0].data.shift();
    }
    
    returnsChart.update();
  }
}

// Update charts
function updateCharts(data) {
  if (!returnsChart || !positionsChart) return;

  // Update Returns Chart
  const timestamp = new Date().toLocaleTimeString();
  returnsChart.data.labels.push(timestamp);
  returnsChart.data.datasets[0].data.push(data.returns);
  
  // Keep only last 20 data points
  if (returnsChart.data.labels.length > 20) {
    returnsChart.data.labels.shift();
    returnsChart.data.datasets[0].data.shift();
  }
  
  returnsChart.update('none'); // Use 'none' for better performance

  // Update Positions Chart
  positionsChart.data.labels.push(timestamp);
  positionsChart.data.datasets[0].data.push(data.positions);
  
  // Keep only last 20 data points
  if (positionsChart.data.labels.length > 20) {
    positionsChart.data.labels.shift();
    positionsChart.data.datasets[0].data.shift();
  }
  
  positionsChart.update('none'); // Use 'none' for better performance
}

// Show error message
function showError(message) {
  errorMessage.textContent = message;
  errorMessage.style.display = 'block';
  setTimeout(() => {
    errorMessage.style.display = 'none';
  }, 5000);
}

// Handle login form submission
document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;

  try {
    // Mock login - in production, this would be an API call
    if (username && password) {
      // Hide login page and show dashboard
      document.getElementById('login-page').style.display = 'none';
      document.getElementById('dashboard').style.display = 'block';
      
      // Update user profile
      const name = username.split('@')[0];
      const email = username;
      userAvatar.textContent = name.charAt(0).toUpperCase();
      userName.textContent = name;
      userEmail.textContent = email;
      userProfile.style.display = 'flex';
      
      // Initialize charts
      initializeCharts();
      
      // Fetch initial status
      const response = await fetch('/api/status');
      if (!response.ok) {
        throw new Error('Failed to fetch status');
      }
      const data = await response.json();
      if (data.success) {
        updateBotStatus(data.bot_status.status);
        updateMarketStatus(data.market_open);
        updateMetrics(data);
      }
    } else {
      showError('Please enter both username and password');
    }
  } catch (error) {
    console.error('Login error:', error);
    showError('Login failed. Please try again.');
  }
});

// Handle social login buttons
document.querySelectorAll('.social-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    // Mock social login - in production, this would redirect to OAuth
    const mockEmail = 'user@example.com';
    const mockName = 'User';
    
    // Hide login page and show dashboard
    document.getElementById('login-page').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    
    // Update user profile
    userAvatar.textContent = mockName.charAt(0).toUpperCase();
    userName.textContent = mockName;
    userEmail.textContent = mockEmail;
    userProfile.style.display = 'flex';
    
    // Initialize charts
    initializeCharts();
  });
});

// Handle logout
document.getElementById('logout-btn').addEventListener('click', () => {
  // Hide dashboard and show login page
  document.getElementById('dashboard').style.display = 'none';
  document.getElementById('login-page').style.display = 'block';
  
  // Clear user profile
  userProfile.style.display = 'none';
  userAvatar.textContent = '';
  userName.textContent = '';
  userEmail.textContent = '';
  
  // Reset form
  document.getElementById('login-form').reset();
  
  // Clear any existing charts
  if (returnsChart) returnsChart.destroy();
  if (positionsChart) positionsChart.destroy();
});

// Handle start bot button
startBotBtn.addEventListener('click', async () => {
  try {
    const response = await fetch('/api/start', {
      method: 'POST'
    });
    const data = await response.json();
    if (data.success) {
      updateBotStatus('RUNNING');
      addLog('Bot started successfully');
    } else {
      showError(data.error || 'Failed to start bot');
    }
  } catch (error) {
    showError('Failed to start bot');
  }
});

// Handle stop bot button
stopBotBtn.addEventListener('click', async () => {
  try {
    const response = await fetch('/api/stop', {
      method: 'POST'
    });
    const data = await response.json();
    if (data.success) {
      updateBotStatus('STOPPED');
      addLog('Bot stopped successfully');
    } else {
      showError(data.error || 'Failed to stop bot');
    }
  } catch (error) {
    showError('Failed to stop bot');
  }
});

// Handle config form submission
configForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const symbols = document.getElementById('symbols').value;
  const initialCapital = document.getElementById('initial-capital').value;

  try {
    const response = await fetch('/api/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        symbols: symbols.split(',').map(s => s.trim()),
        initial_capital: parseFloat(initialCapital)
      })
    });
    const data = await response.json();
    if (data.success) {
      showError('Configuration updated successfully');
    } else {
      showError(data.error || 'Failed to update configuration');
    }
  } catch (error) {
    showError('Failed to update configuration');
  }
});

// Socket.IO event handlers
socket.on('connect', () => {
  console.log('Connected to server');
});

socket.on('disconnect', () => {
  console.log('Disconnected from server');
});

socket.on('update', (data) => {
  updateBotStatus(data.bot_status.status);
  updateMarketStatus(data.market_open);
  updateMetrics(data);
  updateCharts(data);
  document.getElementById('runtime').textContent = data.runtime;
});

// Initialize the UI
document.addEventListener('DOMContentLoaded', () => {
  // Only initialize charts after successful login
  if (document.getElementById('dashboard').style.display === 'block') {
    initializeCharts();
    
    // Fetch initial configuration
    fetch('/api/config')
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch configuration');
        }
        return response.json();
      })
      .then(data => {
        if (data.success) {
          symbolsInput.value = data.symbols.join(', ');
          initialCapitalInput.value = data.initial_capital;
          initialCapital.textContent = `$${data.initial_capital.toFixed(2)}`;
        } else {
          showError(data.error || 'Failed to load configuration');
        }
      })
      .catch(error => {
        console.error('Configuration error:', error);
        showError('Error loading configuration: ' + error.message);
      });
  }
}); 