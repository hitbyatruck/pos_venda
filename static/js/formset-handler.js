document.addEventListener('DOMContentLoaded', function() {
    // Function to initialize a formset
    function initFormset(formsetName) {
        const formsetContainer = document.querySelector(`#${formsetName}-formset`);
        if (!formsetContainer) return;

        const totalFormsInput = document.querySelector(`#id_${formsetName}-TOTAL_FORMS`);
        const maxFormsInput = document.querySelector(`#id_${formsetName}-MAX_NUM_FORMS`);
        const formCount = parseInt(totalFormsInput.value);
        const maxForms = parseInt(maxFormsInput.value);

        // Add new form button
        const addButton = document.querySelector(`#add-${formsetName}`);
        if (addButton) {
            addButton.addEventListener('click', function(e) {
                e.preventDefault();
                if (formCount < maxForms) {
                    const newForm = createNewForm(formsetName, formCount);
                    formsetContainer.appendChild(newForm);
                    totalFormsInput.value = formCount + 1;
                    updateButtonStates();
                }
            });
        }

        function createNewForm(prefix, index) {
            // Get the empty form template
            const emptyFormElement = document.querySelector(`#empty-${prefix}-form`);
            if (!emptyFormElement) return;

            // Create a new form from the template
            const newForm = emptyFormElement.cloneNode(true);
            newForm.id = `${prefix}-${index}`;
            newForm.classList.remove('d-none');
            
            // Update form index in all name and id attributes
            const inputs = newForm.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.name = input.name.replace('__prefix__', index);
                input.id = input.id.replace('__prefix__', index);
                if (input.type === 'checkbox') {
                    input.checked = false;
                } else {
                    input.value = '';
                }
            });

            // Add delete button functionality
            const deleteButton = newForm.querySelector(`.delete-${prefix}`);
            if (deleteButton) {
                deleteButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    newForm.remove();
                    updateFormIndices();
                    totalFormsInput.value = parseInt(totalFormsInput.value) - 1;
                    updateButtonStates();
                });
            }

            return newForm;
        }

        function updateFormIndices() {
            // Update form indices after deletion
            const forms = formsetContainer.querySelectorAll(`.${formsetName}-form:not(#empty-${formsetName}-form)`);
            forms.forEach((form, index) => {
                const inputs = form.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    input.name = input.name.replace(
                        new RegExp(`${formsetName}-\\d+-`), 
                        `${formsetName}-${index}-`
                    );
                    input.id = input.id.replace(
                        new RegExp(`id_${formsetName}-\\d+-`), 
                        `id_${formsetName}-${index}-`
                    );
                });
            });
        }

        function updateButtonStates() {
            // Disable add button if max forms reached
            if (addButton) {
                const currentForms = parseInt(totalFormsInput.value);
                addButton.disabled = currentForms >= maxForms;
            }
        }

        // Initial setup for delete buttons on existing forms
        const existingForms = formsetContainer.querySelectorAll(`.${formsetName}-form:not(#empty-${formsetName}-form)`);
        existingForms.forEach(form => {
            const deleteButton = form.querySelector(`.delete-${formsetName}`);
            if (deleteButton) {
                deleteButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    form.remove();
                    updateFormIndices();
                    totalFormsInput.value = parseInt(totalFormsInput.value) - 1;
                    updateButtonStates();
                });
            }
        });

        // Initial button state
        updateButtonStates();
        
        // If no forms exist yet, add an initial empty one
        if (formCount === 0) {
            addButton.click();
        }
    }

    // Initialize formsets
    initFormset('contacto');
});
