document.addEventListener('DOMContentLoaded', function () {
    // Clear cart counts or cached session items on order completion
    if (window.localStorage) {
        localStorage.removeItem('cart_count');
        localStorage.removeItem('cart_items');
    }

    // Optional: Auto-print or handle receipt downloads if needed
    const printBtn = document.getElementById('btn-print-receipt');
    if (printBtn) {
        printBtn.addEventListener('click', function (e) {
            e.preventDefault();
            window.print();
        });
    }
});