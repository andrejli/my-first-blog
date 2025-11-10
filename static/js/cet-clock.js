// CET Time Clock
(function() {
    function actualizeTime(i) {
        if (i < 10) {i = "0" + i;}
        return i;
    }
    
    function ActualTime() {
        var now = new Date();
        
        // Calculate UTC time
        var utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
        
        // Check if we're in DST for Central Europe
        var jan = new Date(now.getFullYear(), 0, 1);
        var jul = new Date(now.getFullYear(), 6, 1);
        var isDST = Math.max(jan.getTimezoneOffset(), jul.getTimezoneOffset()) !== now.getTimezoneOffset();
        
        // CET offset: +1 hour (60 min) or +2 hours (120 min) during DST
        var cetOffset = isDST ? 120 : 60;
        var cetTime = new Date(utcTime + (cetOffset * 60000));
        
        var hours = actualizeTime(cetTime.getUTCHours());
        var minutes = actualizeTime(cetTime.getUTCMinutes());
        var seconds = actualizeTime(cetTime.getUTCSeconds());
        var milliseconds = String(cetTime.getUTCMilliseconds()).padStart(3, '0');
        
        var watchElement = document.getElementById('watch');
        if (watchElement) {
            watchElement.innerHTML = hours + ":" + minutes + ":" + seconds + ":" + milliseconds;
        }
        
        setTimeout(ActualTime, 1);
    }
    
    // Start immediately
    ActualTime();
})();
