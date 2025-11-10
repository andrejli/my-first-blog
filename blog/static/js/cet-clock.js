// CET Time Clock (Vienna/Bratislava timezone)
(function() {
    function actualizeTime(i) {
        if (i < 10) {i = "0" + i;}
        return i;
    }
    
    function ActualTime() {
        // Use toLocaleString with Vienna timezone to get accurate CET/CEST time
        var now = new Date();
        
        // Format for Vienna timezone (which is CET/CEST)
        var cetString = now.toLocaleString('en-US', {
            timeZone: 'Europe/Vienna',
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        // Parse the time string
        var parts = cetString.split(/[:\s]/);
        var hours = parts[0];
        var minutes = parts[1];
        var seconds = parts[2];
        var milliseconds = String(now.getMilliseconds()).padStart(3, '0');
        
        var watchElement = document.getElementById('watch');
        if (watchElement) {
            watchElement.innerHTML = hours + ":" + minutes + ":" + seconds + ":" + milliseconds;
        }
        
        setTimeout(ActualTime, 1);
    }
    
    // Start immediately
    ActualTime();
})();
