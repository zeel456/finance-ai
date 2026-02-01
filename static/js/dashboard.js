// Chart instances
let categoryChart = null;
let trendChart = null;

// Load all dashboard data
async function loadDashboard() {
    try {
        await Promise.all([
            loadStats(),
            loadCategoryBreakdown(),
            loadMonthlyTrend(),
            loadRecentTransactions(),
            loadTopVendors()
        ]);
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        // Update stats cards
        document.getElementById('totalExpenses').textContent = 
            formatCurrency(data.total_expenses);
        document.getElementById('currentMonthExpenses').textContent = 
            formatCurrency(data.current_month_expenses);
        document.getElementById('totalTransactions').textContent = 
            data.total_transactions;
        document.getElementById('totalDocs').textContent = 
            data.total_documents;
        
        // Update change percentage
        const changeEl = document.getElementById('changePercentage');
        const change = data.change_percentage;
        if (changeEl) {
            changeEl.textContent = `${change > 0 ? '+' : ''}${change.toFixed(1)}%`;
            changeEl.className = `stat-badge ${change > 0 ? 'negative' : 'positive'}`;
        }
        
        console.log('✅ Stats loaded successfully');
    } catch (error) {
        console.error('❌ Error loading stats:', error);
    }
}

// Load category breakdown chart
async function loadCategoryBreakdown() {
    try {
        const response = await fetch('/api/category-breakdown');
        const data = await response.json();
        
        const chartContainer = document.getElementById('categoryChart');
        if (!chartContainer) return;
        
        if (data.length === 0) {
            chartContainer.parentElement.innerHTML = 
                '<div class="no-data"><p>📊 No expense data available yet</p><p>Upload documents or seed data to get started!</p></div>';
            return;
        }
        
        // Prepare chart data
        const labels = data.map(item => item.name);
        const amounts = data.map(item => item.total);
        const colors = data.map(item => item.color);
        
        // Create chart
        const ctx = chartContainer.getContext('2d');
        
        if (categoryChart) {
            categoryChart.destroy();
        }
        
        categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: amounts,
                    backgroundColor: colors,
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${formatCurrency(value)} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        // Create custom legend
        const legendHtml = data.map(item => `
            <div class="legend-item">
                <span class="legend-color" style="background: ${item.color}"></span>
                <span class="legend-label">${item.icon} ${item.name}</span>
                <span class="legend-value">${formatCurrency(item.total)}</span>
            </div>
        `).join('');
        
        const legendContainer = document.getElementById('categoryLegend');
        if (legendContainer) {
            legendContainer.innerHTML = legendHtml;
        }
        
        console.log('✅ Category chart loaded successfully');
    } catch (error) {
        console.error('❌ Error loading category breakdown:', error);
    }
}

// Load monthly trend chart
async function loadMonthlyTrend() {
    try {
        const response = await fetch('/api/monthly-trend?months=6');
        const data = await response.json();
        
        const chartContainer = document.getElementById('trendChart');
        if (!chartContainer) return;
        
        if (data.length === 0) {
            chartContainer.parentElement.innerHTML = 
                '<div class="no-data"><p>📈 No trend data available yet</p></div>';
            return;
        }
        
        // Prepare chart data
        const labels = data.map(item => `${item.month.substring(0, 3)} ${item.year}`);
        const amounts = data.map(item => item.total);
        
        // Create chart
        const ctx = chartContainer.getContext('2d');
        
        if (trendChart) {
            trendChart.destroy();
        }
        
        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Monthly Expenses',
                    data: amounts,
                    borderColor: '#4F46E5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointBackgroundColor: '#4F46E5'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Expenses: ${formatCurrency(context.parsed.y)}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    }
                }
            }
        });
        
        console.log('✅ Trend chart loaded successfully');
    } catch (error) {
        console.error('❌ Error loading trend:', error);
    }
}

// Load recent transactions
async function loadRecentTransactions() {
    try {
        const response = await fetch('/api/recent-transactions?limit=10');
        const data = await response.json();
        
        const container = document.getElementById('recentTransactions');
        if (!container) return;
        
        if (data.length === 0) {
            container.innerHTML = `
                <div class="no-data">
                    <p>📝 No transactions yet</p>
                    <p>Upload documents or seed data to get started!</p>
                </div>
            `;
            return;
        }
        
        const html = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Vendor</th>
                        <th>Category</th>
                        <th>Payment</th>
                        <th class="text-right">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(t => `
                        <tr>
                            <td>${t.date || 'N/A'}</td>
                            <td><strong>${t.vendor || 'Unknown'}</strong></td>
                            <td><span class="badge">${t.category || 'Uncategorized'}</span></td>
                            <td>${t.payment_method || 'N/A'}</td>
                            <td class="amount text-right">${formatCurrency(t.amount)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = html;
        console.log('✅ Recent transactions loaded successfully');
    } catch (error) {
        console.error('❌ Error loading transactions:', error);
        const container = document.getElementById('recentTransactions');
        if (container) {
            container.innerHTML = '<div class="error"><p>⚠️ Error loading transactions</p></div>';
        }
    }
}

// Load top vendors
async function loadTopVendors() {
    try {
        const response = await fetch('/api/top-vendors?limit=5');
        const data = await response.json();
        
        const container = document.getElementById('topVendors');
        if (!container) return;
        
        if (data.length === 0) {
            container.innerHTML = '<div class="no-data"><p>🏪 No vendor data available yet</p></div>';
            return;
        }
        
        const html = data.map((vendor, index) => `
            <div class="vendor-item">
                <div class="vendor-rank">#${index + 1}</div>
                <div class="vendor-info">
                    <h4>${vendor.vendor}</h4>
                    <p>${vendor.transaction_count} transaction${vendor.transaction_count > 1 ? 's' : ''}</p>
                </div>
                <div class="vendor-amount">
                    ${formatCurrency(vendor.total)}
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
        console.log('✅ Top vendors loaded successfully');
    } catch (error) {
        console.error('❌ Error loading vendors:', error);
        const container = document.getElementById('topVendors');
        if (container) {
            container.innerHTML = '<div class="error"><p>⚠️ Error loading vendors</p></div>';
        }
    }
}

// Helper function for currency formatting
function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing dashboard...');
    loadDashboard();
});

// Auto-refresh every 30 seconds
setInterval(() => {
    console.log('🔄 Auto-refreshing dashboard...');
    loadDashboard();
}, 30000);