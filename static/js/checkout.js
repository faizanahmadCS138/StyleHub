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