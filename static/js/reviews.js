document.addEventListener('DOMContentLoaded', () => {

    const writeReviewBtn = document.getElementById('writeReviewBtn');
    const reviewModal = document.getElementById('reviewModal');
    const reviewModalClose = document.getElementById('reviewModalClose');
    const reviewCancelBtn = document.getElementById('reviewCancelBtn');

    const reviewForm = document.getElementById('reviewForm');

    const starInputs = document.querySelectorAll('.star-input');
    const ratingInput = document.getElementById('ratingInput');

    const reviewModalTitle = document.getElementById('reviewModalTitle');
    const reviewComment = document.getElementById('reviewComment');

    let currentProductId = null;


    /* =========================================
       OPEN REVIEW MODAL
    ========================================= */

    if (writeReviewBtn) {

        writeReviewBtn.addEventListener('click', () => {

            /*
             * Check authentication.
             *
             * IS_AUTHENTICATED comes from the Django template.
             */
            if (!IS_AUTHENTICATED) {

                if (typeof showLoginPrompt === 'function') {
                    showLoginPrompt();
                } else {
                    alert('Sign up or log in to write a review.');
                }

                return;
            }


            currentProductId =
                writeReviewBtn.dataset.productId;


            const productName =
                writeReviewBtn.dataset.productName;


            /*
             * Change modal title
             */

            if (reviewModalTitle) {

                reviewModalTitle.textContent =
                    `Write a Review for ${productName}`;

            }


            /*
             * Clear old form data
             */

            resetReviewForm();


            /*
             * Open modal
             */

            if (reviewModal) {

                reviewModal.classList.add('is-open');

                document.body.style.overflow = 'hidden';

            }

        });

    }


    /* =========================================
       CLOSE MODAL
    ========================================= */

    function closeReviewModal() {

        if (!reviewModal) {
            return;
        }

        reviewModal.classList.remove('is-open');

        document.body.style.overflow = '';

    }


    if (reviewModalClose) {

        reviewModalClose.addEventListener(
            'click',
            closeReviewModal
        );

    }


    if (reviewCancelBtn) {

        reviewCancelBtn.addEventListener(
            'click',
            closeReviewModal
        );

    }


    /*
     * Close when clicking outside modal
     */

    if (reviewModal) {

        reviewModal.addEventListener('click', (event) => {

            if (event.target === reviewModal) {

                closeReviewModal();

            }

        });

    }


    /*
     * Close with Escape key
     */

    document.addEventListener('keydown', (event) => {

        if (
            event.key === 'Escape' &&
            reviewModal &&
            reviewModal.classList.contains('is-open')
        ) {

            closeReviewModal();

        }

    });


    /* =========================================
       STAR RATING
    ========================================= */

    starInputs.forEach((star) => {

        star.addEventListener('click', () => {

            const value =
                parseInt(star.dataset.value, 10);


            /*
             * Store selected rating
             */

            ratingInput.value = value;


            /*
             * Highlight selected stars
             */

            starInputs.forEach((s) => {

                const starValue =
                    parseInt(s.dataset.value, 10);


                if (starValue <= value) {

                    s.classList.add('selected');

                } else {

                    s.classList.remove('selected');

                }

            });

        });

    });


    /* =========================================
       RESET FORM
    ========================================= */

    function resetReviewForm() {
    // Default rating = 5 stars
    ratingInput.value = 5;

    starInputs.forEach(star => {
        star.classList.toggle(
            'selected',
            parseInt(star.dataset.value, 10) <= 5
        );
    });

    document.getElementById('reviewComment').value = '';
}


    /* =========================================
       CSRF COOKIE
    ========================================= */

    function getCookie(name) {

        let cookieValue = null;


        if (document.cookie && document.cookie !== '') {

            const cookies =
                document.cookie.split(';');


            for (let cookie of cookies) {

                cookie = cookie.trim();


                if (
                    cookie.substring(
                        0,
                        name.length + 1
                    ) === `${name}=`
                ) {

                    cookieValue =
                        decodeURIComponent(
                            cookie.substring(
                                name.length + 1
                            )
                        );

                    break;

                }

            }

        }


        return cookieValue;

    }


    /* =========================================
       SUBMIT REVIEW
    ========================================= */

    if (reviewForm) {

        reviewForm.addEventListener(
            'submit',
            async (event) => {

                event.preventDefault();


                /* -------------------------------
                   Validate rating
                -------------------------------- */

                const selectedRating =
                    parseInt(
                        ratingInput.value,
                        10
                    );


                if (!selectedRating) {

                    showToast(
                        'Please select a star rating.',
                        'error'
                    );

                    return;

                }


                /* -------------------------------
                   Product ID
                -------------------------------- */

                if (!currentProductId) {

                    showToast(
                        'Product could not be identified.',
                        'error'
                    );

                    return;

                }


                /* -------------------------------
                   Create form data
                -------------------------------- */

                const formData =
                    new FormData(reviewForm);


                /*
                 * Disable submit button
                 */

                const submitButton =
                    reviewForm.querySelector(
                        '.btn-submit-review'
                    );


                if (submitButton) {

                    submitButton.disabled = true;

                    submitButton.textContent =
                        'Submitting...';

                }


                try {

                    /* ---------------------------
                       Send AJAX request
                    ---------------------------- */

                    const response = await fetch(
                        `/reviews/product/${currentProductId}/add/`,
                        {
                            method: 'POST',

                            headers: {
                                'X-CSRFToken':
                                    getCookie('csrftoken'),

                                'X-Requested-With':
                                    'XMLHttpRequest'
                            },

                            body: formData
                        }
                    );


                    const data =
                        await response.json();


                    /* ---------------------------
                       NOT LOGGED IN
                    ---------------------------- */

                    if (response.status === 401) {

                        closeReviewModal();


                        if (
                            typeof showLoginPrompt ===
                            'function'
                        ) {

                            showLoginPrompt();

                        } else {

                            alert(data.message);

                        }

                        return;

                    }


                    /* ---------------------------
                       BACKEND ERROR
                    ---------------------------- */

                    if (
                        !response.ok ||
                        !data.success
                    ) {

                        showToast(
                            data.message ||
                            'Something went wrong.',
                            'error'
                        );

                        return;

                    }


                    /* ---------------------------
                       SUCCESS
                    ---------------------------- */

                    closeReviewModal();


                    showToast(
                        'Review submitted!',
                        'success'
                    );


                    /* ---------------------------
                       Remove empty state
                    ---------------------------- */

                    const emptyState =
                        document.getElementById(
                            'reviewsEmptyState'
                        );


                    if (emptyState) {

                        emptyState.remove();

                    }


                    /* ---------------------------
                       Add new review
                    ---------------------------- */

                    const reviewsList =
                        document.getElementById(
                            'reviewsList'
                        );


                    if (
                        reviewsList &&
                        data.review_html
                    ) {

                        reviewsList.insertAdjacentHTML(
                            'afterbegin',
                            data.review_html
                        );

                    }


                    /* ---------------------------
                       Update average rating
                    ---------------------------- */

                    const ratingNumber =
                        document.querySelector(
                            '.reviews-summary-number'
                        );


                    if (
                        ratingNumber &&
                        data.avg_rating !== undefined
                    ) {

                        ratingNumber.textContent =
                            Number(
                                data.avg_rating
                            ).toFixed(1);

                    }


                    /* ---------------------------
                       Update review count
                    ---------------------------- */

                    const reviewCount =
                        document.querySelector(
                            '.reviews-summary-count'
                        );


                    if (
                        reviewCount &&
                        data.review_count !== undefined
                    ) {

                        const count =
                            data.review_count;


                        reviewCount.textContent =
                            `(${count} review${count === 1 ? '' : 's'})`;

                    }


                    /* ---------------------------
                       Update stars
                    ---------------------------- */

                    updateSummaryStars(
                        data.avg_rating
                    );


                    /* ---------------------------
                       Disable Write Review button
                    ---------------------------- */

                    if (writeReviewBtn) {

                        writeReviewBtn.disabled = true;

                        writeReviewBtn.innerHTML =
                            '<i class="fa-solid fa-check"></i> You reviewed this product';

                    }


                    /* ---------------------------
                       Reset form
                    ---------------------------- */

                    resetReviewForm();


                } catch (error) {

                    console.error(
                        'Review submit error:',
                        error
                    );


                    showToast(
                        'Something went wrong. Please try again.',
                        'error'
                    );


                } finally {

                    if (submitButton) {

                        submitButton.disabled = false;

                        submitButton.textContent =
                            'Submit Review';

                    }

                }

            }
        );

    }


    /* =========================================
       UPDATE SUMMARY STARS
    ========================================= */

    function updateSummaryStars(avgRating) {

        const stars =
            document.querySelectorAll(
                '.reviews-summary-stars i'
            );


        const rating =
            Number(avgRating) || 0;


        stars.forEach((star, index) => {

            const starNumber = index + 1;


            if (starNumber <= rating) {

                star.classList.add('filled');

            } else {

                star.classList.remove('filled');

            }

        });

    }


    /* =========================================
       TOAST
    ========================================= */

    function showToast(
        message,
        type = 'error'
    ) {

        const container =
            document.getElementById(
                'toastContainer'
            );


        if (!container) {

            alert(message);

            return;

        }


        const toast =
            document.createElement('div');


        toast.className =
            `toast toast-${type}`;


        toast.innerHTML = `
            <i class="fa-solid ${
                type === 'error'
                    ? 'fa-triangle-exclamation'
                    : 'fa-circle-check'
            }"></i>

            <span>${message}</span>

            <button
                type="button"
                class="toast-close"
            >
                &times;
            </button>
        `;


        container.appendChild(toast);


        const closeButton =
            toast.querySelector(
                '.toast-close'
            );


        if (closeButton) {

            closeButton.addEventListener(
                'click',
                () => toast.remove()
            );

        }


        setTimeout(() => {

            if (toast.parentNode) {

                toast.remove();

            }

        }, 5000);

    }

});