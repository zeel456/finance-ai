// Global utilities and functions

// Toggle mobile menu
function toggleMenu() {
    const menu = document.getElementById('navMenu');
    if (menu) {
        menu.classList.toggle('active');
    }
}

// Format currency with Indian Rupee symbol
function formatCurrency(amount, currency = 'INR') {
    const numAmount = parseFloat(amount) || 0;
    return '₹' + numAmount.toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Format date to readable format
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Show notification toast
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span class="notification-icon">${getNotificationIcon(type)}</span>
        <span class="notification-message">${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Hide and remove notification
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Get notification icon based on type
function getNotificationIcon(type) {
    const icons = {
        'success': '✓',
        'error': '✕',
        'warning': '⚠',
        'info': 'ℹ'
    };
    return icons[type] || icons['info'];
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Add notification styles dynamically
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateX(400px);
        transition: transform 0.3s ease;
        z-index: 1000;
        max-width: 350px;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .notification.show {
        transform: translateX(0);
    }
    
    .notification-icon {
        font-size: 1.25rem;
        font-weight: bold;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        flex-shrink: 0;
    }
    
    .notification-message {
        flex: 1;
    }
    
    .notification-success {
        border-left: 4px solid #10b981;
    }
    
    .notification-success .notification-icon {
        background: #D1FAE5;
        color: #10b981;
    }
    
    .notification-error {
        border-left: 4px solid #ef4444;
    }
    
    .notification-error .notification-icon {
        background: #FEE2E2;
        color: #ef4444;
    }
    
    .notification-warning {
        border-left: 4px solid #f59e0b;
    }
    
    .notification-warning .notification-icon {
        background: #FEF3C7;
        color: #f59e0b;
    }
    
    .notification-info {
        border-left: 4px solid #3b82f6;
    }
    
    .notification-info .notification-icon {
        background: #DBEAFE;
        color: #3b82f6;
    }
    
    .nav-toggle {
        display: none;
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        color: var(--dark);
        padding: 0.5rem;
    }
    
    @media (max-width: 768px) {
        .nav-toggle {
            display: block;
        }
        
        .nav-menu {
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            flex-direction: column;
            padding: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            gap: 0.5rem;
        }
        
        .nav-menu.active {
            display: flex;
        }
        
        .notification {
            right: 10px;
            left: 10px;
            max-width: calc(100% - 20px);
        }
    }
`;
document.head.appendChild(notificationStyles);

// Log that main.js is loaded
console.log('✅ Main.js loaded successfully');

// Close mobile menu when clicking outside
document.addEventListener('click', (e) => {
    const menu = document.getElementById('navMenu');
    const toggle = document.querySelector('.nav-toggle');
    
    if (menu && toggle && menu.classList.contains('active')) {
        if (!menu.contains(e.target) && !toggle.contains(e.target)) {
            menu.classList.remove('active');
        }
    }
});