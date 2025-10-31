// Main JavaScript for InventoryPro

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    console.log('InventoryPro initialized');
    
    // Initialize tooltips
    initTooltips();
    
    // Initialize auto-hide messages
    autoHideMessages();
    
    // Initialize search debounce
    initSearchDebounce();
    
    // Initialize confirmation dialogs
    initConfirmDialogs();
});

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

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type} fixed bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 z-50 animate-slide-in-right`;
    
    const icon = {
        'success': '<i class="fas fa-check-circle text-green-500 mr-2"></i>',
        'error': '<i class="fas fa-exclamation-circle text-red-500 mr-2"></i>',
        'warning': '<i class="fas fa-exclamation-triangle text-yellow-500 mr-2"></i>',
        'info': '<i class="fas fa-info-circle text-blue-500 mr-2"></i>'
    }[type] || '';
    
    toast.innerHTML = `
        <div class="flex items-center">
            ${icon}
            <span class="text-gray-800">${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-gray-400 hover:text-gray-600">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.transition = 'opacity 0.3s ease-out';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Format currency (Indonesian Rupiah)
function formatCurrency(amount) {
    return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR',
        minimumFractionDigits: 0
    }).format(amount);
}

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

// Export table to CSV
function exportTableToCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        
        cols.forEach(col => {
            let data = col.textContent.trim();
            data = data.replace(/"/g, '""'); // Escape quotes
            rowData.push(`"${data}"`);
        });
        
        csv.push(rowData.join(','));
    });
    
    downloadCSV(csv.join('
'), filename);
}

// Download CSV
function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
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
function showLoader() {
    const loader = document.createElement('div');
    loader.id = 'global-loader';
    loader.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    loader.innerHTML = `
        <div class="bg-white rounded-lg p-8">
            <div class="loading mx-auto mb-4"></div>
            <p class="text-gray-700">Loading...</p>
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

// AJAX helper
async function fetchData(url, options = {}) {
    try {
        showLoader();
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
            
            // Show error message
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

// Local storage helpers
const storage = {
    set(key, value) {
        localStorage.setItem(key, JSON.stringify(value));
    },
    
    get(key) {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : null;
    },
    
    remove(key) {
        localStorage.removeItem(key);
    },
    
    clear() {
        localStorage.clear();
    }
};

// Export functions for global use
window.showToast = showToast;
window.copyToClipboard = copyToClipboard;
window.exportTableToCSV = exportTableToCSV;
window.printPage = printPage;
window.scrollToElement = scrollToElement;
window.toggleElement = toggleElement;
window.showLoader = showLoader;
window.hideLoader = hideLoader;
window.fetchData = fetchData;
window.validateForm = validateForm;
window.storage = storage;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;