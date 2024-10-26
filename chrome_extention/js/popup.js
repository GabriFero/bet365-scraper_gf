document.getElementById('saveBtn').addEventListener('click', function() {
    const apiUrl = document.getElementById('apiUrl').value;

    // save API URL
    chrome.storage.sync.set({ apiUrl: apiUrl }, function() {
        console.log('API URL saved:', apiUrl);
    });
});
