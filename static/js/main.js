# 4. static/js/main.js - Full professional JavaScript
main_js = '''/**
 * ============================================
 * حاسبة وزن الحديد الذكية - Smart Iron Calculator
 * Main JavaScript Module
 * Professional Factory-Grade Code
 * ============================================
 */

(function() {
    'use strict';

    // ===== Global Configuration =====
    const CONFIG = {
        debounceDelay: 300,
        autoHideDelay: 5000,
        animationDuration: 300,
        toastPosition: 'top-end',
        apiBase: '',
        version: '1.0.0'
    };

    // ===== DOM Ready Handler =====
    document.addEventListener('DOMContentLoaded', function() {
        initAutoHideAlerts();
        initPreventDoubleSubmit();
        initInputValidation();
        initNumberInputs();
        initTooltips();
        initSmoothScroll();
        initKeyboardShortcuts();
        initTouchFeedback();
        initPageVisibility();
        console.log(`⚖️ Smart Iron Calculator v${CONFIG.version} loaded successfully`);
    });

    // ===== Auto-hide Flash Messages =====
    function initAutoHideAlerts() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach((alert, index) => {
            // Stagger the auto-hide timing
            const delay = CONFIG.autoHideDelay + (index * 500);
            setTimeout(() => {
                if (alert && alert.parentNode) {
                    const bsAlert = bootstrap.Alert.getInstance(alert);
                    if (bsAlert) {
                        bsAlert.close();
                    } else {
                        fadeOut(alert);
                    }
                }
            }, delay);
        });
    }

    // ===== Prevent Double Form Submission =====
    function initPreventDoubleSubmit() {
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function(e) {
                const submitBtn = this.querySelector('button[type="submit"]');
                if (!submitBtn) return;

                // Check if already submitting
                if (submitBtn.dataset.submitting === 'true') {
                    e.preventDefault();
                    return false;
                }

                submitBtn.dataset.submitting = 'true';
                const originalContent = submitBtn.innerHTML;
                const originalWidth = submitBtn.offsetWidth;

                // Set fixed width to prevent layout shift
                submitBtn.style.width = originalWidth + 'px';
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> جاري...';
                submitBtn.disabled = true;

                // Re-enable after timeout (safety net)
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalContent;
                    submitBtn.style.width = '';
                    submitBtn.dataset.submitting = 'false';
                }, 8000);
            });
        });
    }

    // ===== Input Validation =====
    function initInputValidation() {
        // Positive number validation
        document.querySelectorAll('input[type="number"]').forEach(input => {
            input.addEventListener('input', function() {
                if (this.hasAttribute('min') && parseFloat(this.value) < parseFloat(this.min)) {
                    this.value = this.min;
                }
                if (this.hasAttribute('max') && parseFloat(this.value) > parseFloat(this.max)) {
                    this.value = this.max;
                }
            });

            // Prevent negative on paste
            input.addEventListener('paste', function(e) {
                const pasted = (e.clipboardData || window.clipboardData).getData('text');
                if (parseFloat(pasted) < 0 && this.min >= 0) {
                    e.preventDefault();
                    showToast('لا يمكن إدخال قيم سالبة', 'warning');
                }
            });
        });

        // Required field visual feedback
        document.querySelectorAll('input[required], select[required], textarea[required]').forEach(field => {
            field.addEventListener('blur', function() {
                if (!this.value.trim()) {
                    this.classList.add('is-invalid');
                } else {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });

            field.addEventListener('input', function() {
                if (this.value.trim()) {
                    this.classList.remove('is-invalid');
                }
            });
        });
    }

    // ===== Number Input Enhancements =====
    function initNumberInputs() {
        document.querySelectorAll('input[type="number"]').forEach(input => {
            // Allow arrow keys to increment/decrement
            input.addEventListener('keydown', function(e) {
                if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    const step = parseFloat(this.step) || 1;
                    const current = parseFloat(this.value) || 0;
                    this.value = (current + step).toFixed(getDecimalPlaces(step));
                    this.dispatchEvent(new Event('input'));
                } else if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    const step = parseFloat(this.step) || 1;
                    const current = parseFloat(this.value) || 0;
                    const min = parseFloat(this.min);
                    const newVal = current - step;
                    if (isNaN(min) || newVal >= min) {
                        this.value = newVal.toFixed(getDecimalPlaces(step));
                        this.dispatchEvent(new Event('input'));
                    }
                }
            });
        });
    }

    // ===== Bootstrap Tooltips =====
    function initTooltips() {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        if (tooltipTriggerList.length && typeof bootstrap !== 'undefined') {
            [...tooltipTriggerList].map(el => new bootstrap.Tooltip(el));
        }
    }

    // ===== Smooth Scroll =====
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;
                const target = document.querySelector(targetId);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }

    // ===== Keyboard Shortcuts =====
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Escape to close modals and search results
            if (e.key === 'Escape') {
                const openModal = document.querySelector('.modal.show');
                if (openModal) {
                    const modalInstance = bootstrap.Modal.getInstance(openModal);
                    if (modalInstance) modalInstance.hide();
                }

                const searchResults = document.getElementById('searchResults');
                if (searchResults) {
                    searchResults.classList.add('d-none');
                }
            }

            // Ctrl+K or / to focus search
            if ((e.ctrlKey && e.key === 'k') || (e.key === '/' && !isInputFocused())) {
                e.preventDefault();
                const searchInput = document.getElementById('itemSearch');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }

            // Ctrl+Enter to submit forms
            if (e.ctrlKey && e.key === 'Enter') {
                const activeForm = document.querySelector('form');
                if (activeForm && isInputFocused()) {
                    activeForm.dispatchEvent(new Event('submit'));
                }
            }
        });
    }

    // ===== Touch Feedback for Mobile =====
    function initTouchFeedback() {
        if ('ontouchstart' in window) {
            document.querySelectorAll('.btn, .list-group-item, .nav-link').forEach(el => {
                el.addEventListener('touchstart', function() {
                    this.style.opacity = '0.7';
                });
                el.addEventListener('touchend', function() {
                    this.style.opacity = '';
                });
            });
        }
    }

    // ===== Page Visibility API =====
    function initPageVisibility() {
        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'visible') {
                // Refresh data when page becomes visible (optional)
                // console.log('Page became visible');
            }
        });
    }

    // ===== Utility Functions =====

    /**
     * Debounce function execution
     * @param {Function} func - Function to debounce
     * @param {number} wait - Delay in milliseconds
     * @returns {Function} Debounced function
     */
    window.debounce = function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    };

    /**
     * Throttle function execution
     * @param {Function} func - Function to throttle
     * @param {number} limit - Time limit in milliseconds
     * @returns {Function} Throttled function
     */
    window.throttle = function(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    };

    /**
     * Fade out element
     * @param {HTMLElement} element - Element to fade out
     * @param {number} duration - Animation duration
     */
    window.fadeOut = function(element, duration = 300) {
        if (!element) return;
        element.style.transition = `opacity ${duration}ms ease`;
        element.style.opacity = '0';
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }, duration);
    };

    /**
     * Fade in element
     * @param {HTMLElement} element - Element to fade in
     * @param {number} duration - Animation duration
     */
    window.fadeIn = function(element, duration = 300) {
        if (!element) return;
        element.style.opacity = '0';
        element.style.display = '';
        element.style.transition = `opacity ${duration}ms ease`;
        requestAnimationFrame(() => {
            element.style.opacity = '1';
        });
    };

    /**
     * Show toast notification
     * @param {string} message - Toast message
     * @param {string} type - Toast type: success, error, warning, info
     * @param {number} duration - Display duration in ms
     */
    window.showToast = function(message, type = 'info', duration = 3000) {
        const toastContainer = document.getElementById('toastContainer') || createToastContainer();

        const toastEl = document.createElement('div');
        toastEl.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show shadow-sm`;
        toastEl.style.minWidth = '250px';
        toastEl.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        toastContainer.appendChild(toastEl);

        setTimeout(() => {
            fadeOut(toastEl, 300);
        }, duration);
    };

    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = 'position:fixed;top:20px;left:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;';
        document.body.appendChild(container);
        return container;
    }

    /**
     * Format number with Arabic numerals
     * @param {number} num - Number to format
     * @param {number} decimals - Decimal places
     * @returns {string} Formatted number
     */
    window.formatNumber = function(num, decimals = 2) {
        if (num === null || num === undefined || isNaN(num)) return '-';
        return parseFloat(num).toLocaleString('ar-SA', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    };

    /**
     * Format weight with unit
     * @param {number} weight - Weight value
     * @returns {string} Formatted weight string
     */
    window.formatWeight = function(weight) {
        return `${formatNumber(weight, 2)} <small class="text-muted">كجم</small>`;
    };

    /**
     * Get decimal places from a number
     * @param {number} num - Number to analyze
     * @returns {number} Number of decimal places
     */
    function getDecimalPlaces(num) {
        const match = ('' + num).match(/(?:\\.(\\d+))?(?:[eE]([+-]?\\d+))?$/);
        if (!match) return 0;
        return Math.max(0, (match[1] ? match[1].length : 0) - (match[2] ? +match[2] : 0));
    }

    /**
     * Check if an input element is currently focused
     * @returns {boolean}
     */
    function isInputFocused() {
        const active = document.activeElement;
        return active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'SELECT' || active.isContentEditable);
    }

    /**
     * Copy text to clipboard
     * @param {string} text - Text to copy
     * @returns {Promise<boolean>}
     */
    window.copyToClipboard = async function(text) {
        try {
            await navigator.clipboard.writeText(text);
            showToast('تم النسخ إلى الحافظة!', 'success');
            return true;
        } catch (err) {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                showToast('تم النسخ إلى الحافظة!', 'success');
                return true;
            } catch (e) {
                showToast('فشل النسخ', 'error');
                return false;
            } finally {
                document.body.removeChild(textarea);
            }
        }
    };

    /**
     * Share content using Web Share API or fallback to clipboard
     * @param {string} title - Share title
     * @param {string} text - Share text
     */
    window.shareContent = async function(title, text) {
        if (navigator.share) {
            try {
                await navigator.share({ title, text });
            } catch (err) {
                if (err.name !== 'AbortError') {
                    copyToClipboard(text);
                }
            }
        } else {
            copyToClipboard(text);
        }
    };

    /**
     * Confirm dialog with custom message
     * @param {string} message - Confirmation message
     * @returns {boolean}
     */
    window.confirmAction = function(message) {
        return confirm(message);
    };

    /**
     * Animate number counting
     * @param {HTMLElement} element - Element to animate
     * @param {number} target - Target number
     * @param {number} duration - Animation duration in ms
     * @param {number} decimals - Decimal places
     */
    window.animateNumber = function(element, target, duration = 800, decimals = 2) {
        if (!element) return;
        const start = parseFloat(element.textContent.replace(/[^0-9.-]/g, '')) || 0;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = 1 - Math.pow(1 - progress, 3); // ease-out cubic
            const current = start + (target - start) * easeProgress;
            element.textContent = formatNumber(current, decimals);

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    };

    /**
     * Shake an element to indicate error
     * @param {HTMLElement} element - Element to shake
     */
    window.shakeElement = function(element) {
        if (!element) return;
        element.classList.add('animate-shake');
        setTimeout(() => element.classList.remove('animate-shake'), 400);
    };

    /**
     * Highlight element briefly
     * @param {HTMLElement} element - Element to highlight
     * @param {string} color - Highlight color class
     */
    window.highlightElement = function(element, color = 'bg-warning') {
        if (!element) return;
        element.classList.add(color);
        setTimeout(() => element.classList.remove(color), 1000);
    };

    /**
     * Scroll to element smoothly
     * @param {string|HTMLElement} target - Target element or selector
     * @param {number} offset - Offset from top
     */
    window.scrollToElement = function(target, offset = 80) {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (!element) return;
        const top = element.getBoundingClientRect().top + window.pageYOffset - offset;
        window.scrollTo({ top, behavior: 'smooth' });
    };

    /**
     * API Helper - GET request
     * @param {string} url - API endpoint
     * @returns {Promise<any>}
     */
    window.apiGet = async function(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API GET Error:', error);
            showToast('خطأ في الاتصال بالخادم', 'error');
            throw error;
        }
    };

    /**
     * API Helper - POST request
     * @param {string} url - API endpoint
     * @param {Object} data - Request body
     * @returns {Promise<any>}
     */
    window.apiPost = async function(url, data = {}) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API POST Error:', error);
            showToast('خطأ في الاتصال بالخادم', 'error');
            throw error;
        }
    };

    /**
     * Local Storage Helper
     */
    window.Storage = {
        set: function(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (e) {
                console.error('Storage error:', e);
                return false;
            }
        },
        get: function(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                return defaultValue;
            }
        },
        remove: function(key) {
            localStorage.removeItem(key);
        },
        clear: function() {
            localStorage.clear();
        }
    };

    /**
     * Session Storage Helper
     */
    window.Session = {
        set: function(key, value) {
            try {
                sessionStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (e) {
                return false;
            }
        },
        get: function(key, defaultValue = null) {
            try {
                const item = sessionStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                return defaultValue;
            }
        }
    };

    // ===== Service Worker Registration (for PWA support) =====
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            // Uncomment when service-worker.js is ready
            // navigator.serviceWorker.register('/static/js/service-worker.js')
            //     .then(reg => console.log('SW registered:', reg.scope))
            //     .catch(err => console.log('SW registration failed:', err));
        });
    }

    // ===== Expose utilities globally =====
    window.SmartIron = {
        config: CONFIG,
        debounce: window.debounce,
        throttle: window.throttle,
        fadeOut: window.fadeOut,
        fadeIn: window.fadeIn,
        showToast: window.showToast,
        formatNumber: window.formatNumber,
        formatWeight: window.formatWeight,
        copyToClipboard: window.copyToClipboard,
        shareContent: window.shareContent,
        animateNumber: window.animateNumber,
        shakeElement: window.shakeElement,
        scrollToElement: window.scrollToElement,
        apiGet: window.apiGet,
        apiPost: window.apiPost,
        storage: window.Storage,
        session: window.Session
    };

})();
