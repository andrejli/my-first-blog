/**
 * Immediate Theme Loader
 * Loads theme before page renders to prevent flash
 * This runs inline in the head to apply theme as fast as possible
 */
(function() {
    'use strict';
    
    function getCookie(name) {
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
    
    function applyThemeImmediate() {
        // Check if theme is already set server-side
        const html = document.documentElement;
        const serverTheme = html.getAttribute('data-theme');
        if (serverTheme) {
            return; // Already set by server
        }
        
        // Get theme from localStorage first (fastest)
        let theme = localStorage.getItem('user_theme');
        
        // Fallback to cookie
        if (!theme) {
            theme = getCookie('theme_preference');
        }
        
        // Apply theme if found and valid
        if (theme && theme !== 'terminal-amber') {
            html.setAttribute('data-theme', theme);
        }
    }
    
    // Apply theme immediately
    applyThemeImmediate();
    
    // Also run when DOM is ready (in case of race conditions)
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyThemeImmediate);
    }
})();