/* Catalog Grid Controls & Color Swatch Switcher */
document.addEventListener('DOMContentLoaded', function () {
    const productGrid = document.getElementById('productGrid');
    const btnGrid3 = document.getElementById('btnGrid3');
    const btnGrid4 = document.getElementById('btnGrid4');
    const btnGrid5 = document.getElementById('btnGrid5');

    // ── Grid Column Toggles ──────────────────────────────────
    if (productGrid) {
        if (btnGrid3) {
            btnGrid3.addEventListener('click', function () {
                productGrid.className = 'product-grid grid-cols-3';
                setActiveBtn(btnGrid3);
            });
        }

        if (btnGrid4) {
            btnGrid4.addEventListener('click', function () {
                productGrid.className = 'product-grid grid-cols-4';
                setActiveBtn(btnGrid4);
            });
        }

        if (btnGrid5) {
            btnGrid5.addEventListener('click', function () {
                productGrid.className = 'product-grid grid-cols-5';
                setActiveBtn(btnGrid5);
            });
        }
    }

    function setActiveBtn(activeBtn) {
        [btnGrid3, btnGrid4, btnGrid5].forEach(btn => {
            if (btn) btn.classList.remove('active');
        });
        if (activeBtn) activeBtn.classList.add('active');
    }

    // ── Color Swatches Click Switcher ────────────────
    const colorDots = document.querySelectorAll('.color-swatch-dot');
    colorDots.forEach(dot => {
        dot.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();

            const productId = this.getAttribute('data-product-id');
            const imgEl = document.getElementById('product-img-' + productId);

            // Toggle active swatch dot state
            const parentSwatches = this.closest('.color-swatches-list');
            if (parentSwatches) {
                parentSwatches.querySelectorAll('.color-swatch-dot').forEach(d => d.classList.remove('active'));
            }
            this.classList.add('active');

            // Swap image to specific color image if available, else toggle secondary
            const targetImageUrl = this.dataset.imageUrl;
            const selectedColorName = this.dataset.color;
            if (imgEl && targetImageUrl) {
                imgEl.src = targetImageUrl;
            } else if (imgEl && imgEl.dataset.secondary) {
                if (imgEl.src === imgEl.dataset.primary) {
                    imgEl.src = imgEl.dataset.secondary;
                } else {
                    imgEl.src = imgEl.dataset.primary;
                }
            }

            // Update card links to include ?color=
            if (selectedColorName) {
                const productCard = this.closest('.product-card');
                if (productCard) {
                    const cardLinks = productCard.querySelectorAll('a.product-card-image-wrap, a.product-card-title, a[href*="/products/"]');
                    cardLinks.forEach(link => {
                        try {
                            const url = new URL(link.href, window.location.origin);
                            url.searchParams.set('color', selectedColorName);
                            link.href = url.pathname + url.search;
                        } catch (err) {}
                    });
                }
            }
        });
    });

    // Sync initial card links for active swatch dots
    document.querySelectorAll('.product-card').forEach(card => {
        const activeDot = card.querySelector('.color-swatch-dot.active');
        if (activeDot && activeDot.dataset.color) {
            const cardLinks = card.querySelectorAll('a.product-card-image-wrap, a.product-card-title, a[href*="/products/"]');
            cardLinks.forEach(link => {
                try {
                    const url = new URL(link.href, window.location.origin);
                    url.searchParams.set('color', activeDot.dataset.color);
                    link.href = url.pathname + url.search;
                } catch (err) {}
            });
        }
    });
});
