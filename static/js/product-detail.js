/* Outfitters Product Detail Page JavaScript */
document.addEventListener('DOMContentLoaded', function () {

    let selectedColor = null;
    let selectedSize = null;
    const variantsData = window.VARIANTS_DATA || [];

    const colorDots = document.querySelectorAll('.pdp-color-dot');
    const sizeChips = document.querySelectorAll('.pdp-size-chip');
    const colorNameSpan = document.getElementById('selectedColorName');
    const addToBagBtn = document.getElementById('addToBagBtn');

    // FIX 1: Provide a fallback URL if dataset property is missing from body
    const cartApiUrl = document.body?.dataset.cartApiUrl || '/cart/add/';

    const formatPrice = new Intl.NumberFormat('en-PK', {
        style: 'currency',
        currency: 'PKR',
        maximumFractionDigits: 0,
    });

    // ── 1. Color Selection ───────────────────────────────────
    if (colorDots.length > 0) {
        selectColor(colorDots[0]);
    }

    colorDots.forEach(dot => {
        dot.addEventListener('click', function () {
            selectColor(this);
        });
    });

    function selectColor(dot) {
        colorDots.forEach(d => d.classList.remove('active'));
        dot.classList.add('active');
        selectedColor = dot.dataset.color;
        if (colorNameSpan) {
            colorNameSpan.textContent = selectedColor.charAt(0).toUpperCase() + selectedColor.slice(1);
        }

        updateSizeAvailability();
        checkSelectedVariant();
    }

    // ── 2. Size Selection ────────────────────────────────────
    sizeChips.forEach(chip => {
        chip.addEventListener('click', function () {
            if (this.classList.contains('out-of-stock')) return;

            sizeChips.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            selectedSize = this.dataset.size;

            checkSelectedVariant();
        });
    });

    function updateSizeAvailability() {
        sizeChips.forEach(chip => {
            const sizeName = chip.dataset.size;
            const matchingVar = variantsData.find(v =>
                (!selectedColor || v.color?.toLowerCase() === selectedColor.toLowerCase()) &&
                v.size?.toLowerCase() === sizeName.toLowerCase()
            );

            if (matchingVar && matchingVar.stock > 0) {
                chip.classList.remove('out-of-stock');
            } else {
                chip.classList.add('out-of-stock');
                if (chip.classList.contains('active')) {
                    chip.classList.remove('active');
                    selectedSize = null;
                }
            }
        });
    }

    function checkSelectedVariant() {
        if (!selectedColor && colorDots.length > 0) return;

        const matchedVariant = variantsData.find(v =>
            (!selectedColor || v.color?.toLowerCase() === selectedColor.toLowerCase()) &&
            (!selectedSize || v.size?.toLowerCase() === selectedSize.toLowerCase())
        );

        if (addToBagBtn) {
            if (selectedSize && matchedVariant && matchedVariant.stock > 0) {
                addToBagBtn.disabled = false;
                addToBagBtn.style.opacity = '1';
            } else if (selectedSize && matchedVariant && matchedVariant.stock <= 0) {
                addToBagBtn.disabled = true;
                addToBagBtn.style.opacity = '0.5';
            }
        }
    }

    async function addSelectedVariantToCart(e) {
        if (e) e.preventDefault(); // FIX 2: Prevent form submission if inside a form

        const matchedVariant = variantsData.find(v =>
            (!selectedColor || v.color?.toLowerCase() === selectedColor.toLowerCase()) &&
            (!selectedSize || v.size?.toLowerCase() === selectedSize.toLowerCase())
        );

        if (!selectedSize) {
            alert("Please select a size first!");
            return;
        }

        if (!matchedVariant) {
            alert("Selected variant is unavailable.");
            return;
        }

        // FIX 3: Robust ID matching (handles v.id or v.variant_id)
        const targetVariantId = matchedVariant.id || matchedVariant.variant_id;

        if (!targetVariantId) {
            console.error("Variant found but contains no ID field:", matchedVariant);
            alert("Invalid product variant configuration.");
            return;
        }

        const payload = {
            variant_id: targetVariantId,
            quantity: 1,
        };

        console.log("Sending payload to:", cartApiUrl, payload); // Debug log

        try {
            const response = await fetch(cartApiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCsrfToken(),
                },
                credentials: 'same-origin',
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (!response.ok || data.ok === false) {
                throw new Error(data.error || 'Unable to add item to cart.');
            }

            if (window.StyleHubCart) {
                const normalizedPayload = typeof normalizeCartPayload === 'function' ? normalizeCartPayload(data) : data;
                window.StyleHubCart.render(normalizedPayload);
                window.StyleHubCart.refresh();
            }

        } catch (error) {
            console.error("Cart Error:", error);
            alert(error.message || 'Could not add the selected item to the cart.');
        } finally {
            if (addToBagBtn) {
                addToBagBtn.disabled = false;
            }
        }
    }

    function getCsrfToken() {
        const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        if (match) {
            return decodeURIComponent(match[1]);
        }

        const hiddenToken = document.querySelector('#csrfTokenForm input[name="csrfmiddlewaretoken"]') ||
            document.querySelector('input[name="csrfmiddlewaretoken"]');
        return hiddenToken ? hiddenToken.value : '';
    }

    // ── 3. Accordions (+ / - Toggle) ─────────────────────────
    const accordionHeaders = document.querySelectorAll('.pdp-accordion-header');
    accordionHeaders.forEach(header => {
        header.addEventListener('click', function () {
            const item = this.parentElement;
            const icon = this.querySelector('.pdp-accordion-icon');
            const isActive = item.classList.contains('active');

            item.classList.toggle('active');
            if (icon) {
                icon.textContent = isActive ? '+' : '−';
            }
        });
    });

    if (addToBagBtn) {
        addToBagBtn.addEventListener('click', function (e) {
            addSelectedVariantToCart(e);
        });
    }

});