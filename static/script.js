let currentPage = 1;
const itemsPerPage = 20;

async function fetchData(endpoint, page = 1, method = 'POST') {
    const form = document.getElementById('browser-form');
    const previewSpinner = document.getElementById('preview-spinner');
    const downloadSpinner = document.getElementById('download-spinner');

    if (endpoint === '/preview') previewSpinner.classList.remove('hidden');
    else if (endpoint === '/download') downloadSpinner.classList.remove('hidden');

    try {
        let response;
        if (method === 'POST') {
            const formData = new FormData(form);
            response = await fetch(endpoint, {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });
        } else {
            response = await fetch(`${endpoint}?page=${page}`, {
                method: 'GET',
                credentials: 'same-origin'
            });
        }

        if (response.status === 405) {
            throw new Error('Phương thức HTTP không được phép. Vui lòng kiểm tra phương thức gửi yêu cầu.');
        }

        if (response.headers.get('content-type').includes('application/json')) {
            const result = await response.json();
            if (result.error) {
                Toastify({
                    text: `<span style="color: white; margin-right: 8px;">✖</span>Lỗi: ${result.error}`,
                    duration: 3000,
                    gravity: "top",
                    position: "right",
                    backgroundColor: "#EF4444",
                    className: "rounded-toast",
                    stopOnFocus: true,
                    escapeMarkup: false
                }).showToast();
                return null;
            }
            Toastify({
                text: `<span style="color: white; margin-right: 8px;">✔</span>${endpoint === '/preview' ? "Xem trước dữ liệu thành công!" : "Tải xuống CSV thành công!"}`,
                duration: 3000,
                gravity: "top",
                position: "right",
                backgroundColor: "#10B981",
                className: "rounded-toast",
                stopOnFocus: true,
                escapeMarkup: false
            }).showToast();
            return result;
        } else {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = response.headers.get('content-disposition')?.split('filename=')[1] || 'browser_data.csv';
            a.click();
            window.URL.revokeObjectURL(url);
            Toastify({
                text: `<span style="color: white; margin-right: 8px;">✔</span>Tải xuống CSV thành công!`,
                duration: 3000,
                gravity: "top",
                position: "right",
                backgroundColor: "#10B981",
                className: "rounded-toast",
                stopOnFocus: true,
                escapeMarkup: false
            }).showToast();
            return null;
        }
    } catch (error) {
        Toastify({
            text: `<span style="color: white; margin-right: 8px;">✖</span>Lỗi: ${error.message}`,
            duration: 3000,
            gravity: "top",
            position: "right",
            backgroundColor: "#EF4444",
            className: "rounded-toast",
            stopOnFocus: true,
            escapeMarkup: false
        }).showToast();
        return null;
    } finally {
        previewSpinner.classList.add('hidden');
        downloadSpinner.classList.add('hidden');
    }
}

async function previewData(page, usePost = false) {
    const method = usePost ? 'POST' : 'GET';
    const data = await fetchData('/preview', page, method);
    if (!data) return;

    currentPage = page < 1 ? 1 : page;
    const dataTable = document.getElementById('data-table');
    const tbody = document.getElementById('data-body');
    const pagination = document.getElementById('pagination');
    const pageInfo = document.getElementById('page-info');
    const visitCountHeader = document.querySelector('.visit-count-header');

    dataTable.classList.remove('hidden');
    tbody.innerHTML = '';
    pagination.classList.remove('hidden');

    const dataType = document.getElementById('data_type').value;
    const hideVisitCount = ['cookies', 'logins', 'autofill'].includes(dataType);
    visitCountHeader.style.display = hideVisitCount ? 'none' : '';

    data.data.forEach((row, index) => {
        const rowIndex = (currentPage - 1) * itemsPerPage + index + 1;
        const tr = document.createElement('tr');
        const urlDisplay = row['URL'] === "Không có URL" ? row['URL'] : `<a href="${row['URL']}" target="_blank" class="text-blue-600 hover:underline">${row['URL']}</a>`;
        tr.innerHTML = `
            <td class="px-6 py-4">${rowIndex}</td>
            <td class="px-6 py-4">${row['Loại']}</td>
            <td class="px-6 py-4 truncate max-w-xs">${row['Tiêu đề']}</td>
            <td class="px-6 py-4 truncate max-w-md">${urlDisplay}</td>
            <td class="px-6 py-4 visit-count-cell" style="display: ${hideVisitCount ? 'none' : ''}">${row['Số lần truy cập'] || '-'}</td>
            <td class="px-6 py-4">${row['Thời gian'] || '-'}</td>
        `;
        tbody.appendChild(tr);
    });

    const totalPages = data.total_pages;
    pageInfo.textContent = `Trang ${currentPage} / ${totalPages}`;
    document.getElementById('prev-page').disabled = currentPage === 1;
    document.getElementById('next-page').disabled = currentPage === totalPages;
}

async function downloadData() {
    await fetchData('/download', 1, 'POST');
}

function updateDataTypeWarning() {
    const browser = document.getElementById('browser');
    const dataType = document.getElementById('data_type');
    const warning = document.getElementById('data_type_warning');
    warning.classList.add('hidden');

    if (browser.value === 'firefox') {
        if (dataType.value === 'downloads') {
            warning.textContent = "Lưu ý: Firefox có thể không hỗ trợ dữ liệu tải xuống trong một số phiên bản.";
            warning.classList.remove('hidden');
        } else if (dataType.value === 'autofill') {
            warning.textContent = "Lưu ý: Dữ liệu tự động điền trên Firefox có thể không đầy đủ.";
            warning.classList.remove('hidden');
        }
    } else {
        if (dataType.value === 'autofill') {
            warning.textContent = "Lưu ý: Dữ liệu tự động điền có thể không có nếu bạn chưa sử dụng tính năng này.";
            warning.classList.remove('hidden');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const browserSelect = document.getElementById('browser');
    const dataTypeSelect = document.getElementById('data_type');
    const previewBtn = document.getElementById('preview-btn');
    const downloadBtn = document.getElementById('download-btn');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const form = document.getElementById('browser-form');

    browserSelect.addEventListener('change', updateDataTypeWarning);
    dataTypeSelect.addEventListener('change', updateDataTypeWarning);

    form.addEventListener('submit', (event) => {
        event.preventDefault();
    });

    previewBtn.addEventListener('click', () => previewData(1, true));
    downloadBtn.addEventListener('click', downloadData);
    prevPageBtn.addEventListener('click', () => previewData(currentPage - 1));
    nextPageBtn.addEventListener('click', () => previewData(currentPage + 1));

    updateDataTypeWarning();

    const style = document.createElement('style');
    style.innerHTML = `
        .rounded-toast {
            border-radius: 12px !important;
            padding: 12px 16px !important;
            font-size: 16px !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
    `;
    document.head.appendChild(style);
});