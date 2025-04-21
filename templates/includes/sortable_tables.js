/**
 * Adds sorting functionality to all tables with the 'sortable-table' class
 * Usage:
 * 1. Add the 'sortable-table' class to the table
 * 2. Add the 'sortable' class to any th element you want to be sortable
 * 3. (Optional) Add 'data-sort-type' attribute to specify sort type:
 *    - 'text' (default): sorts as text
 *    - 'number': sorts as numbers
 *    - 'date': sorts as dates (format: DD/MM/YYYY or YYYY-MM-DD)
 */
document.addEventListener('DOMContentLoaded', function() {
    const sortableTables = document.querySelectorAll('table.sortable-table');

    sortableTables.forEach(function(table) {
        const headers = table.querySelectorAll('th.sortable');
        let currentSort = null;

        headers.forEach(function(header) {
            // Add sort icon and styling
            const icon = document.createElement('i');
            icon.className = 'fas fa-sort ms-1 text-muted sort-icon';
            header.appendChild(icon);
            header.style.cursor = 'pointer';

            // Add click event
            header.addEventListener('click', function() {
                const columnIndex = Array.from(header.parentNode.children).indexOf(header);
                const sortType = header.getAttribute('data-sort-type') || 'text';

                // Reset all headers
                headers.forEach(h => {
                    h.querySelector('.sort-icon').className = 'fas fa-sort ms-1 text-muted sort-icon';
                });

                // Determine sort direction
                let sortDirection = 'asc';
                if (currentSort &&
                    currentSort.columnIndex === columnIndex &&
                    currentSort.direction === 'asc') {
                    sortDirection = 'desc';
                }

                // Update current sort state
                currentSort = {
                    columnIndex: columnIndex,
                    direction: sortDirection
                };

                // Update sort icon
                const sortIcon = header.querySelector('.sort-icon');
                sortIcon.className = `fas fa-sort-${sortDirection === 'asc' ? 'up' : 'down'} ms-1 text-primary sort-icon`;

                // Sort the table
                sortTable(table, columnIndex, sortDirection, sortType);
            });
        });
    });

    function sortTable(table, columnIndex, sortDirection, sortType) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));

        // Sort rows
        const sortedRows = rows.sort((a, b) => {
            const aValue = getCellValue(a, columnIndex, sortType);
            const bValue = getCellValue(b, columnIndex, sortType);

            if (sortDirection === 'asc') {
                return aValue > bValue ? 1 : -1;
            } else {
                return aValue < bValue ? 1 : -1;
            }
        });

        // Clear and re-append rows
        while (tbody.firstChild) {
            tbody.removeChild(tbody.firstChild);
        }

        sortedRows.forEach(row => tbody.appendChild(row));
    }

    function getCellValue(row, columnIndex, sortType) {
        const cell = row.cells[columnIndex];
        if (!cell) return '';

        let value = cell.textContent.trim();

        // Check for explicit sort value in data attribute
        if (cell.hasAttribute('data-sort-value')) {
            value = cell.getAttribute('data-sort-value');
        }

        // Convert value based on sort type
        switch (sortType) {
            case 'number':
                return parseFloat(value.replace(/[^\d.-]/g, '')) || 0;
            case 'date':
                // Handle DD/MM/YYYY format
                if (value.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
                    const parts = value.split('/');
                    return new Date(parts[2], parts[1] - 1, parts[0]).getTime();
                }
                // Handle YYYY-MM-DD format
                else if (value.match(/^\d{4}-\d{2}-\d{2}$/)) {
                    return new Date(value).getTime();
                }
                return new Date(value).getTime() || 0;
            default:
                return value.toLowerCase();
        }
    }
});
