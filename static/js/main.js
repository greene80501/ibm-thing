// Alice Insight Suite - Professional Corporate Version
console.log("Alice Insight Suite initialized - Professional Mode");

// Global utilities for corporate environment
window.AliceInsight = {
    // Configuration
    config: {
        apiTimeout: 30000,
        retryAttempts: 3,
        debounceDelay: 300
    },

    // Enhanced form handling for corporate security
    forms: {
        init() {
            // Add CSRF protection if needed
            this.addFormValidation();
            this.addLoadingStates();
        },

        addFormValidation() {
            document.querySelectorAll('form').forEach(form => {
                form.addEventListener('submit', function(e) {
                    const inputs = this.querySelectorAll('input[required]');
                    let isValid = true;

                    inputs.forEach(input => {
                        if (!input.value.trim()) {
                            input.classList.add('border-red-500');
                            isValid = false;
                        } else {
                            input.classList.remove('border-red-500');
                        }
                    });

                    if (!isValid) {
                        e.preventDefault();
                        AliceInsight.ui.showNotification('Please fill in all required fields', 'error');
                    }
                });
            });
        },

        addLoadingStates() {
            document.addEventListener('submit', function(e) {
                if (e.target.classList.contains('api-form')) {
                    AliceInsight.ui.showLoading();
                    
                    // Timeout protection
                    setTimeout(() => {
                        AliceInsight.ui.hideLoading();
                        AliceInsight.ui.showNotification('Request timeout. Please try again.', 'warning');
                    }, AliceInsight.config.apiTimeout);
                }
            });
        },

        validateYouTubeURL(url) {
            const patterns = [
                /^https?:\/\/(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)/,
                /^https?:\/\/(www\.)?youtube\.com\/watch\?.*v=.*/
            ];
            return patterns.some(pattern => pattern.test(url));
        }
    },

    // Professional UI components
    ui: {
        showLoading(message = 'Processing request...') {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                overlay.querySelector('p').textContent = message;
                overlay.classList.remove('hidden');
            }
        },

        hideLoading() {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                overlay.classList.add('hidden');
            }
        },

        showNotification(message, type = 'info', duration = 5000) {
            const container = this.getNotificationContainer();
            
            const notification = document.createElement('div');
            notification.className = `notification p-4 rounded-lg border mb-3 transition-all duration-300`;
            
            const typeStyles = {
                success: 'bg-green-900/50 border-green-500 text-green-200',
                error: 'bg-red-900/50 border-red-500 text-red-200',
                warning: 'bg-yellow-900/50 border-yellow-500 text-yellow-200',
                info: 'bg-blue-900/50 border-blue-500 text-blue-200'
            };
            
            const typeIcons = {
                success: 'fa-check-circle',
                error: 'fa-exclamation-triangle',
                warning: 'fa-exclamation-circle',
                info: 'fa-info-circle'
            };
            
            notification.className += ' ' + typeStyles[type];
            notification.innerHTML = `
                <div class="flex items-center justify-between">
                    <div class="flex items-center">
                        <i class="fas ${typeIcons[type]} mr-3"></i>
                        <span class="text-sm font-medium">${message}</span>
                    </div>
                    <button class="ml-4 text-current opacity-70 hover:opacity-100" onclick="this.parentElement.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            
            container.appendChild(notification);
            
            // Auto-remove
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.style.transform = 'translateX(100%)';
                    notification.style.opacity = '0';
                    setTimeout(() => notification.remove(), 300);
                }
            }, duration);
        },

        getNotificationContainer() {
            let container = document.getElementById('notification-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'notification-container';
                container.className = 'fixed top-4 right-4 z-50 max-w-sm';
                document.body.appendChild(container);
            }
            return container;
        },

        setButtonLoading(button, loading = true, text = 'Processing...') {
            if (loading) {
                button.dataset.originalText = button.textContent;
                button.innerHTML = `
                    <i class="fas fa-spinner fa-spin mr-2"></i>
                    ${text}
                `;
                button.disabled = true;
            } else {
                button.textContent = button.dataset.originalText || 'Submit';
                button.disabled = false;
                delete button.dataset.originalText;
            }
        }
    },

    // Analytics tracking for corporate reporting
    analytics: {
        events: [],
        
        track(action, category = 'general', data = {}) {
            const event = {
                timestamp: new Date().toISOString(),
                action,
                category,
                data,
                sessionId: this.getSessionId()
            };
            
            this.events.push(event);
            console.log('Analytics:', event);
            
            // Keep only last 1000 events
            if (this.events.length > 1000) {
                this.events.shift();
            }
            
            // Store for session persistence
            try {
                sessionStorage.setItem('alice-analytics', JSON.stringify(this.events.slice(-100)));
            } catch (e) {
                console.warn('Could not store analytics data');
            }
        },

        getSessionId() {
            let sessionId = sessionStorage.getItem('alice-session-id');
            if (!sessionId) {
                sessionId = 'session-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
                sessionStorage.setItem('alice-session-id', sessionId);
            }
            return sessionId;
        },

        getReport() {
            return {
                totalEvents: this.events.length,
                categories: this.events.reduce((acc, event) => {
                    acc[event.category] = (acc[event.category] || 0) + 1;
                    return acc;
                }, {}),
                recentEvents: this.events.slice(-10)
            };
        }
    },

    // Utility functions for corporate environment
    utils: {
        formatNumber(num) {
            if (num >= 1000000) {
                return (num / 1000000).toFixed(1) + 'M';
            } else if (num >= 1000) {
                return (num / 1000).toFixed(1) + 'K';
            }
            return num.toString();
        },

        formatDate(date) {
            return new Intl.DateTimeFormat('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }).format(new Date(date));
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

        async copyToClipboard(text) {
            try {
                await navigator.clipboard.writeText(text);
                AliceInsight.ui.showNotification('Copied to clipboard', 'success', 2000);
                return true;
            } catch (err) {
                AliceInsight.ui.showNotification('Failed to copy to clipboard', 'error');
                return false;
            }
        },

        downloadFile(data, filename, type = 'text/plain') {
            const blob = new Blob([data], { type });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }
    },

    // Security features for corporate environment
    security: {
        init() {
            this.addCSRFProtection();
            this.validateInputs();
        },

        addCSRFProtection() {
            // Add CSRF tokens to forms if needed
            document.querySelectorAll('form').forEach(form => {
                if (!form.querySelector('input[name="csrf_token"]')) {
                    // CSRF token would be added here in production
                }
            });
        },

        validateInputs() {
            document.querySelectorAll('input, textarea').forEach(input => {
                input.addEventListener('input', function() {
                    // Basic XSS prevention
                    if (this.value.includes('<script') || this.value.includes('javascript:')) {
                        this.value = this.value.replace(/<script[^>]*>.*?<\/script>/gi, '');
                        AliceInsight.ui.showNotification('Invalid characters detected and removed', 'warning');
                    }
                });
            });
        }
    }
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all modules
    AliceInsight.forms.init();
    AliceInsight.security.init();
    
    // Set active navigation
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
        
        // Track navigation clicks
        link.addEventListener('click', () => {
            AliceInsight.analytics.track('navigation', 'sidebar', {
                page: link.getAttribute('href'),
                label: link.textContent.trim()
            });
        });
    });
    
    // Enhanced search functionality
    const searchInput = document.querySelector('input[placeholder="Search..."]');
    if (searchInput) {
        const debouncedSearch = AliceInsight.utils.debounce((query) => {
            if (query.length > 2) {
                AliceInsight.analytics.track('search', 'query', { query });
                // Implement actual search functionality here
                console.log('Searching for:', query);
            }
        }, AliceInsight.config.debounceDelay);
        
        searchInput.addEventListener('input', (e) => {
            debouncedSearch(e.target.value);
        });
    }
    
    // Keyboard shortcuts for productivity
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
                AliceInsight.analytics.track('keyboard_shortcut', 'search_focus');
            }
        }
        
        // Escape to close overlays
        if (e.key === 'Escape') {
            const overlay = document.getElementById('loading-overlay');
            if (overlay && !overlay.classList.contains('hidden')) {
                AliceInsight.ui.hideLoading();
            }
        }
    });
    
    // Form validation enhancements
    document.querySelectorAll('input[required]').forEach(input => {
        input.addEventListener('blur', function() {
            if (!this.value.trim()) {
                this.classList.add('border-red-500');
            } else {
                this.classList.remove('border-red-500');
            }
        });
    });
    
    // Auto-save form data in session storage
    document.querySelectorAll('form input, form textarea, form select').forEach(input => {
        const key = `alice-form-${input.name || input.id}`;
        
        // Restore saved data
        const savedValue = sessionStorage.getItem(key);
        if (savedValue && input.type !== 'password') {
            input.value = savedValue;
        }
        
        // Save data on input
        input.addEventListener('input', AliceInsight.utils.debounce(() => {
            if (input.type !== 'password') {
                sessionStorage.setItem(key, input.value);
            }
        }, 1000));
    });
    
    // Clear form data on successful submission
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            // Clear saved form data after successful submission
            setTimeout(() => {
                const inputs = this.querySelectorAll('input, textarea, select');
                inputs.forEach(input => {
                    const key = `alice-form-${input.name || input.id}`;
                    sessionStorage.removeItem(key);
                });
            }, 1000);
        });
    });
    
    // Add hover effects to interactive elements
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Enhanced button interactions
    document.querySelectorAll('button').forEach(button => {
        button.addEventListener('click', function() {
            if (!this.disabled) {
                AliceInsight.analytics.track('button_click', 'interaction', {
                    text: this.textContent.trim(),
                    page: window.location.pathname
                });
            }
        });
    });
    
    // Track form submissions
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            AliceInsight.analytics.track('form_submit', 'interaction', {
                formId: this.id || 'unknown',
                page: window.location.pathname
            });
        });
    });
});

// Error handling for corporate environment
window.addEventListener('error', function(e) {
    console.error('Application error:', e.error);
    AliceInsight.analytics.track('error', 'javascript', {
        message: e.error?.message || 'Unknown error',
        filename: e.filename,
        line: e.lineno
    });
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    AliceInsight.ui.hideLoading();
    AliceInsight.ui.showNotification('An unexpected error occurred. Please try again.', 'error');
    AliceInsight.analytics.track('error', 'promise_rejection', {
        reason: e.reason?.message || 'Unknown rejection'
    });
});

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', () => {
        setTimeout(() => {
            const perfData = performance.getEntriesByType('navigation')[0];
            if (perfData) {
                const loadTime = Math.round(perfData.loadEventEnd - perfData.loadEventStart);
                AliceInsight.analytics.track('performance', 'page_load', {
                    loadTime,
                    url: window.location.pathname
                });
                
                if (loadTime > 3000) {
                    console.warn(`Slow page load detected: ${loadTime}ms`);
                }
            }
        }, 0);
    });
}

// Network status monitoring
window.addEventListener('online', () => {
    AliceInsight.ui.showNotification('Connection restored', 'success', 2000);
    AliceInsight.analytics.track('network', 'online');
});

window.addEventListener('offline', () => {
    AliceInsight.ui.showNotification('Connection lost. Some features may be limited.', 'warning', 8000);
    AliceInsight.analytics.track('network', 'offline');
});

// Page visibility tracking
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        AliceInsight.analytics.track('page', 'hidden');
    } else {
        AliceInsight.analytics.track('page', 'visible');
    }
});

// Session tracking
window.addEventListener('beforeunload', function() {
    AliceInsight.analytics.track('session', 'end', {
        duration: Date.now() - (sessionStorage.getItem('session-start') || Date.now())
    });
});

// Initialize session start time
if (!sessionStorage.getItem('session-start')) {
    sessionStorage.setItem('session-start', Date.now().toString());
    AliceInsight.analytics.track('session', 'start');
}

// API request interceptor for corporate logging
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const startTime = Date.now();
    const url = args[0];
    
    return originalFetch.apply(this, args)
        .then(response => {
            const duration = Date.now() - startTime;
            AliceInsight.analytics.track('api_request', 'success', {
                url: typeof url === 'string' ? url : url.url,
                duration,
                status: response.status
            });
            return response;
        })
        .catch(error => {
            const duration = Date.now() - startTime;
            AliceInsight.analytics.track('api_request', 'error', {
                url: typeof url === 'string' ? url : url.url,
                duration,
                error: error.message
            });
            throw error;
        });
};

// Backward compatibility functions
window.showLoading = function(message) {
    AliceInsight.ui.showLoading(message);
};

window.hideLoading = function() {
    AliceInsight.ui.hideLoading();
};

window.showNotification = function(message, type, duration) {
    AliceInsight.ui.showNotification(message, type, duration);
};

window.validateYouTubeURL = function(url) {
    return AliceInsight.forms.validateYouTubeURL(url);
};

// Development helpers (only in development environment)
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log('%c🏢 Alice Insight Suite - Corporate Edition', 'color: #3b82f6; font-size: 16px; font-weight: bold;');
    console.log('%cKeyboard Shortcuts:', 'color: #64748b; font-weight: bold;');
    console.log('• Ctrl/Cmd + K: Focus search');
    console.log('• Escape: Close overlays');
    
    // Add development helpers to global scope
    window.AliceInsight.dev = {
        getAnalytics: () => AliceInsight.analytics.getReport(),
        clearAnalytics: () => {
            AliceInsight.analytics.events = [];
            sessionStorage.removeItem('alice-analytics');
            console.log('Analytics data cleared');
        },
        testNotification: (type = 'info') => {
            AliceInsight.ui.showNotification(`Test ${type} notification`, type);
        },
        simulateError: () => {
            throw new Error('Simulated error for testing');
        },
        getSessionData: () => {
            const data = {};
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                if (key.startsWith('alice-')) {
                    data[key] = sessionStorage.getItem(key);
                }
            }
            return data;
        }
    };
    
    console.log('%cDevelopment helpers available at:', 'color: #10b981;');
    console.log('• AliceInsight.dev.getAnalytics()');
    console.log('• AliceInsight.dev.clearAnalytics()');
    console.log('• AliceInsight.dev.testNotification(type)');
    console.log('• AliceInsight.dev.getSessionData()');
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AliceInsight;
}