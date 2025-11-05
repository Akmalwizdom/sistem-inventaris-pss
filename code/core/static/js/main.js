// Main JavaScript for InventoryPro

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    console.log('InventoryPro initialized');
    
    // Format all currency elements
    formatAllCurrencies();
    
    // Initialize tooltips
    initTooltips();
    
    // Initialize auto-hide messages
    autoHideMessages();
    
    // Initialize search debounce
    initSearchDebounce();
    
    // Initialize confirmation dialogs
    initConfirmDialogs();
    
    // Initialize number animations for countup elements
    initCountUpAnimations();
    
    // Format mini currencies (K, M format)
    formatMiniCurrencies();
});

// ========== CURRENCY FORMATTING ==========

// Format currency (Indonesian Rupiah)
function formatCurrency(amount) {
    if (amount === null || amount === undefined) return 'Rp 0';
    
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
    
    if (isNaN(numAmount)) return 'Rp 0';
    
    return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(numAmount);
}

// Format all elements with .currency class
function formatAllCurrencies() {
    document.querySelectorAll('.currency').forEach(el => {
        const value = parseFloat(el.textContent.trim());
        if (!isNaN(value)) {
            el.textContent = formatCurrency(value);
        }
    });
}

// Format currency to short form (K, M, B)
function formatCurrencyMini(amount) {
    if (amount === null || amount === undefined) return 'Rp 0';
    
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
    
    if (isNaN(numAmount)) return 'Rp 0';
    
    if (numAmount >= 1000000000) {
        return 'Rp ' + (numAmount / 1000000000).toFixed(1) + 'B';
    } else if (numAmount >= 1000000) {
        return 'Rp ' + (numAmount / 1000000).toFixed(1) + 'M';
    } else if (numAmount >= 1000) {
        return 'Rp ' + (numAmount / 1000).toFixed(0) + 'K';
    }
    
    return formatCurrency(numAmount);
}

// Format mini currencies (for compact display)
function formatMiniCurrencies() {
    document.querySelectorAll('.currency-mini').forEach(el => {
        const value = parseFloat(el.textContent.trim());
        if (!isNaN(value)) {
            if (value >= 1000000) {
                el.textContent = (value / 1000000).toFixed(1) + 'M';
            } else if (value >= 1000) {
                el.textContent = (value / 1000).toFixed(0) + 'K';
            } else {
                el.textContent = value.toLocaleString('id-ID');
            }
        }
    });
}

// ========== NUMBER ANIMATIONS ==========

// Initialize CountUp animations
function initCountUpAnimations() {
    const counters = document.querySelectorAll('[data-countup]');
    
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-countup'));
        const duration = 2000; // 2 seconds
        animateNumber(counter, target, duration);
    });
}

// Animate number from 0 to target
function animateNumber(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16); // 60fps
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = Math.round(target).toLocaleString('id-ID');
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current).toLocaleString('id-ID');
        }
    }, 16);
}

// Animate number with callback
function animateNumberWithCallback(element, start, end, duration, callback) {
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function (ease-out)
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = start + (end - start) * easeOut;
        
        element.textContent = Math.floor(current).toLocaleString('id-ID');
        
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.textContent = end.toLocaleString('id-ID');
            if (callback) callback();
        }
    }
    
    requestAnimationFrame(update);
}

// ========== CHART.JS UTILITIES ==========

// Chart color palette
const chartColors = {
    primary: '#0ea5e9',
    success: '#10b981',
    danger: '#ef4444',
    warning: '#f59e0b',
    info: '#3b82f6',
    purple: '#8b5cf6',
    pink: '#ec4899',
    cyan: '#06b6d4',
    indigo: '#6366f1',
    gray: '#6b7280'
};

// Generate random color
function getRandomColor() {
    const colors = Object.values(chartColors);
    return colors[Math.floor(Math.random() * colors.length)];
}

// Generate color palette
function generateColorPalette(count) {
    const colors = Object.values(chartColors);
    const palette = [];
    
    for (let i = 0; i < count; i++) {
        palette.push(colors[i % colors.length]);
    }
    
    return palette;
}

// Convert hex to rgba
function hexToRgba(hex, alpha = 1) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Chart.js default configuration
function getChartDefaults() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    padding: 15,
                    usePointStyle: true,
                    font: {
                        family: "'Inter', 'Segoe UI', sans-serif",
                        size: 12
                    }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12,
                titleColor: '#fff',
                bodyColor: '#fff',
                borderColor: 'rgba(255, 255, 255, 0.2)',
                borderWidth: 1,
                cornerRadius: 8,
                displayColors: true
            }
        },
        animation: {
            duration: 1000,
            easing: 'easeInOutQuart'
        }
    };
}

// ========== TOOLTIP FUNCTIONALITY ==========

// Tooltip initialization
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltipText = this.getAttribute('data-tooltip');
            const tooltip = createTooltip(tooltipText);
            this.appendChild(tooltip);
        });
        
        element.addEventListener('mouseleave', function() {
            const tooltip = this.querySelector('.tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        });
    });
}

// Create tooltip element
function createTooltip(text) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip absolute bg-gray-900 text-white text-xs rounded py-1 px-2 -top-8 left-1/2 transform -translate-x-1/2 whitespace-nowrap z-50';
    tooltip.textContent = text;
    
    // Add arrow
    const arrow = document.createElement('div');
    arrow.className = 'absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900';
    tooltip.appendChild(arrow);
    
    return tooltip;
}

// ========== MESSAGES & NOTIFICATIONS ==========

// Auto-hide Django messages
function autoHideMessages() {
    const messages = document.querySelectorAll('.alert, .message');
    
    messages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'opacity 0.5s ease-out';
            message.style.opacity = '0';
            
            setTimeout(() => {
                message.remove();
            }, 500);
        }, 5000);
        
        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '&times;';
        closeBtn.className = 'absolute top-2 right-2 text-2xl font-bold opacity-50 hover:opacity-100';
        closeBtn.onclick = () => message.remove();
        message.style.position = 'relative';
        message.appendChild(closeBtn);
    });
}

// Show toast notification
function showToast(message, type = 'info') {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(toastContainer);
    }
    
    const toast = document.createElement('div');
    const toastId = 'toast-' + Date.now();
    toast.id = toastId;
    
    const typeClasses = {
        'success': 'bg-green-500 text-white',
        'error': 'bg-red-500 text-white',
        'warning': 'bg-yellow-500 text-black',
        'info': 'bg-blue-500 text-white'
    };
    
    const icons = {
        'success': '✓',
        'error': '✕',
        'warning': '⚠',
        'info': 'ℹ'
    };
    
    toast.className = `${typeClasses[type] || typeClasses.info} px-4 py-3 rounded-lg shadow-lg flex items-center space-x-2 animate-slide-in transform transition-all duration-300`;
    
    toast.innerHTML = `
        <span class="font-bold text-lg">${icons[type] || icons.info}</span>
        <span>${message}</span>
        <button onclick="closeToast('${toastId}')" class="ml-2 font-bold hover:opacity-75 text-lg">×</button>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        closeToast(toastId);
    }, 5000);
}

function closeToast(toastId) {
    const toast = document.getElementById(toastId);
    if (toast) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }
}

// ========== SEARCH & FORMS ==========

// Search with debounce
function initSearchDebounce() {
    const searchInputs = document.querySelectorAll('input[type="search"], input[name="search"]');
    
    searchInputs.forEach(input => {
        let timeout;
        
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            
            const form = this.closest('form');
            if (!form) return;
            
            timeout = setTimeout(() => {
                // Auto-submit form after 500ms of no typing
                // Uncomment if you want auto-submit
                // form.submit();
            }, 500);
        });
    });
}

// Confirmation dialogs
function initConfirmDialogs() {
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Are you sure?';
            
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('border-red-500');
            
            const error = document.createElement('p');
            error.className = 'text-red-500 text-xs mt-1';
            error.textContent = 'This field is required';
            
            if (!input.nextElementSibling || !input.nextElementSibling.classList.contains('text-red-500')) {
                input.parentNode.appendChild(error);
            }
        } else {
            input.classList.remove('border-red-500');
            const error = input.nextElementSibling;
            if (error && error.classList.contains('text-red-500')) {
                error.remove();
            }
        }
    });
    
    return isValid;
}

// Calculate restock quantity
function calculateRestockQuantity(minStock, currentStock) {
    return Math.max(0, minStock - currentStock);
}

// ========== UTILITY FUNCTIONS ==========

// Format date (Indonesian)
function formatDate(date) {
    return new Intl.DateTimeFormat('id-ID', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    }).format(new Date(date));
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showToast('Failed to copy', 'error');
    });
}

// Print page
function printPage() {
    window.print();
}

// Smooth scroll to element
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Toggle element visibility
function toggleElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.toggle('hidden');
    }
}

// Loading spinner
function showLoader(message = 'Loading...') {
    const loader = document.createElement('div');
    loader.id = 'global-loader';
    loader.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    loader.innerHTML = `
        <div class="bg-white rounded-lg p-8 text-center">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent mb-4"></div>
            <p class="text-gray-700 font-medium">${message}</p>
        </div>
    `;
    document.body.appendChild(loader);
}

function hideLoader() {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.remove();
    }
}

// ========== AJAX HELPERS ==========

// AJAX helper
async function fetchData(url, options = {}) {
    try {
        showLoader('Fetching data...');
        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Fetch error:', error);
        showToast('Failed to fetch data', 'error');
        throw error;
    } finally {
        hideLoader();
    }
}

// POST request helper
async function postData(url, data) {
    return fetchData(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(data)
    });
}

// Get CSRF token from cookie
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ========== EXPORT FUNCTIONS ==========

// Export table to CSV
function exportTableToCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) {
        showToast('Table not found', 'error');
        return;
    }
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const csvRow = [];
        
        cols.forEach(col => {
            csvRow.push('"' + col.textContent.trim().replace(/"/g, '""') + '"');
        });
        
        csv.push(csvRow.join(','));
    });
    
    const csvContent = csv.join('');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showToast('Export successful!', 'success');
    }
}

// ========== LOCAL STORAGE ==========

// Local storage helpers
const storage = {
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('LocalStorage error:', e);
            return false;
        }
    },
    
    get(key) {
        try {
            const value = localStorage.getItem(key);
            return value ? JSON.parse(value) : null;
        } catch (e) {
            console.error('LocalStorage error:', e);
            return null;
        }
    },
    
    remove(key) {
        localStorage.removeItem(key);
    },
    
    clear() {
        localStorage.clear();
    }
};

// ========== EXPORT TO GLOBAL SCOPE ==========

// Export functions for global use
window.showToast = showToast;
window.closeToast = closeToast;
window.copyToClipboard = copyToClipboard;
window.exportTableToCSV = exportTableToCSV;
window.printPage = printPage;
window.scrollToElement = scrollToElement;
window.toggleElement = toggleElement;
window.showLoader = showLoader;
window.hideLoader = hideLoader;
window.fetchData = fetchData;
window.postData = postData;
window.validateForm = validateForm;
window.storage = storage;
window.formatCurrency = formatCurrency;
window.formatCurrencyMini = formatCurrencyMini;
window.formatDate = formatDate;
window.animateNumber = animateNumber;
window.animateNumberWithCallback = animateNumberWithCallback;

// Chart.js utilities
window.chartColors = chartColors;
window.getRandomColor = getRandomColor;
window.generateColorPalette = generateColorPalette;
window.hexToRgba = hexToRgba;
window.getChartDefaults = getChartDefaults;

// Add custom CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slide-in {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .animate-slide-in {
        animation: slide-in 0.3s ease-out;
    }
    
    @keyframes pulse-scale {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
    }
    
    .animate-pulse-scale {
        animation: pulse-scale 2s infinite;
    }
    
    @keyframes fade-in {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
    
    .animate-fade-in {
        animation: fade-in 0.5s ease-in;
    }
`;
document.head.appendChild(style);

console.log('✅ InventoryPro main.js loaded successfully');