document.addEventListener('DOMContentLoaded', function () {
    // Get formset container, total form input and add button
    const formsetContainer = document.querySelector('.contacto-formset');
    const totalForms = document.querySelector('#id_contacto_set-TOTAL_FORMS');
    const addButton = document.querySelector('#add-contacto-btn');

    if (!formsetContainer || !totalForms || !addButton) {
        return; // Exit if elements not found
    }

    // Add new contact form
    addButton.addEventListener('click', function () {
        const formCount = formsetContainer.children.length;

        // Get the first form as a template and clone it
        const formTemplate = formsetContainer.querySelector('.contacto-form');
        const newForm = formTemplate.cloneNode(true);

        // Update form index numbers
        newForm.innerHTML = newForm.innerHTML.replace(/-0-/g, `-${formCount}-`);
        newForm.innerHTML = newForm.innerHTML.replace(/_0_/g, `_${formCount}_`);

        // Clear form fields
        newForm.querySelectorAll('input:not([type=hidden]):not([type=checkbox]), select, textarea').forEach(input => {
            input.value = '';
        });

        // Uncheck checkboxes
        newForm.querySelectorAll('input[type=checkbox]').forEach(checkbox => {
            checkbox.checked = false;
        });

        // Add delete button if not present
        const header = newForm.querySelector('.card-header');
        if (!header.querySelector('.btn-remove-form')) {
            const removeButton = document.createElement('button');
            removeButton.type = 'button';
            removeButton.className = 'btn btn-sm btn-danger btn-remove-form';
            removeButton.innerHTML = '<i class="fas fa-trash"></i>';
            header.appendChild(removeButton);
        }

        // Update form index number in header
        newForm.querySelector('.form-index').textContent = formCount + 1;

        // Reset errors
        newForm.querySelectorAll('.invalid-feedback').forEach(feedback => {
            feedback.textContent = '';
        });

        formsetContainer.appendChild(newForm);
        totalForms.value = formCount + 1;
    });

    // Remove form
    formsetContainer.addEventListener('click', function (e) {
        if (e.target.closest('.btn-remove-form')) {
            const form = e.target.closest('.contacto-form');
            const deleteInput = form.querySelector('input[name$="-DELETE"]');

            if (deleteInput) {
                deleteInput.value = 'on';
                form.style.display = 'none';
            } else {
                form.remove();

                // Update form indexes and total
                const forms = formsetContainer.querySelectorAll('.contacto-form:not([style*="display: none"])');
                totalForms.value = forms.length;

                // Update form index numbers in headers
                forms.forEach((form, index) => {
                    form.querySelector('.form-index').textContent = index + 1;
                });
            }
        }
    });
});
