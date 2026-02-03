// ============================================================================
// TRANSACTIONS PAGE - JavaScript
// Save as: static/js/transactions.js
// ============================================================================

// Global state
let currentPage = 1;
let totalPages = 1;
let currentTransactionId = null;
let allCategories = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    loadTransactions();
    loadStats();
    setDefaultDate();
});

// Set today's date as default in form
function setDefaultDate() {
    const el = document.getElementById('transaction_date');
    if (!el) return;
    el.value = new Date().toISOString().split('T')[0];
}

// ============================================================================
// LOAD CATEGORIES  ✅ FIXED
// ============================================================================

async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const data = await response.json();

        // ✅ Handle both API formats
        const categories = data.categories || data;

        if (!Array.isArray(categories)) {
            throw new Error('Invalid categories response');
        }

        allCategories = categories;

        const selects = ['category_id', 'filterCategory'];

        selects.forEach(id => {
            const select = document.getElementById(id);
            if (!select) return;

            const isFilter = id === 'filterCategory';
            select.innerHTML = isFilter
                ? '<option value="">All Categories</option>'
                : '<option value="">Select Category</option>';

            categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.id;
                option.textContent = cat.name;
                select.appendChild(option);
            });
        });

        console.log('✅ Categories loaded:', categories.length);

    } catch (error) {
        console.error('❌ Error loading categories:', error);
        showNotification('Failed to load categories', 'error');
    }
}

// ============================================================================
// LOAD TRANSACTIONS
// ============================================================================

async function loadTransactions(page = 1) {
    try {
        currentPage = page;
        const tableBody = document.getElementById('transactionsTableBody');
        tableBody.innerHTML = `<tr><td colspan="7" class="loading-spinner">⏳ Loading...</td></tr>`;

        const params = new URLSearchParams({ page, per_page: 20 });

        const category = document.getElementById('filterCategory')?.value;
        const start = document.getElementById('filterStartDate')?.value;
        const end = document.getElementById('filterEndDate')?.value;
        const method = document.getElementById('filterPaymentMethod')?.value;

        if (category) params.append('category_id', category);
        if (start) params.append('start_date', start);
        if (end) params.append('end_date', end);
        if (method) params.append('payment_method', method);

        const response = await fetch(`/api/transactions?${params}`);
        const data = await response.json();

        if (data.success && data.transactions.length) {
            displayTransactions(data.transactions);
            updatePagination(data.page, data.pages);
        } else {
            tableBody.innerHTML = `
                <tr><td colspan="7" class="empty-state">📭 No transactions found</td></tr>
            `;
            document.getElementById('paginationContainer').style.display = 'none';
        }

    } catch (error) {
        console.error('❌ Error loading transactions:', error);
    }
}

function displayTransactions(transactions) {
    const body = document.getElementById('transactionsTableBody');
    body.innerHTML = transactions.map(t => `
        <tr>
            <td>${t.date}</td>
            <td>${t.vendor}</td>
            <td class="amount-cell">₹${t.amount.toFixed(2)}</td>
            <td><span class="category-badge">${t.category}</span></td>
            <td><span class="payment-badge">${t.payment_method || 'N/A'}</span></td>
            <td>${t.description || '-'}</td>
            <td>
                <button onclick="editTransaction(${t.id})">✏️</button>
                <button onclick="deleteTransaction(${t.id}, '${t.vendor}')">🗑️</button>
            </td>
        </tr>
    `).join('');
}

// ============================================================================
// LOAD STATS  ✅ FIXED
// ============================================================================

async function loadStats() {
    try {
        const totalEl = document.getElementById('totalTransactions');
        if (!totalEl) return; // page safety

        const res = await fetch('/api/stats');
        const stats = await res.json();

        document.getElementById('totalTransactions').textContent =
            stats.transaction_count || 0;

        document.getElementById('totalAmount').textContent =
            formatCurrency(stats.total_expenses || 0);

        const avgEl = document.getElementById('avgTransaction');
        if (avgEl) {
            avgEl.textContent = formatCurrency(
                stats.transaction_count
                    ? stats.total_expenses / stats.transaction_count
                    : 0
            );
        }

        const monthEl = document.getElementById('thisMonth');
        if (monthEl) {
            const now = new Date();
            const start = new Date(now.getFullYear(), now.getMonth(), 1)
                .toISOString().split('T')[0];
            const end = new Date(now.getFullYear(), now.getMonth() + 1, 0)
                .toISOString().split('T')[0];

            const mRes = await fetch(`/api/transactions?start_date=${start}&end_date=${end}&per_page=1000`);
            const mData = await mRes.json();

            if (mData.success) {
                const total = mData.transactions.reduce((s, t) => s + t.amount, 0);
                monthEl.textContent = formatCurrency(total);
            }
        }

    } catch (error) {
        console.error('❌ Error loading stats:', error);
    }
}

// ============================================================================
// UTILS
// ============================================================================

function formatCurrency(amount) {
    return '₹' + Number(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 2
    });
}

console.log('✅ transactions.js loaded');
