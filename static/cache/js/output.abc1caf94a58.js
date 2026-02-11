(function(){'use strict';function getCookie(name){let cookieValue=null;if(document.cookie&&document.cookie!==''){const cookies=document.cookie.split(';');for(let i=0;i<cookies.length;i++){const cookie=cookies[i].trim();if(cookie.substring(0,name.length+1)===(name+'=')){cookieValue=decodeURIComponent(cookie.substring(name.length+1));break;}}}
return cookieValue;}
function applyThemeImmediate(){const html=document.documentElement;const serverTheme=html.getAttribute('data-theme');if(serverTheme){localStorage.setItem('user_theme',serverTheme);return;}
let theme=localStorage.getItem('user_theme');if(!theme){theme=getCookie('theme_preference');}
if(theme&&theme!=='terminal-amber'){html.setAttribute('data-theme',theme);}}
applyThemeImmediate();if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',applyThemeImmediate);}})();;