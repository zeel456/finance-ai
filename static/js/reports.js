/**
 * Reports JavaScript with PDF Export
 * Updated save as: static/js/reports.js
 */

let currentReportType = 'monthly';
let currentReportData = null;
let charts = {};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    selectReportType('monthly');
    generateReport();
});

// Select report type
function selectReportType(type) {
    currentReportType = type;
    
    document.querySelectorAll('.report-type-card').forEach(card => {
        card.classList.remove('active');
    });
    document.querySelector(`[data-type="${type}"]`).classList.add('active');
    
    updateControls(type);
}

// Update controls based on report type
function updateControls(type) {
    const controlsContainer = document.getElementById('reportControls');
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1;
    
    let controlsHTML = '';
    
    if (type === 'monthly') {
        controlsHTML = `
            <div class="control-group">
                <label>Year</label>
                <select id="reportYear">
                    ${generateYearOptions(currentYear)}
                </select>
            </div>
            <div class="control-group">
                <label>Month</label>
                <select id="reportMonth">
                    ${generateMonthOptions(currentMonth)}
                </select>
            </div>
        `;
    } else if (type === 'quarterly') {
        const currentQuarter = Math.floor((currentMonth - 1) / 3) + 1;
        controlsHTML = `
            <div class="control-group">
                <label>Year</label>
                <select id="reportYear">
                    ${generateYearOptions(currentYear)}
                </select>
            </div>
            <div class="control-group">
                <label>Quarter</label>
                <select id="reportQuarter">
                    <option value="1" ${currentQuarter === 1 ? 'selected' : ''}>Q1 (Jan-Mar)</option>
                    <option value="2" ${currentQuarter === 2 ? 'selected' : ''}>Q2 (Apr-Jun)</option>
                    <option value="3" ${currentQuarter === 3 ? 'selected' : ''}>Q3 (Jul-Sep)</option>
                    <option value="4" ${currentQuarter === 4 ? 'selected' : ''}>Q4 (Oct-Dec)</option>
                </select>
            </div>
        `;
    } else if (type === 'comparison') {
        controlsHTML = `
            <div class="control-group">
                <label>Period Type</label>
                <select id="periodType">
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                </select>
            </div>
            <div class="control-group">
                <label>Number of Periods</label>
                <select id="periodsCount">
                    <option value="3">3 Periods</option>
                    <option value="6" selected>6 Periods</option>
                    <option value="12">12 Periods</option>
                </select>
            </div>
        `;
    } else if (type === 'custom') {
        const today = now.toISOString().split('T')[0];
        const firstDayOfMonth = new Date(currentYear, currentMonth - 1, 1).toISOString().split('T')[0];
        controlsHTML = `
            <div class="control-group">
                <label>Start Date</label>
                <input type="date" id="startDate" value="${firstDayOfMonth}">
            </div>
            <div class="control-group">
                <label>End Date</label>
                <input type="date" id="endDate" value="${today}">
            </div>
        `;
    }
    
    controlsContainer.innerHTML = controlsHTML;
}

// Generate year options
function generateYearOptions(currentYear) {
    let options = '';
    for (let year = currentYear; year >= currentYear - 5; year--) {
        options += `<option value="${year}" ${year === currentYear ? 'selected' : ''}>${year}</option>`;
    }
    return options;
}

// Generate month options
function generateMonthOptions(currentMonth) {
    const months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return months.map((month, index) => 
        `<option value="${index + 1}" ${index + 1 === currentMonth ? 'selected' : ''}>${month}</option>`
    ).join('');
}

// Generate report
async function generateReport() {
    const loadingState = document.getElementById('loadingState');
    const reportDisplay = document.getElementById('reportDisplay');
    
    loadingState.style.display = 'block';
    reportDisplay.style.display = 'none';
    
    try {
        let url = '';
        let params = new URLSearchParams();
        
        if (currentReportType === 'monthly') {
            const year = document.getElementById('reportYear').value;
            const month = document.getElementById('reportMonth').value;
            url = `/api/reports/monthly`;
            params.append('year', year);
            params.append('month', month);
        } else if (currentReportType === 'quarterly') {
            const year = document.getElementById('reportYear').value;
            const quarter = document.getElementById('reportQuarter').value;
            url = `/api/reports/quarterly`;
            params.append('year', year);
            params.append('quarter', quarter);
        } else if (currentReportType === 'comparison') {
            const periodType = document.getElementById('periodType').value;
            const periods = document.getElementById('periodsCount').value;
            url = `/api/reports/comparison`;
            params.append('period_type', periodType);
            params.append('periods', periods);
        } else if (currentReportType === 'custom') {
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            url = `/api/reports/custom`;
            params.append('start_date', startDate);
            params.append('end_date', endDate);
        }
        
        const response = await fetch(`${url}?${params}`);
        const data = await response.json();
        
        if (data.success) {
            currentReportData = data.report;
            displayReport(data.report);
        } else {
            throw new Error(data.error || 'Failed to generate report');
        }
        
    } catch (error) {
        console.error('Report generation error:', error);
        reportDisplay.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">❌</div>
                <h3>Error Generating Report</h3>
                <p>${error.message}</p>
            </div>
        `;
        reportDisplay.style.display = 'block';
    } finally {
        loadingState.style.display = 'none';
    }
}

// Display report
function displayReport(report) {
    const reportDisplay = document.getElementById('reportDisplay');
    
    Object.values(charts).forEach(chart => chart.destroy());
    charts = {};
    
    let html = '';
    
    if (currentReportType === 'monthly' || currentReportType === 'custom') {
        html = generateMonthlyReport(report);
    } else if (currentReportType === 'quarterly') {
        html = generateQuarterlyReport(report);
    } else if (currentReportType === 'comparison') {
        html = generateComparisonReport(report);
    }
    
    reportDisplay.innerHTML = html;
    reportDisplay.style.display = 'block';
    reportDisplay.classList.add('active');
    
    setTimeout(() => renderReportCharts(report), 100);
}

// Generate monthly report HTML
function generateMonthlyReport(report) {
    const period = report.period;
    const summary = report.summary;
    
    return `
        <div class="report-title">
            ${period.type === 'monthly' ? period.month_name + ' ' + period.year : 'Custom Range'} Report
        </div>
        <div class="report-subtitle">
            ${period.start_date} to ${period.end_date}
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-label">Total Expenses</div>
                <div class="summary-value">₹${formatCurrency(summary.total_expenses)}</div>
                <div class="summary-subvalue">${summary.transaction_count} transactions</div>
            </div>
            
            <div class="summary-card">
                <div class="summary-label">Average Transaction</div>
                <div class="summary-value">₹${formatCurrency(summary.average_transaction)}</div>
            </div>
            
            <div class="summary-card">
                <div class="summary-label">Daily Average</div>
                <div class="summary-value">₹${formatCurrency(summary.average_daily)}</div>
                <div class="summary-subvalue">${summary.days_in_period} days</div>
            </div>
            
            <div class="summary-card">
                <div class="summary-label">Total Tax</div>
                <div class="summary-value">₹${formatCurrency(summary.total_tax)}</div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="chart-container">
                <div class="chart-title">Category Breakdown</div>
                <canvas id="categoryChart" width="400" height="200"></canvas>
            </div>
            
            ${report.daily_spending ? `
            <div class="chart-container">
                <div class="chart-title">Daily Spending Trend</div>
                <canvas id="dailyChart" width="400" height="200"></canvas>
            </div>
            ` : ''}
        </div>
        
        <h3 style="margin-top: 2rem; margin-bottom: 1rem; color: #1F2937;">Top Categories</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Amount</th>
                    <th>Transactions</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
                ${report.categories.slice(0, 10).map(cat => `
                    <tr>
                        <td><strong>${cat.name}</strong></td>
                        <td>₹${formatCurrency(cat.total)}</td>
                        <td>${cat.count}</td>
                        <td>${cat.percentage.toFixed(1)}%</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        
        ${report.vendors && report.vendors.length > 0 ? `
        <h3 style="margin-top: 2rem; margin-bottom: 1rem; color: #1F2937;">Top Vendors</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Vendor</th>
                    <th>Amount</th>
                    <th>Transactions</th>
                </tr>
            </thead>
            <tbody>
                ${report.vendors.slice(0, 10).map(vendor => `
                    <tr>
                        <td><strong>${vendor.name}</strong></td>
                        <td>₹${formatCurrency(vendor.total)}</td>
                        <td>${vendor.count}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        ` : ''}
        
        <div class="export-actions">
            <button class="btn-export" onclick="printReport()">
                🖨️ Print Report
            </button>
            <button class="btn-export" onclick="exportToPDF()" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none;">
                📄 Export to PDF
            </button>
        </div>
    `;
}

// Generate quarterly report HTML
function generateQuarterlyReport(report) {
    const period = report.period;
    const summary = report.summary;
    
    return `
        <div class="report-title">
            Q${period.quarter} ${period.year} Report
        </div>
        <div class="report-subtitle">
            ${period.start_date} to ${period.end_date}
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-label">Total Expenses</div>
                <div class="summary-value">₹${formatCurrency(summary.total_expenses)}</div>
                <div class="summary-subvalue">${summary.transaction_count} transactions</div>
            </div>
            
            <div class="summary-card">
                <div class="summary-label">Average Monthly</div>
                <div class="summary-value">₹${formatCurrency(summary.average_monthly)}</div>
            </div>
            
            <div class="summary-card">
                <div class="summary-label">Duration</div>
                <div class="summary-value">${summary.days_in_period}</div>
                <div class="summary-subvalue">days</div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="chart-container">
                <div class="chart-title">Monthly Breakdown</div>
                <canvas id="monthlyChart" width="400" height="200"></canvas>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">Category Distribution</div>
                <canvas id="categoryChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <h3 style="margin-top: 2rem; margin-bottom: 1rem; color: #1F2937;">Monthly Details</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Month</th>
                    <th>Total Spent</th>
                    <th>Transactions</th>
                </tr>
            </thead>
            <tbody>
                ${report.monthly_breakdown.map(month => `
                    <tr>
                        <td><strong>${month.month_name}</strong></td>
                        <td>₹${formatCurrency(month.total)}</td>
                        <td>${month.count}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        
        <div class="export-actions">
            <button class="btn-export" onclick="printReport()">
                🖨️ Print Report
            </button>
            <button class="btn-export" onclick="exportToPDF()" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none;">
                📄 Export to PDF
            </button>
        </div>
    `;
}

// Generate comparison report HTML
function generateComparisonReport(report) {
    const trend = report.trend;
    const trendIcon = trend.direction === 'up' ? '📈' : trend.direction === 'down' ? '📉' : '➡️';
    const trendColor = trend.direction === 'up' ? '#EF4444' : trend.direction === 'down' ? '#10B981' : '#6B7280';
    
    return `
        <div class="report-title">
            ${report.period_type === 'monthly' ? 'Monthly' : 'Quarterly'} Comparison Report
        </div>
        <div class="report-subtitle">
            Comparing ${report.periods_count} periods
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-label">Trend</div>
                <div class="summary-value" style="color: ${trendColor}">
                    ${trendIcon} ${Math.abs(trend.change_percentage).toFixed(1)}%
                </div>
                <div class="summary-subvalue">${trend.direction === 'up' ? 'Increased' : trend.direction === 'down' ? 'Decreased' : 'No change'}</div>
            </div>
            
            <div class="summary-card">
                <div class="summary-label">Latest Period</div>
                <div class="summary-value">₹${formatCurrency(report.data[report.data.length - 1].total)}</div>
                <div class="summary-subvalue">${report.data[report.data.length - 1].count} transactions</div>
            </div>
            
            <div class="summary-card">
                <div class="summary-label">Previous Period</div>
                <div class="summary-value">₹${formatCurrency(report.data[report.data.length - 2].total)}</div>
                <div class="summary-subvalue">${report.data[report.data.length - 2].count} transactions</div>
            </div>
        </div>
        
        <div class="charts-section">
            <div class="chart-container">
                <div class="chart-title">Spending Trend Over Time</div>
                <canvas id="comparisonChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <h3 style="margin-top: 2rem; margin-bottom: 1rem; color: #1F2937;">Period Details</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Period</th>
                    <th>Total Spent</th>
                    <th>Transactions</th>
                    <th>Avg Transaction</th>
                </tr>
            </thead>
            <tbody>
                ${report.data.map(period => `
                    <tr>
                        <td><strong>${period.period}</strong></td>
                        <td>₹${formatCurrency(period.total)}</td>
                        <td>${period.count}</td>
                        <td>₹${formatCurrency(period.avg_transaction || 0)}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        
        <div class="export-actions">
            <button class="btn-export" onclick="printReport()">
                🖨️ Print Report
            </button>
            <button class="btn-export" onclick="exportToPDF()" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none;">
                📄 Export to PDF
            </button>
        </div>
    `;
}

// Render charts
function renderReportCharts(report) {
    if (currentReportType === 'monthly' || currentReportType === 'custom') {
        if (report.categories && report.categories.length > 0) {
            const categoryCanvas = document.getElementById('categoryChart');
            if (categoryCanvas) {
                const colors = [
                    '#667eea', '#764ba2', '#f093fb', '#4facfe',
                    '#43e97b', '#fa709a', '#fee140', '#30cfd0'
                ];
                
                charts.category = new Chart(categoryCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: report.categories.slice(0, 8).map(c => c.name),
                        datasets: [{
                            data: report.categories.slice(0, 8).map(c => c.total),
                            backgroundColor: colors,
                            borderWidth: 2,
                            borderColor: '#fff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: {
                                    padding: 15,
                                    usePointStyle: true
                                }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const value = context.parsed;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = ((value / total) * 100).toFixed(1);
                                        return `₹${formatCurrency(value)} (${percentage}%)`;
                                    }
                                }
                            }
                        }
                    }
                });
            }
        }
        
        if (report.daily_spending && report.daily_spending.length > 0) {
            const dailyCanvas = document.getElementById('dailyChart');
            if (dailyCanvas) {
                charts.daily = new Chart(dailyCanvas, {
                    type: 'line',
                    data: {
                        labels: report.daily_spending.map(d => new Date(d.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })),
                        datasets: [{
                            label: 'Daily Spending',
                            data: report.daily_spending.map(d => d.total),
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4,
                            pointHoverRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    callback: function(value) {
                                        return '₹' + formatCurrency(value);
                                    }
                                }
                            }
                        }
                    }
                });
            }
        }
    } else if (currentReportType === 'quarterly') {
        const monthlyCanvas = document.getElementById('monthlyChart');
        if (monthlyCanvas && report.monthly_breakdown) {
            charts.monthly = new Chart(monthlyCanvas, {
                type: 'bar',
                data: {
                    labels: report.monthly_breakdown.map(m => m.month_name),
                    datasets: [{
                        label: 'Monthly Spending',
                        data: report.monthly_breakdown.map(m => m.total),
                        backgroundColor: ['#667eea', '#764ba2', '#f093fb'],
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '₹' + formatCurrency(value);
                                }
                            }
                        }
                    }
                }
            });
        }
        
        if (report.categories && report.categories.length > 0) {
            const categoryCanvas = document.getElementById('categoryChart');
            if (categoryCanvas) {
                const colors = [
                    '#667eea', '#764ba2', '#f093fb', '#4facfe',
                    '#43e97b', '#fa709a', '#fee140', '#30cfd0'
                ];
                
                charts.category = new Chart(categoryCanvas, {
                    type: 'pie',
                    data: {
                        labels: report.categories.slice(0, 8).map(c => c.name),
                        datasets: [{
                            data: report.categories.slice(0, 8).map(c => c.total),
                            backgroundColor: colors,
                            borderWidth: 2,
                            borderColor: '#fff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: {
                                    padding: 15,
                                    usePointStyle: true
                                }
                            }
                        }
                    }
                });
            }
        }
    } else if (currentReportType === 'comparison') {
        const comparisonCanvas = document.getElementById('comparisonChart');
        if (comparisonCanvas && report.data) {
            charts.comparison = new Chart(comparisonCanvas, {
                type: 'line',
                data: {
                    labels: report.data.map(d => d.period),
                    datasets: [{
                        label: 'Total Spending',
                        data: report.data.map(d => d.total),
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        pointBackgroundColor: '#667eea',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '₹' + formatCurrency(value);
                                }
                            }
                        }
                    }
                }
            });
        }
    }
}

// Format currency
function formatCurrency(amount) {
    return parseFloat(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Capture charts as base64 images with validation
async function captureCharts() {
    const chartsBase64 = {};
    
    for (const [name, chart] of Object.entries(charts)) {
        try {
            if (!chart) {
                console.warn(`Chart ${name} not initialized`);
                continue;
            }
            
            if (!chart.canvas) {
                console.warn(`Chart ${name} has no canvas`);
                continue;
            }
            
            // Capture the chart as base64
            const base64Image = chart.toBase64Image();
            
            // Validate the base64 data
            if (!base64Image || base64Image.length < 100) {
                console.warn(`Chart ${name} produced invalid image data`);
                continue;
            }
            
            chartsBase64[name] = base64Image;
            console.log(`✓ Captured chart: ${name} (${(base64Image.length / 1024).toFixed(1)} KB)`);
            
        } catch (error) {
            console.error(`Error capturing chart ${name}:`, error);
        }
    }
    
    console.log(`Total charts captured: ${Object.keys(chartsBase64).length}`);
    return chartsBase64;
}

// Export to PDF with comprehensive validation
async function exportToPDF() {
    const btn = event.target;
    const originalText = btn.innerText;
    
    try {
        // Validate report data
        if (!currentReportData) {
            throw new Error("No report data available. Please generate a report first.");
        }
        
        if (!currentReportData.period || !currentReportData.summary) {
            throw new Error("Invalid report data structure. Please regenerate the report.");
        }
        
        btn.disabled = true;
        btn.innerText = '⏳ Generating PDF...';
        
        console.log('Starting PDF export for:', currentReportType);
        console.log('Report data:', currentReportData);
        
        // Capture all charts with validation
        const chartsBase64 = await captureCharts();
        console.log('Charts captured:', Object.keys(chartsBase64));
        
        // Prepare payload
        const payload = {
            report_data: currentReportData,
            report_type: currentReportType,
            charts: chartsBase64
        };
        
        // Validate payload
        if (!payload.report_data || typeof payload.report_data !== 'object') {
            throw new Error("Report data validation failed");
        }
        
        console.log('Sending payload size:', (JSON.stringify(payload).length / 1024).toFixed(2), 'KB');
        
        // Send to backend
        const response = await fetch('/api/reports/export-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        console.log('Backend response status:', response.status);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `Server error: ${response.status}`);
        }
        
        // Get the PDF blob and download
        const blob = await response.blob();
        console.log('PDF blob size:', (blob.size / 1024 / 1024).toFixed(2), 'MB');
        
        if (blob.size === 0) {
            throw new Error("Generated PDF is empty");
        }
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Generate filename
        const period = currentReportData.period || {};
        let filename = 'Financial_Report.pdf';
        
        if (currentReportType === 'monthly') {
            filename = `Report_${period.month_name || ''}_${period.year || ''}.pdf`;
        } else if (currentReportType === 'quarterly') {
            filename = `Report_Q${period.quarter || ''}_${period.year || ''}.pdf`;
        } else if (currentReportType === 'custom') {
            filename = `Report_${period.start_date || ''}_to_${period.end_date || ''}.pdf`;
        } else if (currentReportType === 'comparison') {
            filename = `Comparison_Report_${new Date().toISOString().split('T')[0]}.pdf`;
        }
        
        a.download = filename.replace(/\s+/g, '_').replace(/:/g, '-');
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        console.log('PDF downloaded:', a.download);
        btn.innerText = '✅ PDF Downloaded!';
        setTimeout(() => {
            btn.innerText = originalText;
            btn.disabled = false;
        }, 2000);
        
    } catch (error) {
        console.error('PDF export error:', error);
        alert('❌ Error generating PDF:\n\n' + error.message + '\n\nCheck browser console for details.');
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

// Print report
function printReport() {
    window.print();
}

// Clean up charts on page unload
window.addEventListener('beforeunload', () => {
    Object.values(charts).forEach(chart => {
        if (chart) chart.destroy();
    });
});