/**
 * Theme Switcher for LMS
 * Supports multiple color schemes with database storage
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
        
        this.currentTheme = 'terminal-amber'; // default fallback
        this.init();
    }
    
    async init() {
        await this.loadUserTheme();
        this.applyTheme(this.currentTheme);
        this.createThemeSwitcher();
        this.bindEvents();
    }
    
    async loadUserTheme() {
        try {
            const response = await fetch('/api/theme/get/');
            if (response.ok) {
                const data = await response.json();
                this.currentTheme = data.theme || 'terminal-amber';
            }
        } catch (error) {
            console.log('Could not load user theme, using default');
            this.currentTheme = 'terminal-amber';
        }
    }
    
    async saveUserTheme(theme) {
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
            console.log('Could not save theme preference');
        }
        return false;
    }
    
    applyTheme(themeName) {
        const html = document.documentElement;
        
        // Remove all theme classes
        Object.keys(this.themes).forEach(theme => {
            html.removeAttribute('data-theme');
        });
        
        // Apply new theme (terminal-amber is default, no data-theme needed)
        if (themeName !== 'terminal-amber') {
            html.setAttribute('data-theme', themeName);
        }
        
        this.currentTheme = themeName;
        
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