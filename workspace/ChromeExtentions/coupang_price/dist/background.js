import Crawler from "./crawler.js";
// MODIFIED: 브라우저 세션 식별을 위한 고유 ID 생성
const SESSION_ID = `${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
// Chrome Port와 크롤러 인스턴스 매핑용
const crawlers = new Map();
// 상태 + 설정용 객체들
let config;
let taskList;
let resultList;
let currentIndex;
let refetchedAt;
let crawler;
// 기존 상태 복원
const savedPromise = chrome.storage.local.get(['taskList', 'currentIndex', 'resultList', 'refetchedAt', 'isRunning', 'retryCount', 'sessionId']);
const configPromise = (async () => {
    const keys = await chrome.storage.local.get(null);
    if (Object.keys(keys).includes('config')) {
        const result = await chrome.storage.local.get(['config']);
        return result.config;
    }
    else {
        const res = await fetch(chrome.runtime.getURL('config/settings.json'));
        return await res.json();
    }
})();
const initPromise = Promise.all([savedPromise, configPromise])
    .then(([saved, cfg]) => {
    config = cfg;
    taskList = Array.isArray(saved.taskList) ? saved.taskList : [];
    resultList = Array.isArray(saved.resultList) ? saved.resultList : [];
    currentIndex = typeof saved.currentIndex === 'number' ? saved.currentIndex : 0;
    refetchedAt = typeof saved.refetchedAt === 'number' ? saved.refetchedAt : 0;
    // MODIFIED: 이전 세션의 alarm 모두 제거
    chrome.alarms.clearAll();
    // MODIFIED: 세션 ID 저장 및 이전 세션인지 확인
    const savedSessionId = saved.sessionId;
    const isNewSession = !savedSessionId || savedSessionId !== SESSION_ID;
    chrome.storage.local.set({ sessionId: SESSION_ID });
    // MODIFIED: 새 세션인 경우, flush되지 않은 결과 제거 및 인덱스 초기화
    if (isNewSession) {
        // MODIFIED: 'sent' 상태가 아닌 결과 제거
        const sentResults = resultList.filter(r => r.status === 'sent');
        // MODIFIED: 전송된 결과의 개수로 currentIndex 설정
        const newCurrentIndex = sentResults.length;
        resultList = sentResults;
        currentIndex = newCurrentIndex;
        // 저장
        chrome.storage.local.set({
            isRunning: false,
            resultList: sentResults,
            currentIndex: newCurrentIndex
        });
        console.log(`새 세션 시작: flush되지 않은 결과 제거 완료. 새 인덱스: ${newCurrentIndex}`);
    }
})
    .catch(err => console.error(`크롤러 초기화 실패: ${err}`));
/**
 * MODIFIED: 단일 아이템 결과를 resultList에 추가/업데이트
 */
function addOrUpdateResult(result) {
    const idx = resultList.findIndex((r) => r.skuId === result.skuId);
    if (idx >= 0) {
        resultList[idx] = result;
    }
    else {
        resultList.push(result);
    }
    // MODIFIED: 매 아이템마다 저장
    chrome.storage.local.set({ resultList });
}
/**
 * MODIFIED: 배치 전송 완료 시 상태를 'sent'로 업데이트
 */
function markBatchAsSent(batchResults) {
    batchResults.forEach(result => {
        const idx = resultList.findIndex(r => r.skuId === result.skuId);
        if (idx >= 0 && resultList[idx]) {
            resultList[idx].status = 'sent';
        }
    });
    // 저장
    chrome.storage.local.set({ resultList });
}
/** 패널 열기 */
chrome.action.onClicked.addListener(async (tab) => {
    if (chrome.sidePanel && chrome.sidePanel.open) {
        await chrome.sidePanel.open({ windowId: tab.windowId });
    }
    else {
        console.warn('sidePanel API를 지원하지 않는 브라우저입니다.');
    }
});
/** 단일 응답 메세지 수신 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'GET_CONFIG') {
        sendResponse({
            data: config.crawling
        });
        return true;
    }
    if (request.type === 'GET_CURRENT_STATUS') {
        initPromise.then(() => {
            const batchSize = crawler?.config?.batchSize || config?.crawling?.batchSize || 10;
            sendResponse({
                data: {
                    taskList,
                    resultList,
                    currentIndex,
                    batchSize,
                    refetchedAt
                }
            });
        });
        return true;
    }
    if (request.type === 'UPDATE_CONFIG') {
        config = {
            ...config,
            crawling: request.payload
        };
        chrome.storage.local.set({ config });
        const crawler = crawlers.get("panel");
        if (crawler)
            crawler.config = config.crawling;
        sendResponse({ data: config.crawling });
        return true;
    }
    if (request.type === 'FETCH_TARGET_LIST') {
        const cralwingOptions = crawler?.config;
        fetch(`${config.api.server}/collect`)
            .then(res => res.json())
            .then((data) => {
            if (Array.isArray(data)) {
                taskList = data;
                currentIndex = 0;
                refetchedAt = Date.now();
                resultList = [];
                if (crawler)
                    crawler.setTaskList = data;
                chrome.storage.local.set({ taskList, currentIndex, refetchedAt, resultList });
                sendResponse({ data: { batchSize: cralwingOptions?.batchSize || 10, taskList } });
            }
            else {
                sendResponse({ error: "대상 목록 불러오기 실패" });
            }
        })
            .catch(error => {
            console.error("대상 목록 불러오기 실패", error);
            sendResponse({ error: error.message });
        });
        return true;
    }
    return true;
});
/** 실시간 메세지 포트 유지 */
chrome.runtime.onConnect.addListener((port) => {
    if (port.name === "panel") {
        // MODIFIED: 패널 연결 시 크롤러가 없으면 생성, 있으면 포트만 교체
        if (!crawler) {
            // MODIFIED: 반드시 SESSION_ID를 전달하여 크롤러 생성
            crawler = new Crawler(port, SESSION_ID);
            crawler.config = config.crawling;
            crawler.setTaskList = taskList;
            crawler.setCurrentIndex = currentIndex;
            // MODIFIED: 콜백 함수 변경
            crawler.onItemComplete = (result) => addOrUpdateResult(result);
            crawler.onBatchSent = (batchResults, index) => {
                markBatchAsSent(batchResults);
                currentIndex = index;
                chrome.storage.local.set({ currentIndex });
            };
            crawlers.set("panel", crawler);
            // MODIFIED: 브라우저 재시작 후 패널 연결 시에는 자동 시작하지 않음
            // (사용자가 명시적으로 시작 버튼을 눌러야 함)
            chrome.storage.local.set({ isRunning: false });
        }
        else {
            // 패널 재연결 시 포트만 교체
            crawler.port = port;
        }
        port.onDisconnect.addListener(() => {
            // 포트 끊기
            // crawlers.delete("panel");
            crawler.port = null;
        });
        port.onMessage.addListener(async (msg) => {
            switch (msg.type) {
                case 'CRAWL_START':
                    crawler?.start();
                    break;
                case 'CRAWL_STOP':
                    crawler?.stop();
                    break;
                case 'RETRY_STOP':
                    crawler?.stopRetry();
                    break;
            }
        });
    }
});
// MODIFIED: 알람으로 예약된 작업 처리 (세션 검증 추가)
chrome.alarms.onAlarm.addListener((alarm) => {
    if (!crawler || !taskList || taskList.length === 0)
        return;
    // MODIFIED: alarm name에서 세션 ID 추출 및 검증
    const alarmNameParts = alarm.name.split(':');
    if (alarmNameParts.length < 3)
        return; // 잘못된 형식
    const alarmSessionId = alarmNameParts[0];
    const alarmType = alarmNameParts[1];
    const alarmAction = alarmNameParts[2];
    // MODIFIED: 현재 세션과 alarm의 세션이 일치하는지 확인
    if (alarmSessionId !== SESSION_ID) {
        console.log(`다른 세션의 alarm 무시: ${alarm.name}`);
        chrome.alarms.clear(alarm.name); // 다른 세션의 alarm 제거
        return;
    }
    if (alarmType === 'crawler' && (alarmAction === 'next' || alarmAction === 'retry')) {
        crawler.tick();
    }
});
//# sourceMappingURL=background.js.map