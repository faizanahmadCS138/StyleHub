if (!window.moneyFormatter) {
    window.moneyFormatter = new Intl.NumberFormat('en-PK', {
        style: 'currency',
        currency: 'PKR',
        maximumFractionDigits: 0,
    });
}

function formatPrice(value) {
    const number = Number(value || 0);
    return window.moneyFormatter.format(number).replace('PKR', 'PKR ');
}

// Render Side Drawer Items
function renderDrawerItems(container, items) {
    if (!container) return;
    if (!items || !items.length) {
        container.innerHTML = '<div class="cart-drawer-empty">Your basket is empty.</div>';
        return;
    }

    container.innerHTML = items.map((item) => `
        <div class="cart-drawer-item" data-variant-id="${item.variant_id}">
            <img class="cart-drawer-item-image" src="${item.image || ''}" alt="${item.product_name || ''}">
            <div class="cart-drawer-item-content">
                <a class="cart-drawer-item-name" href="${item.product_url || '#'}">${item.product_name || ''}</a>
                <p class="cart-drawer-item-meta">${[item.color, item.size].filter(Boolean).join(' / ')}</p>
                <p class="cart-drawer-item-quantity">${item.quantity}x</p>
            </div>
            <div style="text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 8px;">
                <button type="button" class="cart-drawer-item-remove" data-remove-item="${item.variant_id}">
                    <i class="fa-regular fa-trash-can"></i>
                </button>
                <div class="cart-drawer-item-price">${formatPrice(item.subtotal || 0)}</div>
            </div>
        </div>
    `).join('');
}

// Render Main Cart Page Items
function renderPageItems(container, items) {
    if (!container) return;
    if (!items || !items.length) {
        container.innerHTML = '<div style="padding: 40px 0; font-size: 16px;">Your shopping basket is currently empty.</div>';
        return;
    }

    container.innerHTML = items.map((item) => `
        <div class="cart-item-row" data-variant-id="${item.variant_id}">
            <div class="cart-item-info">
                <img class="cart-item-img" src="${item.image || ''}" alt="${item.product_name || ''}">
                <div class="cart-item-details">
                    <a class="cart-item-name" href="${item.product_url || '#'}">${item.product_name || ''}</a>
                    <div class="cart-item-unit-price">${formatPrice(item.unit_price || 0)}</div>
                    ${item.color ? `<p class="cart-item-meta-text">Color: ${item.color}</p>` : ''}
                    ${item.size ? `<p class="cart-item-meta-text">Size: ${item.size}</p>` : ''}
                </div>
            </div>

            <div class="cart-item-qty-col">
                <div class="qty-control-box">
                    <button type="button" class="qty-btn" data-qty-change="-1" data-variant-id="${item.variant_id}">-</button>
                    <span class="qty-val">${item.quantity}</span>
                    <button type="button" class="qty-btn" data-qty-change="1" data-variant-id="${item.variant_id}">+</button>
                </div>
                <button type="button" class="cart-item-remove-btn" data-remove-item="${item.variant_id}">
                    <i class="fa-regular fa-trash-can"></i>
                </button>
            </div>

            <div class="cart-item-total-col">
                ${formatPrice(item.subtotal || 0)}
            </div>
        </div>
    `).join('');
}