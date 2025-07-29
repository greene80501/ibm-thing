// Enhanced Main JavaScript for Alice Insight Suite
// File: static/js/main.js

// Global utility functions and common functionality
(function() {
    'use strict';

    // Global app configuration
    window.AliceInsight = {
        version: '2.0.0',
        debug: true,
        api: {
            baseUrl: '',
            timeout: 30000,
            retryAttempts: 3
        },
        ui: {
            animationDuration: 300,
            toastDuration: 5000,
            loadingDelay: 200
        }
    };

    // Initialize app when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeApp();
    });

    function initializeApp() {
        console.log('%c🚀 Alice Insight Suite v' + window.AliceInsight.version, 'color: #10b981; font-size: 16px; font-weight: bold;');
        
        setupGlobalEventListeners();
        initializeNotificationSystem();
        setupLoadingSystem();
        initializeFormValidation();
        setupNavigationEnhancements();
        checkAuthStatus();
        
        // Show welcome message if user just logged in
        if (localStorage.getItem('justLoggedIn') === 'true') {
            showWelcomeMessage();
            localStorage.removeItem('justLoggedIn');
        }
    }

    // ===== NOTIFICATION SYSTEM =====
    function initializeNotificationSystem() {
        // Create notification container if it doesn't exist
        if (!document.getElementById('notification-container')) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'fixed top-4 right-4 z-50 max-w-sm space-y-3';
            document.body.appendChild(container);
        }
        
        // Style notification container
        const style = document.createElement('style');
        style.textContent = `
            .notification {
                transform: translateX(100%);
                transition: transform 0.3s ease;
                padding: 1rem;
                border-radius: 0.75rem;
                backdrop-filter: blur(10px);
                border: 1px solid;
                max-width: 24rem;
                word-wrap: break-word;
            }
            
            .notification.show {
                transform: translateX(0);
            }
            
            .notification.success {
                background: rgba(16, 185, 129, 0.9);
                border-color: rgba(16, 185, 129, 1);
                color: white;
            }
            
            .notification.error {
                background: rgba(239, 68, 68, 0.9);
                border-color: rgba(239, 68, 68, 1);
                color: white;
            }
            
            .notification.warning {
                background: rgba(245, 158, 11, 0.9);
                border-color: rgba(245, 158, 11, 1);
                color: white;
            }
            
            .notification.info {
                background: rgba(59, 130, 246, 0.9);
                border-color: rgba(59, 130, 246, 1);
                color: white;
            }
        `;
        document.head.appendChild(style);
    }

    // Enhanced notification function
    window.showNotification = function(message, type = 'info', options = {}) {
        const {
            duration = window.AliceInsight.ui.toastDuration,
            dismissible = true,
            persistent = false,
            onclick = null
        } = options;

        const container = document.getElementById('notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-times-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <i class="${icons[type] || icons.info} mr-2"></i>
                    <span class="font-medium text-sm">${message}</span>
                </div>
                ${dismissible ? `
                    <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white/80 hover:text-white transition-colors">
                        <i class="fas fa-times"></i>
                    </button>
                ` : ''}
            </div>
        `;

        if (onclick) {
            notification.style.cursor = 'pointer';
            notification.addEventListener('click', onclick);
        }

        container.appendChild(notification);

        // Show notification with animation
        setTimeout(() => notification.classList.add('show'), 100);

        // Auto-remove if not persistent
        if (!persistent) {
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }, duration);
        }

        return notification;
    };

    // ===== LOADING SYSTEM =====
    function setupLoadingSystem() {
        // Create global loading overlay if it doesn't exist
        if (!document.getElementById('global-loading-overlay')) {
            const overlay = document.createElement('div');
            overlay.id = 'global-loading-overlay';
            overlay.className = 'fixed inset-0 bg-slate-900/80 backdrop-blur-sm flex items-center justify-center z-50 hidden';
            overlay.innerHTML = `
                <div class="text-center">
                    <div class="inline-block w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mb-4"></div>
                    <p class="text-white font-medium" id="global-loading-text">Loading...</p>
                </div>
            `;
            document.body.appendChild(overlay);
        }
    }

    window.showLoading = function(text = 'Loading...') {
        const overlay = document.getElementById('global-loading-overlay');
        const textElement = document.getElementById('global-loading-text');
        
        if (textElement) textElement.textContent = text;
        if (overlay) overlay.classList.remove('hidden');
    };

    window.hideLoading = function() {
        const overlay = document.getElementById('global-loading-overlay');
        if (overlay) overlay.classList.add('hidden');
    };

    // ===== API UTILITIES =====
    window.apiRequest = async function(url, options = {}) {
        const {
            method = 'GET',
            data = null,
            headers = {},
            timeout = window.AliceInsight.api.timeout,
            retries = window.AliceInsight.api.retryAttempts,
            showLoading: shouldShowLoading = false,
            loadingText = 'Processing...'
        } = options;

        if (shouldShowLoading) {
            window.showLoading(loadingText);
        }

        const defaultHeaders = {
            'Content-Type': 'application/json',
            ...headers
        };

        const requestOptions = {
            method,
            headers: defaultHeaders,
            credentials: 'same-origin'
        };

        if (data && method !== 'GET') {
            requestOptions.body = JSON.stringify(data);
        }

        let lastError;
        
        for (let attempt = 1; attempt <= retries; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), timeout);
                
                requestOptions.signal = controller.signal;
                
                const response = await fetch(url, requestOptions);
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
                }
                
                const result = await response.json();
                
                if (shouldShowLoading) {
                    window.hideLoading();
                }
                
                return result;
                
            } catch (error) {
                lastError = error;
                
                if (window.AliceInsight.debug) {
                    console.warn(`API request attempt ${attempt} failed:`, error);
                }
                
                // Don't retry on certain errors
                if (error.name === 'AbortError' || error.message.includes('401') || error.message.includes('403')) {
                    break;
                }
                
                // Wait before retry (exponential backoff)
                if (attempt < retries) {
                    await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
                }
            }
        }
        
        if (shouldShowLoading) {
            window.hideLoading();
        }
        
        throw lastError;
    };

    // ===== FORM VALIDATION =====
    function initializeFormValidation() {
        // Enhanced form validation for all forms
        document.querySelectorAll('form').forEach(form => {
            setupFormValidation(form);
        });
    }

    function setupFormValidation(form) {
        if (form.hasAttribute('data-validation-setup')) return;
        form.setAttribute('data-validation-setup', 'true');

        // Real-time validation
        form.querySelectorAll('input, textarea, select').forEach(field => {
            field.addEventListener('blur', () => validateField(field));
            field.addEventListener('input', () => clearFieldError(field));
        });

        // Form submission validation
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showNotification('Please fix the errors in the form', 'error');
            }
        });
    }

    function validateField(field) {
        const rules = getValidationRules(field);
        const value = field.value.trim();
        
        for (const rule of rules) {
            if (!rule.test(value)) {
                showFieldError(field, rule.message);
                return false;
            }
        }
        
        showFieldSuccess(field);
        return true;
    }

    function getValidationRules(field) {
        const rules = [];
        
        // Required validation
        if (field.hasAttribute('required')) {
            rules.push({
                test: (value) => value.length > 0,
                message: 'This field is required'
            });
        }
        
        // Email validation
        if (field.type === 'email') {
            rules.push({
                test: (value) => !value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
                message: 'Please enter a valid email address'
            });
        }
        
        // URL validation
        if (field.type === 'url') {
            rules.push({
                test: (value) => !value || isValidUrl(value),
                message: 'Please enter a valid URL'
            });
        }
        
        // Min length validation
        const minLength = field.getAttribute('minlength');
        if (minLength) {
            rules.push({
                test: (value) => !value || value.length >= parseInt(minLength),
                message: `Must be at least ${minLength} characters long`
            });
        }
        
        return rules;
    }

    function showFieldError(field, message) {
        clearFieldState(field);
        field.classList.add('border-red-500', 'bg-red-50');
        
        let errorElement = field.parentNode.querySelector('.field-error');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'field-error text-red-500 text-sm mt-1';
            field.parentNode.appendChild(errorElement);
        }
        
        errorElement.textContent = message;
    }

    function showFieldSuccess(field) {
        clearFieldState(field);
        field.classList.add('border-green-500', 'bg-green-50');
    }

    function clearFieldError(field) {
        clearFieldState(field);
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.remove();
        }
    }

    function clearFieldState(field) {
        field.classList.remove('border-red-500', 'bg-red-50', 'border-green-500', 'bg-green-50');
    }

    function validateForm(form) {
        let isValid = true;
        const fields = form.querySelectorAll('input, textarea, select');
        
        fields.forEach(field => {
            if (!validateField(field)) {
                isValid = false;
            }
        });
        
        return isValid;
    }

    // ===== NAVIGATION ENHANCEMENTS =====
    function setupNavigationEnhancements() {
        // Active navigation highlighting
        highlightActiveNavigation();
        
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
        
        // Back to top button
        createBackToTopButton();
    }

    function highlightActiveNavigation() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link, nav a');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
                link.classList.add('active');
            }
        });
    }

    function createBackToTopButton() {
        const button = document.createElement('button');
        button.id = 'back-to-top';
        button.className = 'fixed bottom-6 right-6 w-12 h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg transition-all duration-300 z-40 opacity-0 pointer-events-none';
        button.innerHTML = '<i class="fas fa-arrow-up"></i>';
        button.title = 'Back to top';
        
        button.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        
        document.body.appendChild(button);
        
        // Show/hide button based on scroll position
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                button.classList.remove('opacity-0', 'pointer-events-none');
            } else {
                button.classList.add('opacity-0', 'pointer-events-none');
            }
        });
    }

    // ===== AUTHENTICATION =====
    function checkAuthStatus() {
        // Check if user is authenticated (this is just a client-side check)
        const userEmail = localStorage.getItem('userEmail');
        if (userEmail) {
            updateUIForAuthenticatedUser(userEmail);
        }
    }

    function updateUIForAuthenticatedUser(email) {
        // Update user display elements
        const userDisplays = document.querySelectorAll('.user-email');
        userDisplays.forEach(element => {
            element.textContent = email;
        });
        
        // Update avatar with user initials
        const avatars = document.querySelectorAll('.user-avatar');
        avatars.forEach(avatar => {
            const initials = email.split('@')[0].substring(0, 2).toUpperCase();
            avatar.textContent = initials;
        });
    }

    function showWelcomeMessage() {
        const userEmail = localStorage.getItem('userEmail');
        const firstName = userEmail ? userEmail.split('@')[0] : 'there';
        
        showNotification(`Welcome back, ${firstName}! 🎉`, 'success', {
            duration: 7000,
            onclick: () => {
                if (window.location.pathname === '/') {
                    // Scroll to recent activity or features
                    const target = document.querySelector('#recent-activity, .analysis-tools');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth' });
                    }
                }
            }
        });
    }

    // ===== UTILITY FUNCTIONS =====
    window.utils = {
        // Debounce function
        debounce: function(func, wait, immediate) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    timeout = null;
                    if (!immediate) func(...args);
                };
                const callNow = immediate && !timeout;
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
                if (callNow) func(...args);
            };
        },

        // Throttle function
        throttle: function(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        // Format number with K, M suffixes
        formatNumber: function(num) {
            if (num >= 1000000) {
                return (num / 1000000).toFixed(1) + 'M';
            } else if (num >= 1000) {
                return (num / 1000).toFixed(1) + 'K';
            }
            return num.toString();
        },

        // Format date
        formatDate: function(date, options = {}) {
            const defaultOptions = {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                ...options
            };
            
            if (typeof date === 'string') {
                date = new Date(date);
            }
            
            return date.toLocaleDateString('en-US', defaultOptions);
        },

        // Format relative time
        formatRelativeTime: function(date) {
            if (typeof date === 'string') {
                date = new Date(date);
            }
            
            const now = new Date();
            const diffInSeconds = Math.floor((now - date) / 1000);
            
            if (diffInSeconds < 60) return 'just now';
            if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} min ago`;
            if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hr ago`;
            if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`;
            
            return this.formatDate(date);
        },

        // Copy text to clipboard
        copyToClipboard: async function(text) {
            try {
                await navigator.clipboard.writeText(text);
                showNotification('Copied to clipboard!', 'success');
                return true;
            } catch (err) {
                console.error('Failed to copy text: ', err);
                showNotification('Failed to copy to clipboard', 'error');
                return false;
            }
        },

        // Download data as file
        downloadAsFile: function(data, filename, type = 'text/plain') {
            const blob = new Blob([data], { type });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        },

        // Validate URL
        isValidUrl: function(string) {
            try {
                new URL(string);
                return true;
            } catch (_) {
                return false;
            }
        },

        // Generate random ID
        generateId: function(length = 8) {
            const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
            let result = '';
            for (let i = 0; i < length; i++) {
                result += chars.charAt(Math.floor(Math.random() * chars.length));
            }
            return result;
        }
    };

    // Expose isValidUrl globally for form validation
    window.isValidUrl = window.utils.isValidUrl;

    // ===== GLOBAL EVENT LISTENERS =====
    function setupGlobalEventListeners() {
        // Escape key to close modals/overlays
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                // Close any open modals
                const modals = document.querySelectorAll('.modal, [id*="modal"], [id*="overlay"]');
                modals.forEach(modal => {
                    if (!modal.classList.contains('hidden')) {
                        modal.classList.add('hidden');
                    }
                });
                
                // Hide loading overlay
                window.hideLoading();
            }
        });

        // Click outside to close dropdowns
        document.addEventListener('click', function(e) {
            const dropdowns = document.querySelectorAll('.dropdown-menu');
            dropdowns.forEach(dropdown => {
                if (!dropdown.contains(e.target) && !dropdown.previousElementSibling?.contains(e.target)) {
                    dropdown.classList.add('hidden');
                }
            });
        });

        // Handle all form submissions with loading states
        document.addEventListener('submit', function(e) {
            const form = e.target;
            if (form.tagName === 'FORM' && !form.hasAttribute('data-no-loading')) {
                const submitButton = form.querySelector('button[type="submit"]');
                if (submitButton) {
                    submitButton.disabled = true;
                    const originalText = submitButton.textContent;
                    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
                    
                    // Re-enable after 5 seconds as failsafe
                    setTimeout(() => {
                        submitButton.disabled = false;
                        submitButton.textContent = originalText;
                    }, 5000);
                }
            }
        });

        // Enhanced link handling
        document.addEventListener('click', function(e) {
            const link = e.target.closest('a');
            if (link && link.href && !link.target && !link.download) {
                // Add loading indicator for internal links
                if (link.hostname === window.location.hostname) {
                    setTimeout(() => window.showLoading('Loading page...'), 100);
                }
            }
        });
    }

    // ===== PERFORMANCE MONITORING =====
    if (window.AliceInsight.debug) {
        // Simple performance monitoring
        const perfObserver = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                if (entry.entryType === 'navigation') {
                    console.log('Page load time:', entry.loadEventEnd - entry.loadEventStart, 'ms');
                }
            }
        });
        
        if ('observe' in perfObserver) {
            perfObserver.observe({ entryTypes: ['navigation'] });
        }
    }

})();

// ===== CHART.JS DEFAULTS =====
if (typeof Chart !== 'undefined') {
    // Set default Chart.js options for dark theme
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.backgroundColor = 'rgba(59, 130, 246, 0.1)';
    Chart.defaults.borderColor = 'rgba(59, 130, 246, 0.2)';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.9)';
    Chart.defaults.plugins.tooltip.titleColor = '#e2e8f0';
    Chart.defaults.plugins.tooltip.bodyColor = '#e2e8f0';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(59, 130, 246, 0.5)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
}

// ===== EXPORT FOR USE IN OTHER SCRIPTS =====
window.AliceInsight.utils = window.utils;
window.AliceInsight.showNotification = window.showNotification;
window.AliceInsight.showLoading = window.showLoading;
window.AliceInsight.hideLoading = window.hideLoading;
window.AliceInsight.apiRequest = window.apiRequest;