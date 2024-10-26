function injectJs(href, callback){
    const script = document.createElement("script");
    script.setAttribute("type", "text/javascript");
    script.src = href;
    script.onload = callback;
    document.body.appendChild(script);
}

injectJs(chrome.runtime.getURL("js/hook.js"));


var cachedApiUrl = "http://127.0.0.1:8485";

chrome.storage.sync.get('apiUrl', function(result) {
    if (result.apiUrl) {
        cachedApiUrl = result.apiUrl;
        console.log("API URL cached:", cachedApiUrl);
    } else {
        console.log("No API URL found in storage");
    }
});

chrome.storage.onChanged.addListener(function(changes, namespace) {
    if (changes.apiUrl) {
        cachedApiUrl = changes.apiUrl.newValue;
        console.log("API URL updated in cache:", cachedApiUrl);
    }
});

window.addEventListener("sendToAPI", async Ot => {
     if (cachedApiUrl) {
        fetch(cachedApiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({data: Ot.detail})
        })
        .then(response => response.json())
        .then(responseData => {
            console.log("Response from API:", responseData);
        })
        .catch(error => {
            console.error("Error during API request:", error);
        });
    }
    else {
        console.error("No API URL cached");
    }
})