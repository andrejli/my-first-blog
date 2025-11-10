/**
 * Theme Switcher for LMS
 * Supports multiple color schemes with database + localStorage + cookie storage
 */

class ThemeSwitcher {
    constructor() {
        this.themes = {
            'terminal-amber': 'Terminal Amber',
            'dark-blue': 'Dark Blue', 
            'light': 'Light Mode',
            'cyberpunk': 'Cyberpunk',
            'matrix': 'Matrix'
        };
        
        this.currentTheme = this.getInitialTheme();
        this.init();
    }
    
    getInitialTheme() {
        // 1. First check if theme is already set server-side (from template)
        const html = document.documentElement;
        const serverTheme = html.getAttribute('data-theme');
        if (serverTheme && this.themes[serverTheme]) {
            return serverTheme;
        }
        
        // 2. Check localStorage for immediate response
        const localTheme = localStorage.getItem('user_theme');
        if (localTheme && this.themes[localTheme]) {
            return localTheme;
        }
        
        // 3. Check cookie
        const cookieTheme = this.getCookie('theme_preference');
        if (cookieTheme && this.themes[cookieTheme]) {
            return cookieTheme;
        }
        
        // 4. Default fallback
        return 'terminal-amber';
    }
    
    getCookie(name) {
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
    
    async init() {
        // Apply theme immediately from server-side or localStorage
        this.applyTheme(this.currentTheme);
        
        // Then sync with server (async)
        await this.syncWithServer();
        
        this.createThemeSwitcher();
        this.bindEvents();
    }
    
    async syncWithServer() {
        try {
            const response = await fetch('/api/theme/get/');
            if (response.ok) {
                const data = await response.json();
                const serverTheme = data.theme || 'terminal-amber';
                
                // If server theme differs from current, use server theme
                if (serverTheme !== this.currentTheme) {
                    this.applyTheme(serverTheme);
                    // Update localStorage
                    localStorage.setItem('user_theme', serverTheme);
                }
            }
        } catch (error) {
            console.log('Could not sync theme with server, using local theme');
        }
    }
    
    async saveUserTheme(theme) {
        // Save to localStorage immediately for instant response
        localStorage.setItem('user_theme', theme);
        
        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            const formData = new FormData();
            formData.append('theme', theme);
            formData.append('csrfmiddlewaretoken', csrfToken);
            
            const response = await fetch('/api/theme/set/', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.success;
            }
        } catch (error) {
            console.log('Could not save theme preference to server, using localStorage');
        }
        return true; // Return true if localStorage worked
    }
    
    applyTheme(themeName) {
        const html = document.documentElement;
        
        // Remove existing theme attribute
        html.removeAttribute('data-theme');
        
        // Apply new theme (terminal-amber is default, no data-theme needed)
        if (themeName !== 'terminal-amber') {
            html.setAttribute('data-theme', themeName);
        }
        
        this.currentTheme = themeName;
        
        // Save to localStorage for persistence
        localStorage.setItem('user_theme', themeName);
        
        // Update theme selector if it exists
        this.updateThemeSelector();
    }
    
    async switchTheme(themeName) {
        if (this.themes[themeName]) {
            this.applyTheme(themeName);
            await this.saveUserTheme(themeName);
        }
    }
    
    updateThemeSelector() {
        const themeSelect = document.getElementById('theme-selector');
        if (themeSelect) {
            themeSelect.value = this.currentTheme;
        }
        
        // Dispatch theme change event
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: this.currentTheme }
        }));
    }
    
    createThemeSwitcher() {
        // Check if we're in a page with top-menu
        const topMenu = document.querySelector('.top-menu');
        if (!topMenu) return;
        
        // Don't create if already exists
        if (document.getElementById('theme-selector')) return;
        
        // Create theme selector
        const themeContainer = document.createElement('span');
        themeContainer.className = 'theme-switcher-container';
        themeContainer.style.marginRight = '15px';
        
        const themeLabel = document.createElement('span');
        themeLabel.textContent = 'Theme: ';
        themeLabel.style.marginRight = '5px';
        themeLabel.style.color = 'inherit';
        
        const themeSelect = document.createElement('select');
        themeSelect.id = 'theme-selector';
        themeSelect.className = 'theme-selector';
        
        // Add options
        Object.entries(this.themes).forEach(([value, label]) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = label;
            if (value === this.currentTheme) {
                option.selected = true;
            }
            themeSelect.appendChild(option);
        });
        
        themeContainer.appendChild(themeLabel);
        themeContainer.appendChild(themeSelect);
        
        // Insert before the first button in top-menu
        const firstButton = topMenu.querySelector('.btn');
        if (firstButton) {
            topMenu.insertBefore(themeContainer, firstButton);
        } else {
            topMenu.appendChild(themeContainer);
        }
    }
    
    bindEvents() {
        // Theme selector change event
        document.addEventListener('change', async (e) => {
            if (e.target.id === 'theme-selector') {
                await this.switchTheme(e.target.value);
            }
        });
        
        // Keyboard shortcut (Ctrl+T)
        document.addEventListener('keydown', async (e) => {
            if (e.ctrlKey && e.key === 't' && !e.target.matches('input, textarea')) {
                e.preventDefault();
                await this.cycleTheme();
            }
        });
    }
    
    async cycleTheme() {
        const themeKeys = Object.keys(this.themes);
        const currentIndex = themeKeys.indexOf(this.currentTheme);
        const nextIndex = (currentIndex + 1) % themeKeys.length;
        await this.switchTheme(themeKeys[nextIndex]);
    }
    
    // Public methods
    async setTheme(themeName) {
        await this.switchTheme(themeName);
    }
    
    getCurrentTheme() {
        return this.currentTheme;
    }
    
    getAvailableThemes() {
        return this.themes;
    }
}

// Initialize theme switcher when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.themeSwitcher = new ThemeSwitcher();
});

// Add some CSS for theme selector hover effects
const style = document.createElement('style');
style.textContent = `
    .theme-switcher-container select:hover {
        border-color: var(--secondary-color) !important;
        box-shadow: 0 0 5px var(--shadow-primary) !important;
    }
    
    .theme-switcher-container select:focus {
        outline: none;
        border-color: var(--accent-color) !important;
        box-shadow: 0 0 8px var(--shadow-secondary) !important;
    }
    
    /* Smooth transitions for theme changes */
    * {
        transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease !important;
    }
    
    /* Override for elements that shouldn't transition */
    .no-transition, .no-transition * {
        transition: none !important;
    }
`;
document.head.appendChild(style);