class ThemeSwitcher{constructor(){this.themes={'terminal-amber':'Terminal Amber','dark-blue':'Dark Blue','light':'Light Mode','cyberpunk':'Cyberpunk','matrix':'Matrix'};this.currentTheme=this.getInitialTheme();this.init();}
getInitialTheme(){const html=document.documentElement;const serverTheme=html.getAttribute('data-theme');if(serverTheme&&this.themes[serverTheme]){localStorage.setItem('user_theme',serverTheme);return serverTheme;}
const localTheme=localStorage.getItem('user_theme');if(localTheme&&this.themes[localTheme]){return localTheme;}
const cookieTheme=this.getCookie('theme_preference');if(cookieTheme&&this.themes[cookieTheme]){return cookieTheme;}
return'terminal-amber';}
getCookie(name){let cookieValue=null;if(document.cookie&&document.cookie!==''){const cookies=document.cookie.split(';');for(let i=0;i<cookies.length;i++){const cookie=cookies[i].trim();if(cookie.substring(0,name.length+1)===(name+'=')){cookieValue=decodeURIComponent(cookie.substring(name.length+1));break;}}}
return cookieValue;}
async init(){this.applyTheme(this.currentTheme);await this.syncWithServer();this.createThemeSwitcher();this.bindEvents();}
async syncWithServer(){try{const response=await fetch('/api/theme/get/');if(response.ok){const data=await response.json();const serverTheme=data.theme||'terminal-amber';if(serverTheme!==this.currentTheme){this.currentTheme=serverTheme;this.applyTheme(serverTheme);}}}catch(error){console.log('Could not sync theme with server, using local theme');}}
async saveUserTheme(theme){localStorage.setItem('user_theme',theme);try{const csrfToken=document.querySelector('[name=csrfmiddlewaretoken]')?.value;const formData=new FormData();formData.append('theme',theme);formData.append('csrfmiddlewaretoken',csrfToken);const response=await fetch('/api/theme/set/',{method:'POST',body:formData});if(response.ok){const data=await response.json();return data.success;}}catch(error){console.log('Could not save theme preference to server, using localStorage');}
return true;}
applyTheme(themeName){const html=document.documentElement;html.removeAttribute('data-theme');if(themeName!=='terminal-amber'){html.setAttribute('data-theme',themeName);}
this.currentTheme=themeName;localStorage.setItem('user_theme',themeName);this.updateThemeSelector();}
async switchTheme(themeName){if(this.themes[themeName]){this.applyTheme(themeName);await this.saveUserTheme(themeName);}}
updateThemeSelector(){const themeSelect=document.getElementById('theme-selector');if(themeSelect){themeSelect.value=this.currentTheme;}
window.dispatchEvent(new CustomEvent('themeChanged',{detail:{theme:this.currentTheme}}));}
createThemeSwitcher(){const topMenu=document.querySelector('.top-menu');if(!topMenu)return;if(document.getElementById('theme-selector'))return;const themeContainer=document.createElement('span');themeContainer.className='theme-switcher-container';themeContainer.style.marginRight='15px';const themeLabel=document.createElement('span');themeLabel.textContent='Theme: ';themeLabel.style.marginRight='5px';themeLabel.style.color='inherit';const themeSelect=document.createElement('select');themeSelect.id='theme-selector';themeSelect.className='theme-selector';Object.entries(this.themes).forEach(([value,label])=>{const option=document.createElement('option');option.value=value;option.textContent=label;if(value===this.currentTheme){option.selected=true;}
themeSelect.appendChild(option);});themeContainer.appendChild(themeLabel);themeContainer.appendChild(themeSelect);const firstButton=topMenu.querySelector('.btn');if(firstButton){topMenu.insertBefore(themeContainer,firstButton);}else{topMenu.appendChild(themeContainer);}}
bindEvents(){document.addEventListener('change',async(e)=>{if(e.target.id==='theme-selector'){await this.switchTheme(e.target.value);}});document.addEventListener('keydown',async(e)=>{if(e.ctrlKey&&e.key==='t'&&!e.target.matches('input, textarea')){e.preventDefault();await this.cycleTheme();}});}
async cycleTheme(){const themeKeys=Object.keys(this.themes);const currentIndex=themeKeys.indexOf(this.currentTheme);const nextIndex=(currentIndex+1)%themeKeys.length;await this.switchTheme(themeKeys[nextIndex]);}
async setTheme(themeName){await this.switchTheme(themeName);}
getCurrentTheme(){return this.currentTheme;}
getAvailableThemes(){return this.themes;}}
document.addEventListener('DOMContentLoaded',()=>{window.themeSwitcher=new ThemeSwitcher();});const style=document.createElement('style');style.textContent=`
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
`;document.head.appendChild(style);;