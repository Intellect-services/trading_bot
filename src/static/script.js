// Connect to WebSocket
const socket = io();

// DOM elements
const runtimeElement = document.getElementById('runtime');
const marketStatusElement = document.getElementById('market-status');
const equityElement = document.getElementById('equity');
const cashElement = document.getElementById('cash');
const buyingPowerElement = document.getElementById('buying-power');
const positionsTableBody = document.getElementById('positions-table-body');
const latestPriceElement = document.getElementById('latest-price');
const priceChangeElement = document.getElementById('price-change');

// Update UI with received data
socket.on('update', function(data) {
    // Update runtime
    runtimeElement.textContent = data.runtime;

    // Update market status
    marketStatusElement.textContent = data.market_open ? 'Open' : 'Closed';
    marketStatusElement.className = data.market_open ? 'market-status market-open' : 'market-status market-closed';

    // Update account info
    equityElement.textContent = formatCurrency(data.account_info.equity);
    cashElement.textContent = formatCurrency(data.account_info.cash);
    buyingPowerElement.textContent = formatCurrency(data.account_info.buying_power);

    // Update positions table
    positionsTableBody.innerHTML = '';
    for (const [symbol, position] of Object.entries(data.positions)) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${symbol}</td>
            <td>${position.quantity}</td>
            <td>${formatCurrency(position.entry_price)}</td>
            <td>${formatCurrency(position.current_price)}</td>
            <td>${formatCurrency(position.market_value)}</td>
            <td>${formatPercentage(position.unrealized_pl_pct)}</td>
        `;
        positionsTableBody.appendChild(row);
    }

    // Update latest price
    latestPriceElement.textContent = formatCurrency(data.latest_price);
    
    // Update price change
    const priceChange = data.price_change;
    priceChangeElement.textContent = formatPercentage(priceChange);
    priceChangeElement.className = priceChange >= 0 ? 'positive' : 'negative';
});

// Helper functions
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value / 100);
}

// Error handling
socket.on('connect_error', function(error) {
    console.error('Connection error:', error);
});

socket.on('error', function(error) {
    console.error('Socket error:', error);
}); 