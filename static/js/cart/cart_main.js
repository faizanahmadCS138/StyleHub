(function () {
    const cartApiUrl = document.body?.dataset.cartApiUrl;
    const overlay = document.getElementById('cartDrawerOverlay');
    const openBtn = document.getElementById('cartTriggerBtn');
    const closeBtn = document.getElementById('cartDrawerCloseBtn');
    const drawerItemsContainer = document.getElementById('cartDrawerItems');
    const pageItemsContainer = document.getElementById('cartPageItems');
    const totalEl = document.getElementById('cartDrawerTotal');
    const pageTotalEl = document.getElementById('cartPageTotal');

    function openDrawer() {
        if (!overlay) return;
        overlay.classList.add('open');
        overlay.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    }

    function closeDrawer() {
        if (!overlay) return;
        if (document.activeElement && overlay.contains(document.activeElement)) {
            document.activeElement.blur();
        }
        overlay.classList.remove('open');
        overlay.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        if (openBtn) openBtn.focus();
    }

    function updateUI(cart) {
        if (!cart) return;

        const items = cart.items || [];
        const totalItems = cart.summary?.total_items ?? cart.cart_count ?? items.reduce((c, i) => c + Number(i.quantity || 0), 0);
        const totalSubtotal = cart.summary?.subtotal ?? cart.subtotal ?? items.reduce((s, i) => s + Number(i.subtotal || 0), 0);

        const badgeEl = document.querySelector('.cart-badge');
        if (badgeEl) {
            badgeEl.textContent = String(totalItems);
            badgeEl.style.display = totalItems > 0 ? 'flex' : 'none';
        }

        const formattedTotal = typeof formatPrice === 'function' ? formatPrice(totalSubtotal) : `PKR ${totalSubtotal}`;
        if (totalEl) totalEl.textContent = formattedTotal;
        if (pageTotalEl) pageTotalEl.textContent = formattedTotal;

        if (typeof renderDrawerItems === 'function' && drawerItemsContainer) {
            renderDrawerItems(drawerItemsContainer, items);
        }
        if (typeof renderPageItems === 'function' && pageItemsContainer) {
            renderPageItems(pageItemsContainer, items);
        }
    }

    async function loadCart() {
        if (typeof fetchCart !== 'function') {
            console.warn("fetchCart function missing from cart-api.js");
            return;
        }
        try {
            const cart = await fetchCart(cartApiUrl);
            updateUI(cart);
            return cart;
        } catch (e) {
            console.error("Error loading cart:", e);
        }
    }

    // Attach to window immediately so other scripts can access it regardless of DOM state
    window.StyleHubCart = {
        open: openDrawer,
        close: closeDrawer,
        refresh: loadCart,
        render: updateUI,
    };

    // Event Listeners
    if (openBtn) {
        openBtn.addEventListener('click', function (event) {
            event.preventDefault();
            openDrawer();
            loadCart();
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', closeDrawer);
    }

    if (overlay) {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeDrawer();
        });
    }

    document.addEventListener('DOMContentLoaded', loadCart);
})();