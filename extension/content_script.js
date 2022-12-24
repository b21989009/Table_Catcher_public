
console.log("this content script starts executing on any tab when you first open the tab. you can manipulate stuff on the page.");

//page_html = document.getElementsByTagName('html')[0].innerHTML; // This reads tab's html.
/*** this console is NOT extension's console but regular website tab's console. */
//console.log(page_html);


// cannot use the pop-up buttons in this file, since that button is not on this tab's document. That button is in the popup's document.


/* popup and content scripts can communicate with each other and send stuff via message passing
google: send data from popup to content script
https://www.freecodecamp.org/news/chrome-extension-message-passing-essentials/
https://medium.com/hackernoon/creating-popup-chrome-extensions-that-interact-with-the-dom-27b943978daf
*/
chrome.runtime.onMessage.addListener( function(request, sender, sendResponse) {
    console.log("Received the data coming from popup.js. ");

    let downloadLinks_and_tableIndices = request.data;
    let downloadLinks = downloadLinks_and_tableIndices.download_links;
    let tableIndices = downloadLinks_and_tableIndices.table_indices;

    highlight_tables_and_show_download_links(tableIndices, downloadLinks);

    sendResponse({success: true});
});


function highlight_tables_and_show_download_links(tableIndices, downloadLinks){
   // Give green borders to caught tables, also add title with download link

    let tables = document.getElementsByTagName("table");

    // If user presses the "scan for tables" again to refresh, old links should be removed
    let check_if_already_exist = document.querySelectorAll(".already_created_");
    if (check_if_already_exist.length > 0) {
        check_if_already_exist.forEach(link => { link.remove(); });   // delete all
    }

    for (let i=0; i < tableIndices.length ; i++){
        // green highlight
        tables[tableIndices[i]].style.border = "8px solid green";
        tables[tableIndices[i]].style["border-style"] = "dashed";
        tables[tableIndices[i]].style["border-collapse"] = "separate";
        tables[tableIndices[i]].style["box-shadow"] = "green 0 0 20px 12px";

        // download links

        let download_link = document.createElement("a");
        download_link.classList.add("already_created_");
        download_link.href = downloadLinks[i];
        download_link.target = "_blank";
        download_link.style["text-decoration"] = "none";

        const download_title = document.createElement("h3");
        download_title.style["color"] = "green";
        download_title.style["text-align"] = "right";
        download_title.style["margin-bottom"] = "30px";
        download_title.style["font-size"] = "23px";
        download_title.style["margin-right"] = "5%";

        const textNode = document.createTextNode("Table " + (i+1) + " ");
        download_title.appendChild(textNode);

        let download_icon = document.createElement('img');
        //black version //download_icon.src = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAQAAADa613fAAAEo0lEQVR42u3bT0wcVRzA8e8uFLvCriRKK6ilGANNPNhqY2uhmmis0F5MTNqLiZxMrImNiY2XHmvSGIm7EC8eG4168CwmFhK1Df5LQwuUXWopmkhBDd1qFvYPOx5WurAzb/bt7Bt2hrzf78QwmTeffW/evHlvBtyMDs4RJ02aOOfowKdxiDFWMf7PPGMc8iOji/G7iLUcp8tvjCBDJoaBwRBBf0HauW4JmaHdrV/OLciDlttb/QZppMFyewP3+gsijsBWgaAhGqIhGqIhGqIhGqIhGqIhGqIhGqIhGqIhGqIhGqIhGiIX9RXsG6CdgzyGwXXG+A3DhfPZhDKaeJsEOQwMcsQ5RaPN3n1kLFesMvQpK8NRhBgoObU0HxJWCokQM5XxPtvVQl5j2XRSWWJCSuWQCENkTfuneFUl4z6+tTytLFEBpVJIhEELhoHBKBF1kKf427IQca1UBhEzDP5kr7rut4UmYa93krM214pMhDnLG8L+s4kWdZAVcjYdeHWUCO/ZMCDHirqmtZtfBRUvamCyTSts06gKmWCXyvv/R7aFmSlykEhZhkFM7ehjD1cqoshAwhKMy3SqviUeZroCSnlImFhZxjV63BiXPVsBpRwkTFSCcditIaY8xR5SY4Y8JUSvENJLqPYMWcoAx0lb/i/NcT7wAgPgubKUZX4S1siPFsPPmjDkasV5biLDTcomMwqU+FZguFErNWKoptSQoZJSY0ahM45vBYaKWvEIo1qKhxjVUDzGcErxIMMJxaOMSikeZsiNjF1iBCxmTJpp4wG2S72OH+AG0yW18nHZ73ameZ3vSiY3HpVaQjBY4S/+4DZ5+zn35xnkFxZJkZHKHBOmCYJytWKeUuhhgpxkiSkW+ZlBXiAk+m338zl3HHShU6YTs7tWzI2qmykHpd7hC/abW802+plzfFOboluSYmb0OGIUco7+jZOtdZxyVBfFnDRRrMZgqmqjmEneoq54uBPcrnrgN2n6yrCbH8hv+A7xGcUMA4MlTqwdrotrSobiZsojvMsoMyQY4TQPu8Ao1POeQrOKKns4mrT49rORNtosPhFTxTAwiFIH+6q4yOUoVqGSYTDHXjiz7ntaFTlhuuytJsSnlJa5yhkYVT4XkuBlmxWoel4RfDVaTY7AvAuzU0sM0GmxQBOkiyhLFR/vFt/wJZdICveYRzBHW23muUGMo3QQoYF7iNDBMYaYXdchy2WWT9hHiDoivMRFwV7pgCtvlBQXUReYJ0mACK3sdPQWw6e8SfLuX518xpOi8aSX85bptPut5/K9/prTRMlDAlxiwfk6e+0iSbpkyz+k/AhpNb1zsYNmP0Ie52DJlqOiVzryHr/cv9+w0n6E3627+wAp0SOjZ+Iyg1zkX1o4xknTGLoQywFm2Y3XI8siKZq5X3gpzNYz7gPINh4qs8eVIF+Txe+RYTjIV6Zbjv8iznCQm5y3n+zyfOQ5z02AFi54vAu2zwvsWDMdIOFbxgwH1lfPi8z4lHGktKU9zYjip3e3c5WRjbVRHI69w1XByzBeywxXOV28NkqXFQLsoo9enmCn5LLCZofBCguMM8wwc+ufbv8DpzW63hl9dtAAAAAASUVORK5CYII=";
        download_icon.src = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAAAXNSR0IArs4c6QAAA/BJREFUeF7t3OuR2zAMBGC4g3SQ6yQuJZ3E10lK8XXidJAOktHccU5xRIEigSWgWf+lRRL7WW/JF8n4+S53eZFvu1N/yJv8lGu28i7ZJiwtGKWohCi5QI5gJEXJA3KVm1zlR9cafZdXucuta1nwQgQBB64NRxAtIXA7QcCBa8MRREsI3E4QcODacATREgK3EwQcuDYcQbSEwO0EAQeuDUcQLSFwO0HAgWvDEURLCNxOEHDg2nAE0RICtxMEHLg2HEG0hMDtBAEHrg1HEC0hcDtBwIFrwxFESwjcThBw4NpwBNESArcTBBy4NhxBtITA7QQBB64NRxAtIXA7QcCBa8MRREsI3E4QcODacATREgK3EwQcuDYcQbSEwO0+IMvLNXufnpdnZryw41GHAmwP0vLaWc+7f2gQrzqgIC1FlAkdRUGCeNYBA+kJ7AhKT/+l+CPvGB7B6OkfBtJTyDK5VhQEiHcNDQcINvuQkbBaUUbGaFlDejGM15IYIC0oniCjGMv8W9DTrCEtO3ovEAuM04LsrSkeIFYYpwapoViDWGKcHmQLxRLEGiMcyDIhjyLXh8RWIN7zbNhx733F5iirjOBZrAWI5/wGIcritiCea8pD7kP/BvQiV/VPz46G2npSe6BfexAvlN/yS77I1wO1fX51ZNnagA4Yy1A+IF4oXRoOCzlh+IKcFcURwx/kbCjOGBiQs6AAMHAg2VFAGFiQrChADDxINhQwxhyQLCgTMOaBREeZhDEXJCrKRIz5INFQJmPEAImCEgAjDshslCAYsUBmoQTCiAeCRgmGERMEhRIQow1EeyTf4nbD1usJHrdby1xrGLNqXWVYv0G1TM7jtucWYC0gDxTkWLVal9vRlXdk/gdBQqwnjAgKMUbrFmOZywbMvyAev8jWCS7f8wzMs+8jNT5/92lenyCzMbTt+8j8omJs1PwOMvLM08ivo7asZYCWfXnUWvr8eHr+HWTk1+c1SYsgLfrwqq+y6bqExLDYfGXCWNV7kZv8Qf0IusbZO2fYOiyvHL2E3RI8hRIfZO/oq+z/1kXV3oGPuFne+IXmACkoOydU1bVv1nlV1+ZgeZQ0+iZra+fXApMMopSZD2S9w19gtj6oSz6da8HeYnlBHMKI0CVBrBTK0V3pr3MtJYgFiOE5D0EsQGp/GtBxSYogBLFIIFgfXEOCgXAfEgxkfSWBR1kBcQamxJ36QHgeixLEI9WBPgkyEJ7HogTxSHWgz9i3cAcKS7noQ94u4Z44SZmk0aTv8hr3qROjGtN083FyGe9BuTQJGk50daYf61FSwxrTdFV9lLRUkOTpjDSB70104xrY9usIRPH3rlyQ/AsiIEpxSL9pzwAAAABJRU5ErkJggg==";
        download_icon.style.height = "1em";
        download_title.appendChild(download_icon);

        download_link.appendChild(download_title);
        tables[i].parentElement.insertBefore(download_link, tables[i]);
    }

}
