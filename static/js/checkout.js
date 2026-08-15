document.addEventListener('DOMContentLoaded', function () {
    const radioCod = document.getElementById('radio-cod');
    const radioStripe = document.getElementById('radio-stripe');
    const labelCod = document.getElementById('label-cod');
    const labelStripe = document.getElementById('label-stripe');
    const stripeInfo = document.getElementById('stripe-info');
    const submitBtn = document.getElementById('submit-btn');

    function updatePaymentUI() {
        if (radioStripe && radioStripe.checked) {
            labelStripe.classList.add('selected');
            labelCod.classList.remove('selected');
            stripeInfo.style.display = 'block';
            submitBtn.textContent = 'Pay now with Stripe';
        } else if (radioCod) {
            labelCod.classList.add('selected');
            labelStripe.classList.remove('selected');
            stripeInfo.style.display = 'none';
            submitBtn.textContent = 'Complete Order';
        }
    }

    if (radioCod && radioStripe) {
        radioCod.addEventListener('change', updatePaymentUI);
        radioStripe.addEventListener('change', updatePaymentUI);
        updatePaymentUI();
    }

    // Saved Address Selection logic for logged-in users
    const savedAddressSelect = document.getElementById('saved-address-select');

    if (savedAddressSelect) {
        const firstNameInput = document.querySelector('input[name="first_name"]');
        const lastNameInput = document.querySelector('input[name="last_name"]');
        const addressInput = document.querySelector('input[name="address"]');
        const citySelect = document.querySelector('select[name="city"]');
        const phoneInput = document.querySelector('input[name="phone"]');

        const userDefaultFirstName = firstNameInput ? firstNameInput.value : '';
        const userDefaultLastName = lastNameInput ? lastNameInput.value : '';
        const userDefaultPhone = phoneInput ? phoneInput.value : '';

        function findMatchingCity(cityVal, streetVal) {
            if (!citySelect) return '';
            const cityLower = (cityVal || '').trim().toLowerCase();
            const streetLower = (streetVal || '').trim().toLowerCase();
            for (let i = 0; i < citySelect.options.length; i++) {
                const val = citySelect.options[i].value;
                if (!val) continue;
                const valLower = val.toLowerCase();
                if (cityLower === valLower || cityLower.includes(valLower) || streetLower.includes(valLower)) {
                    return val;
                }
            }
            return '';
        }

        function handleAddressDropdownChange() {
            const selectedOpt = savedAddressSelect.options[savedAddressSelect.selectedIndex];

            if (!selectedOpt || selectedOpt.value === 'new') {
                if (addressInput) {
                    addressInput.value = '';
                    addressInput.placeholder = 'Type your new address here...';
                    addressInput.focus();
                }
                if (citySelect) citySelect.value = '';
                if (phoneInput) phoneInput.value = userDefaultPhone;
                if (firstNameInput) firstNameInput.value = userDefaultFirstName;
                if (lastNameInput) lastNameInput.value = userDefaultLastName;
            } else {
                const street = selectedOpt.dataset.street || '';
                const apartment = selectedOpt.dataset.apartment || '';
                const cityData = selectedOpt.dataset.city || '';
                const phone = selectedOpt.dataset.phone || '';
                const fullName = selectedOpt.dataset.fullName || '';

                let fullAddress = street;
                if (apartment && !street.includes(apartment)) {
                    fullAddress = street + (street ? ', ' : '') + apartment;
                }

                const matchedCity = findMatchingCity(cityData, street);

                if (addressInput) addressInput.value = fullAddress;
                if (citySelect) citySelect.value = matchedCity;
                if (phoneInput) phoneInput.value = phone || userDefaultPhone;

                if (fullName) {
                    const parts = fullName.trim().split(/\s+/);
                    if (parts.length > 0 && parts[0] && firstNameInput) {
                        firstNameInput.value = parts[0];
                    }
                    if (parts.length > 1 && lastNameInput) {
                        lastNameInput.value = parts.slice(1).join(' ');
                    }
                }
            }
        }

        savedAddressSelect.addEventListener('change', handleAddressDropdownChange);

        function markAddressAsCustom() {
            if (savedAddressSelect && savedAddressSelect.value !== 'new') {
                savedAddressSelect.value = 'new';
            }
        }

        if (addressInput) addressInput.addEventListener('input', markAddressAsCustom);
        if (citySelect) citySelect.addEventListener('change', markAddressAsCustom);
        if (phoneInput) phoneInput.addEventListener('input', markAddressAsCustom);
    }

    // Cart Item Removal
    const removeBtns = document.querySelectorAll('.remove-item-btn');
    removeBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const variantId = this.dataset.variantId;
            if (!variantId) return;

            const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
            const csrfToken = csrfTokenElement ? csrfTokenElement.value : '';

            fetch('/api/cart/', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ variant_id: variantId })
            })
            .then(res => res.json())
            .then(data => {
                if (data.items) {
                    window.location.reload();
                }
            })
            .catch(err => console.error('Error removing item:', err));
        });
    });
});