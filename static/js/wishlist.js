// ============================================================
// WISHLIST.JS — Instagram-style heart toggle + auth gating
// ============================================================

document.addEventListener('DOMContentLoaded', () => {

  // ------------------------------------------------------------
  // 1. HEADER WISHLIST ICON — intercept click for anonymous users
  // ------------------------------------------------------------
  const wishlistTrigger = document.getElementById('wishlistTriggerBtn');
  if (wishlistTrigger) {
    wishlistTrigger.addEventListener('click', (e) => {
      if (!IS_AUTHENTICATED) {
        e.preventDefault();
        showLoginPrompt();
      }
      // if authenticated, let the <a> navigate normally to wishlist:list
    });
  }

  // ------------------------------------------------------------
  // 2. PRODUCT CARD HEARTS — event delegation (works for hearts
  //    added dynamically too, e.g. via AJAX product grids)
  // ------------------------------------------------------------
  document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.wishlist-heart');
    if (!btn) return;

    e.preventDefault();

    if (!IS_AUTHENTICATED) {
      showLoginPrompt();
      return;
    }

    if (btn.dataset.loading === 'true') return; // prevent double-click spam
    btn.dataset.loading = 'true';

    const productId = btn.dataset.productId;

    try {
      const res = await fetch(`/wishlist/${productId}/toggle/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'Content-Type': 'application/json',
        },
      });

      if (res.status === 401 || res.status === 403) {
        showLoginPrompt();
        return;
      }

      if (!res.ok) throw new Error(`Wishlist toggle failed: ${res.status}`);

      const data = await res.json();

      // Update this heart's visual state
      btn.classList.toggle('wishlist-heart--active', data.wishlisted);
      btn.classList.add('animating');
      setTimeout(() => btn.classList.remove('animating'), 300);

      // If we're on the wishlist page itself and item was removed, drop the card
      if (!data.wishlisted && btn.closest('.wishlist-card')) {
        const card = btn.closest('.wishlist-card');
        card.classList.add('removing');
        setTimeout(() => {
          card.remove();
          checkEmptyWishlist();
        }, 250);
      }

      // Sync ALL hearts for this same product on the page
      // (e.g. same product shown in a "related products" row too)
      document.querySelectorAll(`.wishlist-heart[data-product-id="${productId}"]`).forEach(el => {
        el.classList.toggle('wishlist-heart--active', data.wishlisted);
      });

      updateHeaderBadge(data.wishlist_count);

    } catch (err) {
      console.error('Wishlist error:', err);
    } finally {
      btn.dataset.loading = 'false';
    }
  });

  // ------------------------------------------------------------
  // 3. MODAL CLOSE HANDLERS
  // ------------------------------------------------------------
  const modal = document.getElementById('wishlist-login-modal');
  if (modal) {
    // close on backdrop click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeLoginPrompt();
    });
    // close on Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal.classList.contains('is-open')) {
        closeLoginPrompt();
      }
    });
  }

});

// ============================================================
// HELPERS
// ============================================================

function showLoginPrompt() {
  const modal = document.getElementById('wishlist-login-modal');
  if (modal) {
    modal.classList.add('is-open');
  } else {
    alert('Please sign up or log in to use the wishlist.');
  }
}

function closeLoginPrompt() {
  const modal = document.getElementById('wishlist-login-modal');
  if (modal) modal.classList.remove('is-open');
}

function updateHeaderBadge(count) {
  const trigger = document.getElementById('wishlistTriggerBtn');
  if (!trigger) return;

  let badge = trigger.querySelector('.wishlist-badge');

  if (count > 0) {
    if (badge) {
      badge.textContent = count;
    } else {
      badge = document.createElement('span');
      badge.className = 'wishlist-badge';
      badge.textContent = count;
      trigger.appendChild(badge);
    }
  } else {
    if (badge) {
      badge.remove();
    }
  }
}

function checkEmptyWishlist() {
  const grid = document.querySelector('.wishlist-grid');
  if (grid && grid.children.length === 0) {
    grid.innerHTML = '<p>Your wishlist is empty.</p>';
  }
}

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : '';
}