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
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('transaction_date').value = today;
}

// ============================================================================
// LOAD DATA
// ============================================================================

async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const categories = await response.json();
        allCategories = categories;
        
        // Populate category dropdowns
        const categorySelects = ['category_id', 'filterCategory'];
        
        categorySelects.forEach(selectId => {
            const select = document.getElementById(selectId);
            if (select) {
                const isFilter = selectId === 'filterCategory';
                select.innerHTML = isFilter ? '<option value="">All Categories</option>' : '<option value="">Select Category</option>';
                
                categories.forEach(cat => {
                    const option = document.createElement('option');
                    option.value = cat.id;
                    option.textContent = cat.name;
                    select.appendChild(option);
                });
            }
        });
        
        console.log('✅ Categories loaded:', categories.length);
        
    } catch (error) {
        console.error('❌ Error loading categories:', error);
        showNotification('Failed to load categories', 'error');
    }
}

async function loadTransactions(page = 1) {
    try {
        currentPage = page;
        const tableBody = document.getElementById('transactionsTableBody');
        tableBody.innerHTML = '<tr><td colspan="7" class="loading-spinner"><div>⏳ Loading...</div></td></tr>';
        
        // Build query string with filters
        const params = new URLSearchParams({
            page: page,
            per_page: 20
        });
        
        const categoryFilter = document.getElementById('filterCategory')?.value;
        const startDate = document.getElementById('filterStartDate')?.value;
        const endDate = document.getElementById('filterEndDate')?.value;
        const paymentMethod = document.getElementById('filterPaymentMethod')?.value;
        
        if (categoryFilter) params.append('category_id', categoryFilter);
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        if (paymentMethod) params.append('payment_method', paymentMethod);
        
        const response = await fetch(`/api/transactions?${params}`);
        const data = await response.json();
        
        if (data.success && data.transactions.length > 0) {
            displayTransactions(data.transactions);
            updatePagination(data.page, data.pages, data.total);
        } else {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-state">
                        <div class="empty-state-icon">📭</div>
                        <p>No transactions found</p>
                        <button class="btn-primary" onclick="showAddTransactionModal()">
                            Add Your First Transaction
                        </button>
                    </td>
                </tr>
            `;
            document.getElementById('paginationContainer').style.display = 'none';
        }
        
        console.log('✅ Transactions loaded:', data.transactions?.length || 0);
        
    } catch (error) {
        console.error('❌ Error loading transactions:', error);
        const tableBody = document.getElementById('transactionsTableBody');
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-state">
                    <div class="empty-state-icon">⚠️</div>
                    <p>Error loading transactions</p>
                    <button class="btn-secondary" onclick="loadTransactions()">Try Again</button>
                </td>
            </tr>
        `;
    }
}

function displayTransactions(transactions) {
    const tableBody = document.getElementById('transactionsTableBody');
    
    tableBody.innerHTML = transactions.map(t => `
        <tr>
            <td>${t.date || 'N/A'}</td>
            <td><strong>${t.vendor}</strong></td>
            <td class="amount-cell">₹${parseFloat(t.amount).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
            <td><span class="category-badge">${t.category}</span></td>
            <td><span class="payment-badge">${t.payment_method || 'N/A'}</span></td>
            <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${t.description || '-'}">
                ${t.description || '-'}
            </td>
            <td>
                <div class="action-buttons">
                    <button class="btn-icon edit" onclick="editTransaction(${t.id})" title="Edit">
                        ✏️
                    </button>
                    <button class="btn-icon delete" onclick="deleteTransaction(${t.id}, '${t.vendor}')" title="Delete">
                        🗑️
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('totalTransactions').textContent = stats.transaction_count || 0;
        document.getElementById('totalAmount').textContent = formatCurrency(stats.total_expenses || 0);
        document.getElementById('avgTransaction').textContent = formatCurrency(
            stats.transaction_count > 0 ? (stats.total_expenses / stats.transaction_count) : 0
        );
        
        // Get this month's total
        const today = new Date();
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
        const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        
        const monthResponse = await fetch(
            `/api/transactions?start_date=${firstDay.toISOString().split('T')[0]}&end_date=${lastDay.toISOString().split('T')[0]}&per_page=1000`
        );
        const monthData = await monthResponse.json();
        
        if (monthData.success) {
            const monthTotal = monthData.transactions.reduce((sum, t) => sum + t.amount, 0);
            document.getElementById('thisMonth').textContent = formatCurrency(monthTotal);
        }
        
    } catch (error) {
        console.error('❌ Error loading stats:', error);
    }
}

// ============================================================================
// ADD/EDIT TRANSACTION
// ============================================================================

function showAddTransactionModal() {
    currentTransactionId = null;
    document.getElementById('modalTitle').textContent = 'Add Transaction';
    document.getElementById('saveButtonText').textContent = 'Save Transaction';
    document.getElementById('transactionForm').reset();
    setDefaultDate();
    document.getElementById('transactionModal').style.display = 'flex';
}

async function editTransaction(id) {
    try {
        // Fetch transaction details
        const response = await fetch(`/api/transactions?page=1&per_page=1000`);
        const data = await response.json();
        
        if (!data.success) {
            showNotification('Failed to load transaction', 'error');
            return;
        }
        
        const transaction = data.transactions.find(t => t.id === id);
        
        if (!transaction) {
            showNotification('Transaction not found', 'error');
            return;
        }
        
        // Populate form
        currentTransactionId = id;
        document.getElementById('modalTitle').textContent = 'Edit Transaction';
        document.getElementById('saveButtonText').textContent = 'Update Transaction';
        
        document.getElementById('amount').value = transaction.amount;
        document.getElementById('vendor_name').value = transaction.vendor;
        document.getElementById('transaction_date').value = transaction.date;
        
        // Find and select category
        const categorySelect = document.getElementById('category_id');
        const categoryOption = Array.from(categorySelect.options).find(
            opt => opt.textContent === transaction.category
        );
        if (categoryOption) {
            categorySelect.value = categoryOption.value;
        }
        
        document.getElementById('payment_method').value = transaction.payment_method || 'Other';
        document.getElementById('description').value = transaction.description || '';
        document.getElementById('tax_amount').value = transaction.tax_amount || 0;
        
        document.getElementById('transactionModal').style.display = 'flex';
        
    } catch (error) {
        console.error('❌ Error editing transaction:', error);
        showNotification('Failed to load transaction', 'error');
    }
}

async function saveTransaction() {
    const formData = {
        amount: parseFloat(document.getElementById('amount').value),
        vendor_name: document.getElementById('vendor_name').value.trim(),
        transaction_date: document.getElementById('transaction_date').value,
        category_id: parseInt(document.getElementById('category_id').value),
        payment_method: document.getElementById('payment_method').value,
        description: document.getElementById('description').value.trim(),
        tax_amount: parseFloat(document.getElementById('tax_amount').value) || 0
    };
    
    // Validate
    if (!formData.amount || formData.amount <= 0) {
        showNotification('Please enter a valid amount', 'error');
        return;
    }
    
    if (!formData.vendor_name) {
        showNotification('Please enter vendor name', 'error');
        return;
    }
    
    if (!formData.category_id) {
        showNotification('Please select a category', 'error');
        return;
    }
    
    try {
        const url = currentTransactionId 
            ? `/api/transactions/${currentTransactionId}`
            : '/api/transactions';
        
        const method = currentTransactionId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(
                currentTransactionId ? 'Transaction updated successfully!' : 'Transaction added successfully!',
                'success'
            );
            closeTransactionModal();
            loadTransactions(currentPage);
            loadStats();
        } else {
            showNotification(data.error || 'Failed to save transaction', 'error');
        }
        
    } catch (error) {
        console.error('❌ Error saving transaction:', error);
        showNotification('Failed to save transaction', 'error');
    }
}

// ============================================================================
// DELETE TRANSACTION
// ============================================================================

async function deleteTransaction(id, vendorName) {
    if (!confirm(`Delete transaction from "${vendorName}"?\n\nThis action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/transactions/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Transaction deleted successfully', 'success');
            loadTransactions(currentPage);
            loadStats();
        } else {
            showNotification(data.error || 'Failed to delete transaction', 'error');
        }
        
    } catch (error) {
        console.error('❌ Error deleting transaction:', error);
        showNotification('Failed to delete transaction', 'error');
    }
}

// ============================================================================
// FILTERS
// ============================================================================

function applyFilters() {
    currentPage = 1;
    loadTransactions(1);
}

function clearFilters() {
    document.getElementById('filterCategory').value = '';
    document.getElementById('filterStartDate').value = '';
    document.getElementById('filterEndDate').value = '';
    document.getElementById('filterPaymentMethod').value = '';
    loadTransactions(1);
}

// ============================================================================
// PAGINATION
// ============================================================================

function updatePagination(page, pages, total) {
    totalPages = pages;
    currentPage = page;
    
    document.getElementById('currentPage').textContent = page;
    document.getElementById('totalPages').textContent = pages;
    
    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');
    
    prevButton.disabled = page <= 1;
    nextButton.disabled = page >= pages;
    
    document.getElementById('paginationContainer').style.display = 'flex';
}

function previousPage() {
    if (currentPage > 1) {
        loadTransactions(currentPage - 1);
    }
}

function nextPage() {
    if (currentPage < totalPages) {
        loadTransactions(currentPage + 1);
    }
}

// ============================================================================
// MODAL CONTROLS
// ============================================================================

function closeTransactionModal() {
    document.getElementById('transactionModal').style.display = 'none';
    document.getElementById('transactionForm').reset();
    currentTransactionId = null;
}

// Close modal on ESC key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeTransactionModal();
    }
});

// Close modal on outside click
document.getElementById('transactionModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'transactionModal') {
        closeTransactionModal();
    }
});

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

console.log('✅ transactions.js loaded successfully');