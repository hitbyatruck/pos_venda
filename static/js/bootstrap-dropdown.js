/**
 * Bootstrap Dropdown Enhancer
 * 
 * This script ensures all Bootstrap dropdowns work correctly across the application,
 * including those that are dynamically loaded.
 */
document.addEventListener('DOMContentLoaded', function () {
    // Initialize all existing dropdowns
    initializeDropdowns();

    // Monitor for any dynamically added dropdowns
    const observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                // Check if any added nodes contain dropdowns
                for (let i = 0; i < mutation.addedNodes.length; i++) {
                    const node = mutation.addedNodes[i];
                    if (node.nodeType === 1) { // Only process Element nodes
                        const dropdowns = node.querySelectorAll('.dropdown-toggle');
                        if (dropdowns.length > 0) {
                            initializeDropdowns(node);
                        }
                    }
                }
            }
        });
    });

    // Start observing the document for dynamic changes
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // Initialize dropdown elements
    function initializeDropdowns(context = document) {
        const dropdownToggleList = context.querySelectorAll('.dropdown-toggle');

        dropdownToggleList.forEach(function (dropdownToggle) {
            // Ensure dropdown toggle has correct attributes
            if (!dropdownToggle.hasAttribute('data-bs-toggle')) {
                dropdownToggle.setAttribute('data-bs-toggle', 'dropdown');
            }

            // Create dropdown instance if not already created
            if (!dropdownToggle._dropdown) {
                new bootstrap.Dropdown(dropdownToggle);
            }
        });
    }
});
