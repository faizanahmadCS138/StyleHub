document.addEventListener('DOMContentLoaded', function () {
  const trigger    = document.getElementById('searchTriggerBtn');
  const overlay    = document.getElementById('searchDrawerOverlay');
  const closeBtn   = document.getElementById('searchDrawerCloseBtn');
  const input      = document.getElementById('searchDrawerInput');
  const suggList   = document.getElementById('searchSuggestionsList');
  const resPanel   = document.getElementById('searchResultsPanel');
  const grid       = document.getElementById('searchProductsGrid');
  const viewAll    = document.getElementById('searchViewAllLink');

  if (!trigger || !overlay) return;

  const LIVE_URL   = trigger.dataset.liveUrl;
  const SEARCH_URL = trigger.dataset.searchUrl;

  let debounceTimer = null;

  function openDrawer() {
    overlay.classList.add('is-open');
    overlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    setTimeout(() => input.focus(), 150);
    fetchLive('');
  }

  function closeDrawer() {
    overlay.classList.remove('is-open');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    input.value = '';
    resPanel.hidden = true;
  }

  function showLoadingState() {
    resPanel.hidden = false;
    viewAll.style.display = 'none';
    grid.innerHTML = `
      <div class="search-loading-state" style="grid-column: 1/-1; padding: 30px 0; text-align: center; color: #555; font-size: 14px; font-weight: 500;">
        <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 22px; color: #111; margin-right: 10px; vertical-align: middle;"></i>
        Searching products...
      </div>
    `;
  }

  function renderSuggestions(suggestions) {
    if (!suggestions || !suggestions.length) {
      suggList.innerHTML = '<li style="color:#888; cursor:default;">No suggestions</li>';
      return;
    }
    suggList.innerHTML = suggestions.map(s =>
      `<li data-term="${s}"><i class="fa-solid fa-magnifying-glass"></i> ${s}</li>`
    ).join('');
  }

  function renderProducts(products, total, query) {
    if (!products || !products.length) {
      resPanel.hidden = false;
      grid.innerHTML = `<p style="grid-column: 1/-1; color: #666; font-size: 14px; padding: 15px 0;">No products found matching "${query}"</p>`;
      viewAll.style.display = 'none';
      return;
    }
    resPanel.hidden = false;
    viewAll.style.display = 'inline-block';
    grid.innerHTML = products.map(p => `
      <a href="${p.url}" class="search-product-card">
        ${p.image ? `<img src="${p.image}" alt="${p.name}" loading="lazy">` : `<div class="search-no-img">NO IMAGE</div>`}
        <div class="name">${p.name}</div>
        <div class="price">
          PKR ${p.price}
          ${p.original_price ? `<span class="original">PKR ${p.original_price}</span>` : ''}
        </div>
      </a>
    `).join('');
    viewAll.href = `${SEARCH_URL}?q=${encodeURIComponent(query)}`;
    viewAll.textContent = `View all ${total} results`;
  }

  function fetchLive(query) {
    if (query.trim().length >= 2) {
      showLoadingState();
    }
    fetch(`${LIVE_URL}?q=${encodeURIComponent(query)}`)
      .then(r => r.json())
      .then(data => {
        renderSuggestions(data.suggestions);
        if (query.trim().length >= 2) {
          renderProducts(data.products, data.total, query);
        } else {
          resPanel.hidden = true;
        }
      })
      .catch(err => console.error('Live search error:', err));
  }

  trigger.addEventListener('click', openDrawer);
  closeBtn.addEventListener('click', closeDrawer);

  overlay.addEventListener('click', e => {
    if (e.target === overlay) closeDrawer();
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && overlay.classList.contains('is-open')) closeDrawer();
  });

  input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const query = input.value;
    debounceTimer = setTimeout(() => fetchLive(query), 200);
  });

  suggList.addEventListener('click', e => {
    const li = e.target.closest('li');
    if (!li || !li.dataset.term) return;
    const term = li.dataset.term;
    input.value = term;
    fetchLive(term);
  });
});