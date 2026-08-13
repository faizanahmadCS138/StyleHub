// CSRF Token Helper
function getCsrfToken() {
    const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    if (match) {
        return decodeURIComponent(match[1]);
    }
    const hiddenToken = document.querySelector('#csrfTokenForm input[name="csrfmiddlewaretoken"]');
    return hiddenToken ? hiddenToken.value : '';
}

// Payload Normalizer
function normalizeCartPayload(data) {
    if (!data) return { items: [], summary: { total_items: 0, subtotal: 0 } };
    if (data.cart) return data.cart;
    return {
        items: data.items || [],
        summary: data.summary || { total_items: 0, subtotal: 0 },
    };
}

// Fetch Cart Data
async function fetchCart(apiUrl) {
    if (!apiUrl) return null;
    try {
        const response = await fetch(apiUrl, { credentials: 'same-origin' });
        const data = await response.json();
        return normalizeCartPayload(data);
    } catch (error) {
        console.error('Cart load failed', error);
        return null;
    }
}

// Update Item Quantity
async function updateCartItemQty(apiUrl, variantId, quantity, overrideQuantity = true) {
    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken(),
            },
            credentials: 'same-origin',
            body: JSON.stringify({ variant_id: variantId, quantity, override_quantity: overrideQuantity }),
        });
        const data = await response.json();
        return normalizeCartPayload(data);
    } catch (error) {
        console.error('Cart update failed', error);
        return null;
    }
}

// Remove Item
async function removeCartItem(apiUrl, variantId) {
    try {
        const response = await fetch(apiUrl, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken(),
            },
            credentials: 'same-origin',
            body: JSON.stringify({ variant_id: variantId }),
        });
        const data = await response.json();
        return normalizeCartPayload(data);
    } catch (error) {
        console.error('Cart remove failed', error);
        return null;
    }
}