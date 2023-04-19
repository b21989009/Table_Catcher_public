// if we ever need it.




/*
// For resetting some stuff when popup is closed.
chrome.runtime.onConnect.addListener(function(port) {
    if (port.name === "popup_opened") {
        port.onDisconnect.addListener(function() {
           console.log("popup has been closed")
        });
    }
});
*/
