// ============================================================
// VIRTUAL-TRYON.JS — "Try On Yourself" modal + AJAX generation
// ============================================================

document.addEventListener('DOMContentLoaded', () => {

    const tryOnBtn = document.getElementById('tryOnBtn');
    const modal = document.getElementById('tryonModal');
    const modalClose = document.getElementById('tryonModalClose');
    const modalTitle = document.getElementById('tryonModalTitle');

    const uploadState = document.getElementById('tryonUploadState');
    const loadingState = document.getElementById('tryonLoadingState');
    const resultState = document.getElementById('tryonResultState');

    const fileInput = document.getElementById('tryonFileInput');
    const dropzone = document.getElementById('tryonDropzone');
    const dropzoneEmpty = document.getElementById('tryonDropzoneEmpty');
    const previewWrap = document.getElementById('tryonPreviewWrap');
    const previewImg = document.getElementById('tryonPreviewImg');
    const removeBtn = document.getElementById('tryonRemoveBtn');
    const errorText = document.getElementById('tryonErrorText');
    const generateBtn = document.getElementById('tryonGenerateBtn');

    const resultImg = document.getElementById('tryonResultImg');
    const tryAgainBtn = document.getElementById('tryonTryAgainBtn');
    const closeResultBtn = document.getElementById('tryonCloseResultBtn');

    if (!tryOnBtn || !modal) return;

    let currentProductId = null;
    let selectedFile = null;

    const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png'];
    const MAX_SIZE_BYTES = 8 * 1024 * 1024; // 8MB, matches backend TryOnUploadForm

    /* OPEN MODAL */
    tryOnBtn.addEventListener('click', () => {
        if (!IS_AUTHENTICATED) {
            if (typeof showLoginPrompt === 'function') {
                showLoginPrompt();
            } else {
                alert('Please login to use Virtual Try-On.');
            }
            return;
        }

        currentProductId = tryOnBtn.dataset.productId;
        const productName = tryOnBtn.dataset.productName;

        if (modalTitle) {
            modalTitle.textContent = productName ? `Try On: ${productName}` : 'Try On This Product';
        }

        resetToUploadState();
        openModal();
    });

    function openModal() {
        modal.classList.add('is-open');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        modal.classList.remove('is-open');
        document.body.style.overflow = '';
    }

    if (modalClose) modalClose.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('is-open')) {
            closeModal();
        }
    });

    /* UPLOAD / PREVIEW */
    if (dropzone) {
        dropzone.addEventListener('click', () => {
            fileInput.click();
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', () => {
            const file = fileInput.files[0];
            if (!file) return;
            handleSelectedFile(file);
        });
    }

    function handleSelectedFile(file) {
        clearError();

        if (!ALLOWED_TYPES.includes(file.type)) {
            showError('Please upload a JPG, JPEG, or PNG image.');
            fileInput.value = '';
            return;
        }

        if (file.size > MAX_SIZE_BYTES) {
            showError('The uploaded image is too large. Max size is 8MB.');
            fileInput.value = '';
            return;
        }

        selectedFile = file;

        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            dropzoneEmpty.style.display = 'none';
            previewWrap.style.display = 'block';
        };
        reader.readAsDataURL(file);

        generateBtn.disabled = false;
    }

    if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            clearSelectedFile();
        });
    }

    function clearSelectedFile() {
        selectedFile = null;
        fileInput.value = '';
        previewImg.src = '';
        previewWrap.style.display = 'none';
        dropzoneEmpty.style.display = 'flex';
        generateBtn.disabled = true;
        clearError();
    }

    function showError(message) {
        if (errorText) errorText.textContent = message;
    }

    function clearError() {
        if (errorText) errorText.textContent = '';
    }

    /* GENERATE TRY-ON */
    if (generateBtn) {
        generateBtn.addEventListener('click', async () => {
            if (!selectedFile) {
                showError('Please upload a photo first.');
                return;
            }

            if (!currentProductId) {
                showError('Product could not be identified.');
                return;
            }

            clearError();
            showLoadingState();

            const formData = new FormData();
            formData.append('product_id', currentProductId);
            formData.append('user_image', selectedFile);

            try {
                const response = await fetch('/virtual-tryon/generate/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    body: formData,
                });

                const data = await response.json();

                if (response.status === 401 || data.login_required) {
                    closeModal();
                    if (typeof showLoginPrompt === 'function') {
                        showLoginPrompt();
                    } else {
                        alert('Please login to use Virtual Try-On.');
                    }
                    return;
                }

                if (!response.ok || !data.success) {
                    showToast(data.error || 'Unable to generate your try-on right now. Please try again.', 'error');
                    showUploadState();
                    return;
                }

                resultImg.src = data.image_url;
                showResultState();

            } catch (err) {
                console.error('Virtual try-on error:', err);
                showToast('Unable to generate your try-on right now. Please try again.', 'error');
                showUploadState();
            }
        });
    }

    /* TRY AGAIN / CLOSE RESULT */
    if (tryAgainBtn) {
        tryAgainBtn.addEventListener('click', () => {
            resetToUploadState();
            showUploadState();
        });
    }

    if (closeResultBtn) {
        closeResultBtn.addEventListener('click', closeModal);
    }

    /* STATE HELPERS */
    function resetToUploadState() {
        clearSelectedFile();
        resultImg.src = '';
    }

    function showUploadState() {
        uploadState.style.display = 'flex';
        loadingState.style.display = 'none';
        resultState.style.display = 'none';
        generateBtn.disabled = !selectedFile;
        generateBtn.textContent = 'Generate Try-On';
    }

    function showLoadingState() {
        uploadState.style.display = 'none';
        loadingState.style.display = 'flex';
        resultState.style.display = 'none';
        generateBtn.disabled = true;
    }

    function showResultState() {
        uploadState.style.display = 'none';
        loadingState.style.display = 'none';
        resultState.style.display = 'flex';
    }

    /* CSRF COOKIE */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.substring(0, name.length + 1) === `${name}=`) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /* TOAST (mirrors reviews.js pattern) */
    function showToast(message, type = 'error') {
        const container = document.getElementById('toastContainer');
        if (!container) {
            alert(message);
            return;
        }

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fa-solid ${type === 'error' ? 'fa-triangle-exclamation' : 'fa-circle-check'}"></i>
            <span>${message}</span>
            <button type="button" class="toast-close">&times;</button>
        `;

        container.appendChild(toast);

        const closeButton = toast.querySelector('.toast-close');
        if (closeButton) {
            closeButton.addEventListener('click', () => toast.remove());
        }

        setTimeout(() => {
            if (toast.parentNode) toast.remove();
        }, 5000);
    }

});