/* Drawer Navigation & Tab Switcher Module */
document.addEventListener('DOMContentLoaded', function () {
    const menuBtn = document.getElementById('menuToggleBtn');
    const closeBtn = document.getElementById('drawerCloseBtn');
    const drawerOverlay = document.getElementById('navDrawerOverlay');
    const drawerTabs = document.querySelectorAll('.drawer-tab');
    const drawerTabContents = document.querySelectorAll('.drawer-tab-content');

    // Open Drawer
    if (menuBtn && drawerOverlay) {
        menuBtn.addEventListener('click', function () {
            drawerOverlay.classList.add('open');
            document.body.style.overflow = 'hidden';
        });
    }

    // Close Drawer
    if (closeBtn && drawerOverlay) {
        closeBtn.addEventListener('click', function () {
            drawerOverlay.classList.remove('open');
            document.body.style.overflow = 'auto';
        });
    }

    // Close on overlay click outside content
    if (drawerOverlay) {
        drawerOverlay.addEventListener('click', function (e) {
            if (e.target === drawerOverlay) {
                drawerOverlay.classList.remove('open');
                document.body.style.overflow = 'auto';
            }
        });
    }

    // Tab Switching (MEN, WOMEN, KIDS)
    drawerTabs.forEach(tab => {
        tab.addEventListener('click', function () {
            const targetTab = this.getAttribute('data-tab');

            // Toggle Tab Buttons
            drawerTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');

            // Toggle Tab Content Panels
            drawerTabContents.forEach(content => {
                if (content.getAttribute('id') === `tab-content-${targetTab}`) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });
        });
    });
});
