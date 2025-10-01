"use strict";
const test = true;
let port = null;
const PAGINATION = {
    currentPage: 1,
    totalPage: 1,
    totalCount: 0,
};
function createItem({ no, productName, skuId, productId, vendorItemId }) {
    const el = document.createElement('div');
    el.id = `item-${skuId}`;
    el.classList.add('flex', 'flex-col', 'gap-2', 'p-3', 'bg-white', 'rounded-md', 'shadow-xs', 'product-list-item', 'item--pending', 'transition-all', 'duration-300');
    el.dataset.page = Math.ceil(Number(no) / 10).toString();
    el.innerHTML = `
    <div class="flex justify-between align-center">
      <span class="text-xs">No.${no}</span>
      <span class="flex justify-center items-center border rounded-xl px-2 text-xs/4 border-gray-300 text-gray-300 item-status item-status--pending">대기중</span>
      <span class="flex justify-center items-center border rounded-xl px-2 text-xs/4 border-yellow-500 text-yellow-500 item-status item-status--processing">처리중</span>
      <span class="flex justify-center items-center border rounded-xl px-2 text-xs/4 border-red-500 text-red-500 item-status item-status--failed hover:bg-red-100">실패</span>
      <span class="flex justify-center items-center border rounded-xl px-2 text-xs/4 border-gray-500 text-gray-600 bg-gray-100 item-status item-status--out-of-stock--temporary">일시품절</span>
      <span class="flex justify-center items-center border rounded-xl px-2 text-xs/4 border-gray-500 text-gray-600 bg-gray-100 item-status item-status--out-of-stock--permanent">영구품절</span>
      <span class="flex justify-center items-center border rounded-xl px-2 text-xs/4 border-green-500 text-green-500 item-status item-status--completed">완료됨</span>
      <span class="flex justify-center items-center border rounded-xl px-2 text-xs/4 border-blue-500 text-blue-500 item-status item-status--sent">전송됨</span>
    </div>
    <div class="flex flex-col gap-1">
      <div class="flex align-center gap-2 text-sm">
        <label class="whitespace-nowrap text-gray-500">등록명</label>
        <p class="whitespace-nowrap text-ellipsis overflow-hidden font-semibold" title="${productName}">${productName}</p>
      </div>
      <div class="flex align-center gap-2 text-sm">
        <label class="whitespace-nowrap text-gray-500">판매명</label>
        <p class="whitespace-nowrap text-ellipsis overflow-hidden item-product-name"></p>
      </div>
      <div class="flex align-center gap-2 text-sm">
        <label class="whitespace-nowrap text-gray-500">링크</label>
        <a
          class="whitespace-nowrap overflow-ellipsis overflow-hidden text-blue-500 hover:underline cursor-pointer"
          target="_blank"
          rel="noopener noreferrer"
          href="${`https://www.coupang.com/vp/products/${productId}?vendorItemId=${vendorItemId}`}"
        >
          ${`https://www.coupang.com/vp/products/${productId}?vendorItemId=${vendorItemId}`}
        </a>
      </div>
    </div>
    <div class="flex justify-between text-xs">
      <div>
        <div class="flex align-center justify-between gap-2">
          <label class="whitespace-nowrap text-gray-500">SKU</label>
          <span>${skuId}</span>
        </div>
        <div class="flex align-center justify-between gap-2">
          <label class="whitespace-nowrap text-gray-500">PROD</label>
          <span>${productId}</span>
        </div>
        <div class="flex align-center justify-between gap-2">
          <label class="whitespace-nowrap text-gray-500">VDOR</label>
          <span>${vendorItemId}</span>
        </div>
      </div>
      <div>
        <div class="flex align-center justify-between gap-2">
          <label class="whitespace-nowrap text-gray-500">정가</label>
          <span class="item-price--original font-semibold">0</span>
        </div>
        <div class="flex align-center justify-between gap-2">
          <label class="whitespace-nowrap text-gray-500">판매가</label>
          <span class="item-price--sales font-semibold">0</span>
        </div>
        <div class="flex align-center justify-between gap-2">
          <label class="whitespace-nowrap text-gray-500">할인가</label>
          <span class="item-price--final font-semibold">0</span>
        </div>
      </div>
    </div>
  `;
    return el;
}
function initPagination(cnt) {
    PAGINATION.totalPage = Math.ceil(cnt / 10);
    PAGINATION.totalCount = cnt;
    document.getElementById('pagination').innerHTML = '';
    document.getElementById('first-page-btn').addEventListener('click', () => setPage(1));
    document.getElementById('prev-page-btn').addEventListener('click', () => setPage(Math.floor((PAGINATION.currentPage - 1) / 10) * 10));
    document.getElementById('next-page-btn').addEventListener('click', () => setPage(Math.ceil(PAGINATION.currentPage / 10) * 10 + 1));
    document.getElementById('last-page-btn').addEventListener('click', () => setPage(PAGINATION.totalPage));
    checkPagination();
}
function checkPagination() {
    const currentPage = PAGINATION.currentPage;
    const totalPage = PAGINATION.totalPage;
    const currentRange = Math.ceil(currentPage / 10);
    const startPage = (currentRange - 1) * 10 + 1;
    const endPage = currentRange * 10;
    if (currentPage > 1) {
        document.getElementById('first-page-btn').classList.add('active');
        if (currentPage > 10)
            document.getElementById('prev-page-btn').classList.add('active');
        else
            document.getElementById('prev-page-btn').classList.remove('active');
    }
    else {
        document.getElementById('first-page-btn').classList.remove('active');
        document.getElementById('prev-page-btn').classList.remove('active');
    }
    if (currentPage < totalPage) {
        document.getElementById('last-page-btn').classList.add('active');
        if (Math.ceil(currentPage / 10) < Math.ceil(totalPage / 10))
            document.getElementById('next-page-btn').classList.add('active');
        else
            document.getElementById('next-page-btn').classList.remove('active');
    }
    else {
        document.getElementById('next-page-btn').classList.remove('active');
        document.getElementById('last-page-btn').classList.remove('active');
    }
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    for (let i = 1; i <= PAGINATION.totalPage; i++) {
        const el = createPagination(i);
        if (i >= startPage && i <= endPage)
            el.classList.add('active');
        if (i === currentPage)
            el.classList.add('current');
        pagination.appendChild(el);
    }
}
function createPagination(page) {
    const el = document.createElement('a');
    el.textContent = page.toString();
    el.classList.add('text-gray-500', 'cursor-pointer', 'rounded-full', 'hover:bg-gray-100', 'p-1', 'transition-all', 'duration-300', 'pagination-btn', 'text-sm');
    el.addEventListener('click', () => {
        setPage(page);
    });
    return el;
}
function setPage(page) {
    PAGINATION.currentPage = page;
    checkPagination();
    const itemList = document.getElementById('item-list').querySelectorAll('.product-list-item');
    itemList.forEach((item) => {
        item.classList.remove('item--showing');
        if (item.dataset.page === page.toString()) {
            item.classList.add('item--showing');
        }
    });
}
function setItemResult({ skuId, price, status, productName, error }) {
    const el = document.getElementById(`item-${skuId}`);
    if (!el)
        return;
    // MODIFIED: 모든 상태 클래스 제거 (sent 포함)
    el.classList.remove('item--pending');
    el.classList.remove('item--processing');
    el.classList.remove('item--completed');
    el.classList.remove('item--out-of-stock--temporary');
    el.classList.remove('item--out-of-stock--permanent');
    el.classList.remove('item--failed');
    el.classList.remove('item--sent');
    el.classList.add(`item--${status}`);
    if (status === 'failed') {
        const statusEl = el.querySelector('.item-status.item-status--failed');
        if (statusEl)
            statusEl.title = error || '';
    }
    if (productName) {
        const productNameEl = el.querySelector('.item-product-name');
        productNameEl.title = productName;
        productNameEl.textContent = productName;
    }
    const { original, sales, final } = price || { original: 0, sales: 0, final: 0 };
    el.querySelector('.item-price--original').textContent = original.toLocaleString();
    el.querySelector('.item-price--sales').textContent = sales.toLocaleString();
    el.querySelector('.item-price--final').textContent = final.toLocaleString();
}
function ensurePortConnected() {
    if (port)
        return true;
    try {
        port = chrome.runtime.connect({ name: 'panel' });
        port.onMessage.addListener(handleCrawlMessage);
        port.onDisconnect.addListener(() => { port = null; });
        return true;
    }
    catch (err) {
        alert(err.message);
        return false;
    }
}
function startCrawling() {
    port?.postMessage({ type: 'CRAWL_START' });
}
function stopCrawling() {
    port?.postMessage({ type: 'CRAWL_STOP' });
}
function stopRetry() {
    port?.postMessage({ type: 'RETRY_STOP' });
}
function handleCrawlMessage(msg) {
    const { type, data, error } = msg;
    console.log(`크롤러 메세지: ${type}`, data);
    switch (type) {
        case 'CRAWL_START':
            break;
        case 'CRAWL_STOP':
            break;
        case 'CRAWL_SUCCESS':
            document.getElementById('retry-info').classList.remove('active');
            setItemResult(data);
            break;
        case 'CRAWL_PROGRESS':
            document.getElementById('init-btn').disabled = true;
            document.getElementById('crawl-start-btn').disabled = true;
            document.getElementById('crawl-stop-btn').disabled = false;
            setItemResult(data);
            break;
        case 'CRAWL_COMPLETE':
            alert("크롤링이 완료되었습니다");
            break;
        case 'CRAWL_ERROR':
            handleCrawlError(data, error);
            break;
        case 'CRAWL_RETRY':
            renderRetryTimer(data);
            break;
        case 'CRAWL_BATCH_COMPLETE':
            // MODIFIED: 배치 완료 시 'sent' 상태로 업데이트
            updateBatchToSent(data);
            updateProgressBar(data);
            break;
        case 'CRAWL_FAILED':
            handleCrawlFailed(data);
            break;
        case 'RETRY_STOP':
            document.getElementById('retry-info').classList.remove('active');
            break;
        default:
            break;
    }
}
/**
 * MODIFIED: 배치 전송 완료 시 해당 아이템들을 'sent' 상태로 변경
 */
function updateBatchToSent(data) {
    const { resultList } = data;
    if (Array.isArray(resultList)) {
        resultList.forEach((result) => {
            setItemResult({ ...result, status: 'sent' });
        });
    }
}
function handleCrawlError(data, error) {
    setItemResult({ ...data, error });
    document.getElementById('init-btn').disabled = false;
    document.getElementById('crawl-start-btn').disabled = false;
    document.getElementById('crawl-stop-btn').disabled = true;
    console.error(`크롤링에 실패했습니다. SKU ID: ${data?.skuId || 'N/A'}, ERROR: ${error || 'N/A'}`);
}
function handleCrawlFailed(data) {
    document.getElementById("retry-info").classList.remove('active');
    window.alert(`크롤링이 중단되었습니다. SKU ID: ${data?.skuId || 'N/A'}, ERROR: ${data?.error || 'N/A'}`);
}
function renderRetryTimer(data) {
    const { currentIndex, skuId, retryCount, maxRetries, retryInterval } = data;
    const retryInfo = document.getElementById('retry-info');
    if (!retryInfo)
        return;
    retryInfo.classList.add('active');
    const failTime = document.getElementById('fail-time');
    const failProductName = document.getElementById('fail-product-name');
    const failRetryCount = document.getElementById('fail-retry-count');
    const failNextTime = document.getElementById('fail-next-time');
    failTime.title = pattenizeTime(new Date().getTime());
    failProductName.textContent = `No.${currentIndex + 1} - ${skuId}`;
    failRetryCount.textContent = `${retryCount.toString()}/${maxRetries.toString()}`;
    failNextTime.textContent = pattenizeTime(new Date().getTime() + retryInterval);
    failProductName.addEventListener('click', () => {
        const page = Math.ceil((currentIndex + 1) / 10);
        setPage(page);
        const item = document.getElementById(`item-${skuId}`);
        if (item)
            item.scrollIntoView({ behavior: 'smooth' });
    });
}
function pattenizeTime(time) {
    const date = new Date(time);
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
}
function setProgressBar(pageSize, currentIndex) {
    const progressBar = document.getElementById('progress-bar');
    if (!progressBar)
        return;
    progressBar.innerHTML = '';
    for (let i = 0; i < pageSize; i++) {
        const el = document.createElement('div');
        el.classList.add('rounded-sm', 'flex-1', 'h-4', 'border', 'transition-all', 'duration-200', 'progress-fill', 'progress-fill--waiting');
        if (i < currentIndex)
            el.classList.add('progress-fill--completed');
        progressBar.appendChild(el);
    }
}
function updateProgressBar(data) {
    const { currentIndex, pageSize, totalCount } = data;
    const nextProgressFill = document.querySelector('.progress-fill--waiting');
    if (!nextProgressFill)
        return;
    nextProgressFill.classList.remove('progress-fill--waiting');
    nextProgressFill.classList.add('progress-fill--completed');
    nextProgressFill.title = `서버 전송 완료(${currentIndex - pageSize + 1}~${currentIndex} / ${totalCount}) - ${pattenizeTime(new Date().getTime())}`;
}
document.addEventListener('DOMContentLoaded', () => {
    // 기존 상태 불러오기
    chrome.runtime.sendMessage({ type: 'GET_CURRENT_STATUS' }, (response) => {
        if (response.error) {
            alert(`기존 상태를 불러오지 못했습니다: ${response.error}`);
        }
        else {
            const { taskList, resultList, refetchedAt, currentIndex, batchSize } = response.data;
            if (!taskList?.length)
                return;
            document.getElementById('task-container').classList.add('active');
            document.getElementById('crawl-start-btn').disabled = false;
            if (refetchedAt) {
                const btn = document.getElementById('init-btn');
                btn.dataset.refetchedat = new Date(refetchedAt).toISOString();
                btn.innerHTML = `목록 갱신 (마지막: ${new Date(refetchedAt).toLocaleString()})`;
            }
            const itemList = document.getElementById('item-list');
            taskList.forEach((item, index) => {
                itemList.appendChild(createItem({ ...item, no: index + 1 }));
            });
            initPagination(taskList.length);
            setPage(1);
            // MODIFIED: 저장된 결과 상태 복원
            if (resultList?.length > 0) {
                resultList.forEach((item) => {
                    setItemResult(item);
                });
            }
            setProgressBar(Math.ceil(taskList.length / batchSize), Math.floor(currentIndex / batchSize));
        }
    });
    // 대기중 아이템 추가
    document.getElementById('init-btn')?.addEventListener('click', (el) => {
        const btn = el.target;
        if (!!btn.dataset.refetchedat) {
            if (!window.confirm('기존 작업 내역이 사라집니다. 다시 불러오시겠습니까?'))
                return;
        }
        if (!ensurePortConnected())
            return;
        btn.dataset.refetchedat = new Date().toISOString();
        btn.innerHTML = `목록 갱신 (마지막: ${new Date(btn.dataset.refetchedat).toLocaleString()})`;
        chrome.runtime.sendMessage({
            type: 'FETCH_TARGET_LIST'
        }, (response) => {
            if (response.error) {
                alert(response.error);
            }
            else {
                const { batchSize, taskList } = response.data;
                const itemList = document.getElementById('item-list');
                taskList.forEach((item, index) => {
                    itemList.appendChild(createItem({ ...item, no: index + 1 }));
                });
                initPagination(taskList.length);
                setPage(1);
                document.getElementById('crawl-start-btn').disabled = false;
                document.getElementById('task-container').classList.add('active');
                setProgressBar(Math.ceil(taskList.length / batchSize), 0);
            }
        });
    });
    // 크롤링 시작
    document.getElementById('crawl-start-btn')?.addEventListener('click', () => {
        if (!ensurePortConnected())
            return;
        if (document.getElementById('retry-info').classList.contains('active')) {
            const isConfirmed = window.confirm('재시도 대기중인 제품이 있습니다. 계속 진행하시겠습니까? 재시도 카운트가 초기화됩니다.');
            if (!isConfirmed)
                return;
        }
        document.getElementById('init-btn').disabled = true;
        document.getElementById('crawl-start-btn').disabled = true;
        document.getElementById('crawl-stop-btn').disabled = false;
        startCrawling();
    });
    // 크롤링 정지
    document.getElementById('crawl-stop-btn')?.addEventListener('click', () => {
        document.getElementById('init-btn').disabled = false;
        document.getElementById('crawl-start-btn').disabled = false;
        document.getElementById('crawl-stop-btn').disabled = true;
        stopCrawling();
    });
    // 재시도 중단
    document.getElementById('retry-stop-btn')?.addEventListener('click', () => {
        stopRetry();
    });
});
window.addEventListener("unload", () => {
    if (port) {
        port.disconnect();
        port = null;
    }
});
//# sourceMappingURL=panel.js.map