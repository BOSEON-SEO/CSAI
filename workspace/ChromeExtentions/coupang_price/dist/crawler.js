/**
 * 쿠팡 가격 크롤러 싱글톤 클래스
 * 브라우저 세션 단위로 동작하며, 다른 세션의 작업과 격리됨
 */
export default class Crawler {
    constructor(port, sessionId, opt) {
        this.tabId = 0;
        // 1. 전체 작업 대상 및 현재 작업...
        this.refetchedAt = 0;
        this.taskList = [];
        this.currentIndex = 0;
        this.isRunning = false;
        // MODIFIED: 콜백 함수 변경
        this.onItemComplete = () => { };
        this.onBatchSent = () => { };
        this.fetchInterval = {
            min: 1000 * 10,
            max: 1000 * 15,
        };
        this.nextTaskTimer = null;
        // 2. 결과 페이로드/배치
        this.batchSize = 10;
        this.resultBatch = [];
        // 3. 재시도 관련 상태
        this.retryCount = 0;
        this.maxRetries = 3;
        this.retryInterval = 1000 * 60 * 10; // 10분
        this.retryTimer = null;
        this.port = port || null;
        // MODIFIED: 세션 ID 설정 (없으면 생성)
        this.sessionId = sessionId || `${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
        opt && (this.config = opt);
    }
    get config() {
        return {
            batchSize: this.batchSize,
            interval: this.fetchInterval,
            retry: {
                max: this.maxRetries,
                interval: this.retryInterval
            }
        };
    }
    set config(opt) {
        this.fetchInterval = opt.interval || this.fetchInterval;
        this.batchSize = opt.batchSize || this.batchSize;
        this.maxRetries = opt.retry.max || this.maxRetries;
        this.retryInterval = opt.retry.interval || this.retryInterval;
    }
    set setTaskList(taskList) {
        this.refetchedAt = Date.now();
        this.taskList = taskList;
        this.currentIndex = 0;
        this.isRunning = false;
        this.retryCount = 0;
        this.retryTimer = null;
        chrome.storage.local.set({
            taskList,
            currentIndex: 0,
            refetchedAt: this.refetchedAt,
        });
    }
    set setCurrentIndex(currentIndex) {
        this.currentIndex = currentIndex;
    }
    start() {
        if (this.isRunning)
            return;
        if (!this.taskList || this.taskList.length === 0) {
            this.isRunning = false;
            chrome.storage.local.set({ isRunning: false });
            return;
        }
        this.isRunning = true;
        chrome.storage.local.set({ isRunning: true });
        if (this.tabId) {
            chrome.tabs.get(this.tabId, (tab) => {
                if (chrome.runtime.lastError || !tab || tab.status !== 'complete') {
                    chrome.tabs.create({ url: 'about:blank' }, (newTab) => {
                        this.tabId = newTab.id;
                        this.processNextTask();
                    });
                }
                else {
                    this.processNextTask();
                }
            });
        }
        else {
            chrome.tabs.create({ url: 'about:blank' }, (newTab) => {
                this.tabId = newTab.id;
                this.processNextTask();
            });
        }
    }
    stop() {
        this.isRunning = false;
        this.retryCount = 0;
        if (this.retryTimer)
            clearTimeout(this.retryTimer);
        this.retryTimer = null;
        if (this.nextTaskTimer)
            clearTimeout(this.nextTaskTimer);
        this.nextTaskTimer = null;
        // MODIFIED: 세션 ID를 포함한 alarm name으로 제거
        chrome.alarms.clear(`${this.sessionId}:crawler:next`);
        chrome.alarms.clear(`${this.sessionId}:crawler:retry`);
        chrome.storage.local.set({ isRunning: false });
    }
    stopRetry() {
        this.isRunning = false;
        this.retryCount = 0;
        if (this.retryTimer)
            clearTimeout(this.retryTimer);
        this.retryTimer = null;
        if (this.nextTaskTimer)
            clearTimeout(this.nextTaskTimer);
        this.nextTaskTimer = null;
        // MODIFIED: 세션 ID를 포함한 alarm name으로 제거
        chrome.alarms.clear(`${this.sessionId}:crawler:retry`);
        this.port?.postMessage({
            type: 'RETRY_STOP'
        });
    }
    get isWorking() {
        return this.isRunning;
    }
    /**
     * Chrome alarm에서 호출할 외부 트리거
     */
    tick() {
        this.processNextTask();
    }
    /** 개별 크롤링 수행 */
    async processNextTask() {
        if (!this.isRunning)
            return;
        const item = this.taskList[this.currentIndex];
        if (!item)
            return;
        // 크롤링 내부 함수
        const doCrawl = (tabId) => {
            try {
                const { skuId, productId, vendorItemId } = item;
                if (!skuId || !productId || !vendorItemId) {
                    this.handleError(new Error('제품의 필수 파라미터가 존재하지 않습니다.'), item);
                    return;
                }
                const url = `https://www.coupang.com/vp/products/${productId}?vendorItemId=${vendorItemId}`;
                chrome.tabs.update(tabId, { url }, () => {
                    const listener = (updatedTabId, info) => {
                        if (updatedTabId === tabId && info.status === 'complete') {
                            chrome.tabs.onUpdated.removeListener(listener);
                            chrome.scripting.executeScript({
                                target: { tabId },
                                func: (skuId) => {
                                    function parseProductsPrice(html) {
                                        const parser = new DOMParser();
                                        const doc = parser.parseFromString(html, "text/html");
                                        const originalPriceText = doc?.querySelector(".original-price .price-amount")?.textContent;
                                        const salesPriceText = doc?.querySelector(".sales-price .price-amount")?.textContent;
                                        const finalPriceText = doc?.querySelector(".final-price .price-amount")?.textContent;
                                        return {
                                            originalPrice: originalPriceText ? parseInt(originalPriceText.replace(/,/g, "").replace(/원/g, "")) : 0,
                                            salesPrice: salesPriceText ? parseInt(salesPriceText.replace(/,/g, "").replace(/원/g, "")) : 0,
                                            finalPrice: finalPriceText ? parseInt(finalPriceText.replace(/,/g, "").replace(/원/g, "")) : 0,
                                        };
                                    }
                                    return new Promise((resolve, reject) => {
                                        const mainContainer = document.querySelector(".prod-atf");
                                        if (!mainContainer) {
                                            reject(new Error("상품 정보를 찾을 수 없습니다."));
                                            return;
                                        }
                                        const el = document.querySelector(".prod-atf .price-container");
                                        if (el) {
                                            const { originalPrice, salesPrice, finalPrice } = parseProductsPrice(el.outerHTML);
                                            const outOfStockLabel = mainContainer.querySelector(".out-of-stock-label");
                                            resolve({
                                                skuId,
                                                price: {
                                                    original: originalPrice,
                                                    sales: salesPrice,
                                                    final: finalPrice
                                                },
                                                status: outOfStockLabel ? "out-of-stock--temporary" : "completed",
                                                productName: document.title,
                                            });
                                        }
                                        else {
                                            const prodNotFindEl1 = mainContainer.querySelector(".prod-not-find-known__buy__options");
                                            const prodNotFindEl2 = mainContainer.querySelector(".prod-not-find-known__buy__info");
                                            const prodNotFindEl3 = mainContainer.querySelector(".prod-not-find-known__buy__btn");
                                            if (prodNotFindEl1 && prodNotFindEl2 && prodNotFindEl3) {
                                                resolve({
                                                    skuId,
                                                    productName: document.title,
                                                    status: "out-of-stock--permanent"
                                                });
                                            }
                                        }
                                    });
                                },
                                args: [skuId],
                            }, (results) => {
                                if (chrome.runtime.lastError) {
                                    this.handleError(new Error(chrome.runtime.lastError.message), item);
                                    return;
                                }
                                const resultObj = results?.[0]?.result;
                                if (!resultObj) {
                                    this.handleError(new Error("크롤링 결과가 없습니다."), item);
                                    return;
                                }
                                this.handleSuccess(resultObj);
                            });
                        }
                    };
                    chrome.tabs.onUpdated.addListener(listener);
                });
            }
            catch (err) {
                this.handleError(err, item);
            }
        };
        if (!this.tabId) {
            chrome.tabs.create({ url: 'about:blank' }, (tab) => {
                this.tabId = tab.id;
                doCrawl(this.tabId);
            });
            return;
        }
        chrome.tabs.get(this.tabId, (tab) => {
            if (chrome.runtime.lastError || !tab) {
                // 탭이 사라졌거나(닫힘), 비정상 상태
                chrome.tabs.create({ url: 'about:blank' }, (newTab) => {
                    this.tabId = newTab.id;
                    doCrawl(this.tabId);
                });
            }
            else {
                // 정상적인 탭이면 진행!
                doCrawl(this.tabId);
            }
        });
    }
    handleError(err, item) {
        this.isRunning = false;
        this.nextTaskTimer && clearTimeout(this.nextTaskTimer);
        this.nextTaskTimer = null;
        const errorMessage = err.message.includes("error page")
            ? "쿠팡 페이지 차단"
            : err.message;
        this.port?.postMessage({
            type: 'CRAWL_ERROR',
            error: errorMessage,
            ...(item && {
                data: {
                    skuId: item.skuId,
                    status: 'failed',
                    error: err.message
                }
            })
        });
        if (!item)
            return;
        if (this.retryCount < this.maxRetries) {
            this.retryTask(item);
        }
        else {
            this.isRunning = false;
            this.retryTimer && clearTimeout(this.retryTimer);
            this.retryTimer = null;
            this.port?.postMessage({
                type: 'CRAWL_FAILED',
                data: {
                    skuId: item.skuId,
                    error: errorMessage
                }
            });
            chrome.notifications.create(`coupang-crawl-${item.skuId}-failed`, {
                type: 'basic',
                iconUrl: chrome.runtime.getURL('icon.png'),
                title: '쿠팡 크롤링 중단',
                message: `skuId: ${item.skuId}, error: ${err.message}`,
                priority: 2
            });
            chrome.storage.local.set({ isRunning: false });
        }
    }
    handleSuccess(resultObj) {
        this.resultBatch.push(resultObj);
        this.retryCount = 0;
        if (this.retryTimer)
            clearTimeout(this.retryTimer);
        this.retryTimer = null;
        if (this.nextTaskTimer)
            clearTimeout(this.nextTaskTimer);
        this.nextTaskTimer = null;
        // MODIFIED: 매 아이템마다 콜백 호출 (상태 저장)
        if (typeof this.onItemComplete === 'function') {
            this.onItemComplete(resultObj);
        }
        this.port?.postMessage({
            type: 'CRAWL_SUCCESS',
            data: {
                currentIndex: this.currentIndex,
                totalCount: this.taskList.length,
                ...resultObj
            }
        });
        // MODIFIED: 배치가 완료되면 서버로 전송
        if (this.resultBatch.length >= this.batchSize) {
            this.flushResultBatch();
        }
        else if (this.currentIndex >= this.taskList.length - 1) {
            // 마지막 아이템인 경우
            this.flushResultBatch(true);
        }
        this.currentIndex++;
        chrome.storage.local.set({ currentIndex: this.currentIndex });
        this.port?.postMessage({
            type: 'CRAWL_PROGRESS',
            data: {
                currentIndex: this.currentIndex,
                totalCount: this.taskList.length,
                ...this.taskList[this.currentIndex],
                status: 'processing'
            }
        });
        // MODIFIED: 세션 ID를 포함한 alarm name으로 생성
        chrome.alarms.create(`${this.sessionId}:crawler:next`, { when: Date.now() + this.getRandomInterval() });
    }
    retryTask(item) {
        this.isRunning = true;
        this.retryCount++;
        chrome.storage.local.set({ isRunning: true, retryCount: this.retryCount });
        // MODIFIED: 세션 ID를 포함한 alarm name으로 생성
        chrome.alarms.create(`${this.sessionId}:crawler:retry`, { when: Date.now() + this.retryInterval });
        this.port?.postMessage({
            type: 'CRAWL_RETRY',
            data: {
                currentIndex: this.currentIndex,
                totalCount: this.taskList.length,
                skuId: item.skuId,
                retryCount: this.retryCount,
                maxRetries: this.maxRetries,
                retryInterval: this.retryInterval
            }
        });
    }
    /**
     * 랜덤 인터벌 계산
     */
    getRandomInterval() {
        const { min, max } = this.fetchInterval;
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }
    /**
     * 수집 결과를 배치로 서버에 전송
     */
    flushResultBatch(isLast = false) {
        const batchToSend = [...this.resultBatch]; // 복사본 생성
        fetch("https://api.tbnws.co.kr/api/open/crawler/coupang/price", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                result: batchToSend.map((r) => ({
                    sku_id: r.skuId,
                    product_id: this.taskList.find(t => t.skuId === r.skuId)?.productId,
                    vendor_item_id: this.taskList.find(t => t.skuId === r.skuId)?.vendorItemId,
                    page_title: r.productName,
                    original_price: r.price?.original || 0,
                    sales_price: r.price?.sales || 0,
                    final_price: r.price?.final || 0,
                    is_soldout: r.status === 'out-of-stock--temporary' || r.status === 'out-of-stock--permanent',
                    soldout_type: r.status === 'out-of-stock--temporary' ? 'T' : r.status === 'out-of-stock--permanent' ? 'P' : null,
                })),
                totalCnt: this.taskList.length,
                isLast,
                ...(isLast && {
                    successCount: batchToSend.filter(r => r.status === 'completed').length,
                    failedCount: batchToSend.filter(r => r.status === 'failed').length,
                }),
            })
        })
            .then((res) => {
            if (!res.ok)
                throw new Error('결과를 전송하지 못했습니다.');
            // MODIFIED: 배치 전송 완료 시 콜백 호출 (상태를 'sent'로 변경)
            if (typeof this.onBatchSent === 'function') {
                this.onBatchSent(batchToSend, this.currentIndex);
            }
            this.port?.postMessage({
                type: 'CRAWL_BATCH_COMPLETE',
                data: {
                    resultList: batchToSend,
                    currentIndex: this.currentIndex,
                    totalCount: this.taskList.length,
                    pageSize: this.batchSize,
                    isLast
                }
            });
            this.resultBatch = [];
        })
            .catch((err) => {
            console.error(err);
            alert("수집 결과 전송에 실패했습니다! 개발팀에 문의 부탁드립니다.");
            // this.handleError(err);
        });
    }
}
;
//# sourceMappingURL=crawler.js.map