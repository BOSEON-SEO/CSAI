"use strict";
document.addEventListener("DOMContentLoaded", () => {
    chrome.runtime.sendMessage({ type: 'GET_CONFIG' }, (response) => {
        if (response.error) {
            alert(`저장된 설정을 불러오지 못했습니다: ${response.error}`);
        }
        else {
            const { batchSize, interval: { min, max }, retry: { max: retryMax, interval: retryInterval } } = response.data;
            document.getElementById('batchSize').value = batchSize.toString();
            document.getElementById('intervalMin').value = (min / 1000).toString();
            document.getElementById('intervalMax').value = (max / 1000).toString();
            document.getElementById('retryMax').value = retryMax.toString();
            document.getElementById('retryInterval').value = (retryInterval / 1000).toString();
        }
    });
    document.getElementById("configForm").addEventListener("submit", (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const config = Object.fromEntries(formData);
        const { batchSize, intervalMin, intervalMax, retryMax, retryInterval } = config;
        chrome.runtime.sendMessage({ type: 'UPDATE_CONFIG', payload: {
                batchSize: parseInt(batchSize),
                interval: {
                    min: parseInt(intervalMin) * 1000,
                    max: parseInt(intervalMax) * 1000
                },
                retry: {
                    max: parseInt(retryMax),
                    interval: parseInt(retryInterval) * 1000
                }
            } }, (response) => {
            if (response.error) {
                alert(`설정을 저장하지 못했습니다: ${response.error}`);
            }
            else {
                alert("설정이 저장되었습니다.");
            }
        });
    });
});
//# sourceMappingURL=options.js.map