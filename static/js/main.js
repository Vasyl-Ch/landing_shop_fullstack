/**
 * Main JavaScript - E-Commerce Store
 * Common functionality across all pages
 */

// ========================================
// CONFIGURATION
// ========================================
const API_BASE_URL = window.location.origin; // Adjust if Django backend is on different domain
const TOAST_DURATION = 5000; // 5 seconds

// ========================================
// TOAST NOTIFICATIONS
// ========================================
const Toast = {
    container: null,
    
    init() {
        this.container = document.getElementById('toastContainer');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toastContainer';
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },
    
    show(message, type = 'info') {
        this.init();
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-content">${message}</div>
            <button class="toast-close" aria-label="Закрыть">×</button>
        `;
        
        this.container.appendChild(toast);
        
        // Close button
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.remove(toast));
        
        // Auto remove
        setTimeout(() => this.remove(toast), TOAST_DURATION);
    },
    
    remove(toast) {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    },
    
    success(message) {
        this.show(message, 'success');
    },
    
    error(message) {
        this.show(message, 'error');
    },
    
    warning(message) {
        this.show(message, 'warning');
    },
    
    info(message) {
        this.show(message, 'info');
    }
};

// Make Toast available globally
window.Toast = Toast;

// ========================================
// DROPDOWN MENUS
// ========================================
class DropdownManager {
    constructor() {
        this.activeDropdown = null;
        this.init();
    }
    
    init() {
        // Catalog dropdown
        const catalogBtn = document.getElementById('catalogBtn');
        const catalogMenu = document.getElementById('catalogMenu');
        
        if (catalogBtn && catalogMenu) {
            catalogBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggle(catalogMenu);
            });
        }
        
        // Profile dropdown
        const profileBtn = document.getElementById('profileBtn');
        const profileMenu = document.getElementById('profileMenu');
        
        if (profileBtn && profileMenu) {
            profileBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggle(profileMenu);
            });
        }
        
        // Close dropdowns on outside click
        document.addEventListener('click', () => this.closeAll());
    }
    
    toggle(menu) {
        if (this.activeDropdown && this.activeDropdown !== menu) {
            this.close(this.activeDropdown);
        }
        
        menu.classList.toggle('show');
        this.activeDropdown = menu.classList.contains('show') ? menu : null;
    }
    
    close(menu) {
        menu.classList.remove('show');
        if (this.activeDropdown === menu) {
            this.activeDropdown = null;
        }
    }
    
    closeAll() {
        document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
            this.close(menu);
        });
    }
}

// ========================================
// SEARCH FORM
// ========================================
class SearchManager {
    constructor() {
        this.searchBtn = document.getElementById('searchBtn');
        this.searchForm = document.getElementById('searchForm');
        this.closeSearchBtn = document.getElementById('closeSearchBtn');
        this.init();
    }
    
    init() {
        if (this.searchBtn && this.searchForm) {
            this.searchBtn.addEventListener('click', () => this.toggle());
        }
        
        if (this.closeSearchBtn) {
            this.closeSearchBtn.addEventListener('click', () => this.close());
        }
    }
    
    toggle() {
        if (this.searchForm.style.display === 'none' || !this.searchForm.style.display) {
            this.open();
        } else {
            this.close();
        }
    }
    
    open() {
        this.searchForm.style.display = 'block';
        const input = this.searchForm.querySelector('input[type="search"]');
        if (input) input.focus();
    }
    
    close() {
        this.searchForm.style.display = 'none';
    }
}

// ========================================
// MOBILE MENU
// ========================================
class MobileMenuManager {
    constructor() {
        this.menuBtn = document.getElementById('mobileMenuBtn');
        this.init();
    }
    
    init() {
        if (this.menuBtn) {
            this.menuBtn.addEventListener('click', () => this.toggle());
        }
    }
    
    toggle() {
        const headerNav = document.querySelector('.header-nav');
        if (headerNav) {
            headerNav.classList.toggle('mobile-open');
            document.body.classList.toggle('menu-open');
        }
    }
}

// ========================================
// FORM VALIDATION
// ========================================
class FormValidator {
    static validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    static validatePhone(phone) {
        const re = /^[\d\s\+\-\(\)]+$/;
        return phone.length >= 10 && re.test(phone);
    }
    
    static validateRequired(value) {
        return value.trim().length > 0;
    }
    
    static validatePassword(password) {
        return password.length >= 8;
    }
    
    static showError(input, message) {
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;
        
        // Remove existing error
        const existingError = formGroup.querySelector('.form-error');
        if (existingError) existingError.remove();
        
        // Add error class
        input.classList.add('error');
        input.classList.remove('success');
        
        // Add error message
        const error = document.createElement('span');
        error.className = 'form-error';
        error.textContent = message;
        formGroup.appendChild(error);
    }
    
    static showSuccess(input) {
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;
        
        // Remove error
        const existingError = formGroup.querySelector('.form-error');
        if (existingError) existingError.remove();
        
        // Add success class
        input.classList.remove('error');
        input.classList.add('success');
    }
    
    static clearValidation(input) {
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;
        
        const existingError = formGroup.querySelector('.form-error');
        if (existingError) existingError.remove();
        
        input.classList.remove('error', 'success');
    }
}

// Make FormValidator available globally
window.FormValidator = FormValidator;

// ========================================
// QUANTITY INPUT
// ========================================
class QuantityInput {
    constructor(element) {
        this.container = element;
        this.input = element.querySelector('.quantity-value');
        this.decreaseBtn = element.querySelector('.quantity-btn[data-action="decrease"]');
        this.increaseBtn = element.querySelector('.quantity-btn[data-action="increase"]');
        this.min = parseInt(this.input.min) || 1;
        this.max = parseInt(this.input.max) || 9999;
        this.init();
    }
    
    init() {
        if (this.decreaseBtn) {
            this.decreaseBtn.addEventListener('click', () => this.decrease());
        }
        
        if (this.increaseBtn) {
            this.increaseBtn.addEventListener('click', () => this.increase());
        }
        
        if (this.input) {
            this.input.addEventListener('change', () => this.validate());
        }
    }
    
    getValue() {
        return parseInt(this.input.value) || this.min;
    }
    
    setValue(value) {
        const newValue = Math.max(this.min, Math.min(this.max, parseInt(value) || this.min));
        this.input.value = newValue;
        this.updateButtons();
        
        // Dispatch change event
        this.input.dispatchEvent(new Event('change', { bubbles: true }));
    }
    
    decrease() {
        this.setValue(this.getValue() - 1);
    }
    
    increase() {
        this.setValue(this.getValue() + 1);
    }
    
    validate() {
        this.setValue(this.getValue());
    }
    
    updateButtons() {
        const value = this.getValue();
        
        if (this.decreaseBtn) {
            this.decreaseBtn.disabled = value <= this.min;
        }
        
        if (this.increaseBtn) {
            this.increaseBtn.disabled = value >= this.max;
        }
    }
}

// ========================================
// MODAL
// ========================================
class Modal {
    constructor(id) {
        this.id = id;
        this.overlay = null;
        this.modal = null;
    }
    
    create(title, content, footer = '') {
        const overlayHTML = `
            <div class="modal-overlay" id="${this.id}">
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">${title}</h3>
                        <button class="modal-close" data-dismiss="modal">×</button>
                    </div>
                    <div class="modal-body">${content}</div>
                    ${footer ? `<div class="modal-footer">${footer}</div>` : ''}
                </div>
            </div>
        `;
        
        const temp = document.createElement('div');
        temp.innerHTML = overlayHTML;
        this.overlay = temp.firstElementChild;
        document.body.appendChild(this.overlay);
        
        this.modal = this.overlay.querySelector('.modal');
        this.bindEvents();
    }
    
    bindEvents() {
        // Close button
        const closeBtn = this.overlay.querySelector('[data-dismiss="modal"]');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }
        
        // Click outside
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.close();
            }
        });
        
        // Escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                this.close();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
    }
    
    show() {
        if (this.overlay) {
            this.overlay.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }
    
    close() {
        if (this.overlay) {
            this.overlay.style.animation = 'fadeIn 0.3s ease-out reverse';
            setTimeout(() => {
                this.overlay.remove();
                document.body.style.overflow = '';
            }, 300);
        }
    }
    
    static confirm(title, message, onConfirm, onCancel = null) {
        const modal = new Modal('confirmModal');
        const footer = `
            <button class="btn btn-secondary" data-action="cancel">Отмена</button>
            <button class="btn btn-danger" data-action="confirm">Подтвердить</button>
        `;
        
        modal.create(title, `<p>${message}</p>`, footer);
        modal.show();
        
        const confirmBtn = modal.overlay.querySelector('[data-action="confirm"]');
        const cancelBtn = modal.overlay.querySelector('[data-action="cancel"]');
        
        confirmBtn.addEventListener('click', () => {
            modal.close();
            if (onConfirm) onConfirm();
        });
        
        cancelBtn.addEventListener('click', () => {
            modal.close();
            if (onCancel) onCancel();
        });
    }
}

// Make Modal available globally
window.Modal = Modal;

// ========================================
// API HELPER
// ========================================
class API {
    static async request(url, options = {}) {
        // Try multiple methods to get CSRF token
        let csrfToken = null;
        
        // Method 1: From cookie
        csrfToken = this.getCookie('csrftoken');
        
        // Method 2: From meta tag
        if (!csrfToken) {
            const metaTag = document.querySelector('meta[name="csrf-token"]');
            if (metaTag) {
                csrfToken = metaTag.getAttribute('content');
            }
        }
        
        // Method 3: From hidden input
        if (!csrfToken) {
            const hiddenInput = document.querySelector('[name=csrfmiddlewaretoken]');
            if (hiddenInput) {
                csrfToken = hiddenInput.value;
            }
        }
        
        // Debug: Log CSRF token
        console.log('CSRF Token:', csrfToken ? `${csrfToken.substring(0, 10)}...` : 'NOT FOUND');
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken || '',
            },
            credentials: 'same-origin',
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, config);
            
            // Handle CSRF error specifically
            if (response.status === 403) {
                const errorText = await response.text();
                if (errorText.includes('CSRF verification failed')) {
                    throw new Error('CSRF токен недействителен. Пожалуйста, перезагрузите страницу.');
                }
            }
            
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") === -1) {
                throw new Error('Сервер вернул HTML вместо JSON. Возможно, произошла ошибка.');
            }
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Ошибка запроса');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
    
    static get(url) {
        return this.request(url, { method: 'GET' });
    }
    
    static post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }
    
    static put(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }
    
    static delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
    
    static getCookie(name) {
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
}

// Make API available globally
window.API = API;

// ========================================
// UTILITIES
// ========================================
const Utils = {
    formatPrice(price) {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            minimumFractionDigits: 0,
            maximumFractionDigits: 2,
        }).format(price);
    },
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
        });
    },
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
};

// Make Utils available globally
window.Utils = Utils;

// ========================================
// INITIALIZE ON DOM READY
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    // Initialize managers
    new DropdownManager();
    new SearchManager();
    new MobileMenuManager();
    
    // Initialize quantity inputs ONLY for non-cart inputs
    document.querySelectorAll('.quantity-input').forEach(element => {
        const cartInput = element.querySelector('.cart-quantity-input');
        if (!cartInput) {
            // Only initialize QuantityInput for non-cart inputs
            new QuantityInput(element);
        }
    });
    
    // Show Django messages as toasts
    const djangoMessages = document.querySelectorAll('.django-message');
    djangoMessages.forEach(msg => {
        const type = msg.dataset.type || 'info';
        const message = msg.textContent;
        Toast.show(message, type);
        msg.remove();
    });
    
    console.log('E-Commerce Frontend initialized');
});
