// Utility Functions
function getCSRFToken() {
    const name = "csrftoken";
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


document.addEventListener("DOMContentLoaded", function() {
    console.log("assistencia_scripts.js loaded", new Date().toISOString());

    const API_ENDPOINTS = {
        EQUIPAMENTOS: '/assistencia/api/equipamentos/por-cliente/'
    };

    
    // Initialize Delete Functionality (modal for PAT deletion)
    function initializeDelete() {
        const modalEl = document.getElementById("patConfirmModal");
        if (!modalEl || typeof bootstrap === 'undefined') {
            console.log("Modal element or Bootstrap not found");
            return;
        }

        const modal = new bootstrap.Modal(modalEl);
        const confirmBtn = document.getElementById("patConfirmModalBtn");
        let currentPatId = null;
        let currentPatUrl = null;

        // Handle delete button clicks
        document.addEventListener("click", function(event) {
            const deleteBtn = event.target.closest(".pat-delete");
            if (deleteBtn) {
                event.preventDefault();
                currentPatId = deleteBtn.getAttribute("data-id");
                currentPatUrl = deleteBtn.getAttribute("data-url");
                console.log("Opening delete modal for PAT:", currentPatId);
                modal.show();
            }
        });

        // Handle confirmation
        confirmBtn.addEventListener("click", function() {
            if (!currentPatId || !currentPatUrl) {
                console.error("Missing PAT data for deletion");
                return;
            }

            console.log("Confirming deletion of PAT:", currentPatId);
            
            fetch(currentPatUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            })
            .then(async response => {
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.message || `Erro no servidor: ${response.status}`);
                }
                return data;
            })
            .then(data => {
                if (data.success) {
                    const row = document.getElementById(`pat-row-${currentPatId}`);
                    if (row) {
                        row.remove();
                        console.log("PAT deleted successfully:", data.message);
                    }
                    modal.hide();
                } else {
                    throw new Error(data.message || "Erro ao excluir PAT");
                }
            })
            .catch(error => {
                console.error("Error during deletion:", error);
                alert(error.message);
            })
            .finally(() => {
                currentPatId = null;
                currentPatUrl = null;
            });
        });
    }

    // Equipamentos Dropdown Functionality
    const clienteSelect = document.getElementById("id_cliente");
    const equipamentoSelect = document.getElementById("id_equipamento");
    const preselectedEquipamento = equipamentoSelect ? equipamentoSelect.value : "";

    if (clienteSelect && equipamentoSelect) {
        function updateEquipamentoDropdown(clienteId, selectedEquipId) {
            console.log("Atualizando equipamentos para cliente ID:", clienteId);
            if (!clienteId) {
                equipamentoSelect.innerHTML = '<option value="">Selecione um Cliente Primeiro</option>';
                return;
            }
            fetch(`${API_ENDPOINTS.EQUIPAMENTOS}?cliente_id=${clienteId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (!data.success) {
                        throw new Error(data.message || 'Erro ao carregar equipamentos');
                    }

                    console.log("Equipamentos recebidos:", data);
                    equipamentoSelect.innerHTML = "";
                    
                    let placeholderOpt = document.createElement("option");
                    placeholderOpt.value = "";
                    placeholderOpt.text = "Selecione um Equipamento";
                    equipamentoSelect.appendChild(placeholderOpt);
                    
                    if (data.equipamentos && data.equipamentos.length > 0) {
                        data.equipamentos.forEach(eq => {
                            let option = document.createElement("option");
                            option.value = eq.id;
                            option.textContent = `${eq.nome} (Nº Série: ${eq.numero_serie})`;
                            equipamentoSelect.appendChild(option);
                        });
                    } else {
                        let noEquipOpt = document.createElement("option");
                        noEquipOpt.value = "";
                        noEquipOpt.text = "Nenhum equipamento encontrado";
                        equipamentoSelect.appendChild(noEquipOpt);
                    }
                    
                    if (selectedEquipId) {
                        const option = equipamentoSelect.querySelector(`option[value="${selectedEquipId}"]`);
                        if (option) option.selected = true;
                    }
                    
                    console.log("Dropdown Equipamento atualizado.");
                })
                .catch(error => {
                    console.error("Erro ao buscar equipamentos:", error);
                    equipamentoSelect.innerHTML = '<option value="">Erro ao carregar equipamentos</option>';
                });
        }

        clienteSelect.addEventListener("change", function() {
            console.log("Cliente selecionado (change event):", this.value);
            updateEquipamentoDropdown(this.value, "");
        });

        if (clienteSelect.value) {
            updateEquipamentoDropdown(clienteSelect.value, preselectedEquipamento);
        }
    }

    // Items Table Functionality
    const patForm = document.getElementById("patForm");
    if (patForm) {
        // Setup form submission handler
        patForm.addEventListener("submit", handleFormSubmit);
        
        // Initialize item-related stuff
        setupItemFunctionality();
    }

    // Initialize delete functionality if modal exists
    if (document.getElementById("patConfirmModal")) {
        initializeDelete();
    }
});

// ITEM TABLE FUNCTIONALITY
function setupItemFunctionality() {
    // BUTTON SETUP
    const addItemBtn = document.getElementById("addItemBtn");
    if (addItemBtn) {
        addItemBtn.addEventListener("click", addNewRow);
    }
    
    // SETUP EXISTING ROWS
    document.querySelectorAll(".item-row:not(.template-row)").forEach(row => {
        setupRowHandlers(row);
        validateRow(row);
        updateRowTotal(row);
    });
    
    // INITIALIZE TOTALS
    updateGrandTotal();
    
    // DISABLE ADD BUTTON IF EMPTY ROW EXISTS
    updateAddItemButtonState();
}

// FORM SUBMISSION HANDLER
function handleFormSubmit(event) {
    console.log("Form submission handler running");
    
    // Prevent double submission
    if (event.target.hasAttribute("data-submitting")) {
        return true;
    }
    
    // Process any hidden rows to ensure DELETE is properly set
    document.querySelectorAll('.item-row[style*="display: none"]').forEach(row => {
        const deleteCheckbox = row.querySelector('input[name$="-DELETE"]');
        if (deleteCheckbox) {
            console.log("Marcando checkbox para linha escondida");
            deleteCheckbox.checked = true;
        }
    });
    
    // Mark the form as being submitted
    event.target.setAttribute("data-submitting", "true");
    
    // Log submission for debug
    console.log("Form is being submitted");
    return true;
}

// ADD/DELETE ROW FUNCTIONS
function addNewRow() {
    const table = document.getElementById("itensTable");
    const tbody = table.querySelector("tbody");
    const templateRow = document.querySelector(".template-row");
    const totalFormsInput = document.querySelector('[name$="TOTAL_FORMS"]');
    
    if (!templateRow || !totalFormsInput) {
        console.error("Missing template row or total forms input");
        return;
    }
    
    // Clone the template row
    const newRow = templateRow.cloneNode(true);
    newRow.classList.remove("template-row");
    newRow.style.display = "";
    
    // Update form index
    const formCount = parseInt(totalFormsInput.value, 10);
    newRow.innerHTML = newRow.innerHTML.replace(/__prefix__/g, formCount);
    
    // Add to table before the grand total row
    const grandTotalRow = document.getElementById("grandTotalRow");
    if (grandTotalRow) {
        tbody.insertBefore(newRow, grandTotalRow);
    } else {
        tbody.appendChild(newRow);
    }
    
    // Increment form count
    totalFormsInput.value = formCount + 1;
    
    // Setup handlers for the new row
    setupRowHandlers(newRow);
    
    // Initialize row total
    updateRowTotal(newRow);
    
    // Disable add button if needed
    updateAddItemButtonState();
}

// Substitua a função deleteRow por esta versão mais simples:

function deleteRow(row) {
    // Esta é uma solução alternativa para excluir via AJAX em vez de depender do formset
    const idInput = row.querySelector('input[name$="-id"]');
    
    if (idInput && idInput.value) {
        // Item existente - fazer requisição AJAX para excluir diretamente
        const itemId = idInput.value;
        console.log("Excluindo item ID:", itemId);
        
        fetch(`/assistencia/api/item/${itemId}/excluir/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log("Item excluído com sucesso!");
                row.remove(); // Remove a linha da tabela
                updateGrandTotal();
            } else {
                console.error("Erro ao excluir item:", data.error);
                alert("Erro ao excluir item: " + data.error);
            }
        })
        .catch(error => {
            console.error("Erro na requisição:", error);
            alert("Erro ao comunicar com o servidor");
        });
    } else {
        // Nova linha - apenas remover do DOM
        row.remove();
    }
    
    updateGrandTotal();
    updateAddItemButtonState();
}

// ROW HANDLERS
function setupRowHandlers(row) {
    // Delete button
    const deleteBtn = row.querySelector(".item-delete");
    if (deleteBtn) {
        deleteBtn.addEventListener("click", function() {
            deleteRow(row);
        });
    }
    
    // Quantity and price fields
    const qtyField = row.querySelector(".quantidade");
    const priceField = row.querySelector(".preco");
    
    if (qtyField) {
        qtyField.addEventListener("input", function() {
            updateRowTotal(row);
        });
    }
    
    if (priceField) {
        priceField.addEventListener("input", function() {
            updateRowTotal(row);
        });
    }
    
    // All fields for validation
    row.querySelectorAll("input, select").forEach(field => {
        field.addEventListener("change", function() {
            validateRow(row);
            updateAddItemButtonState();
        });
    });
}

// VALIDATION FUNCTION
function validateRow(row) {
    // Remover classes de erro anteriores
    row.querySelectorAll('.is-invalid').forEach(field => {
        field.classList.remove('is-invalid');
    });
    
    // Verificar se algum campo principal tem valor
    const tipoField = row.querySelector('select[name$="-tipo"]');
    const refField = row.querySelector('input[name$="-referencia"]');
    const descField = row.querySelector('input[name$="-designacao"]');
    
    const hasAnyValue = (
        (tipoField && tipoField.selectedIndex > 0) ||
        (refField && refField.value.trim()) ||
        (descField && descField.value.trim())
    );
    
    // Se tiver algum valor, todos são obrigatórios
    if (hasAnyValue) {
        if (tipoField && (!tipoField.value || tipoField.selectedIndex <= 0)) {
            tipoField.classList.add('is-invalid');
        }
        
        if (refField && !refField.value.trim()) {
            refField.classList.add('is-invalid');
        }
        
        if (descField && !descField.value.trim()) {
            descField.classList.add('is-invalid');
        }
    }
}

// TOTAL CALCULATIONS
function updateRowTotal(row) {
    const qtyInput = row.querySelector(".quantidade");
    const priceInput = row.querySelector(".preco");
    const totalCell = row.querySelector(".row-total");
    
    if (qtyInput && priceInput && totalCell) {
        const qty = parseFloat(qtyInput.value || 0);
        const price = parseFloat(priceInput.value || 0);
        const total = qty * price;
        
        totalCell.textContent = total.toFixed(2);
    }
    
    updateGrandTotal();
}

function updateGrandTotal() {
    const grandTotalElement = document.getElementById("grandTotalValue");
    if (!grandTotalElement) return;
    
    let total = 0;
    
    document.querySelectorAll('.item-row:not(.template-row):not([style*="display: none"])').forEach(row => {
        const totalCell = row.querySelector(".row-total");
        if (totalCell) {
            total += parseFloat(totalCell.textContent || 0);
        }
    });
    
    grandTotalElement.textContent = total.toFixed(2);
}

// BUTTON STATE MANAGEMENT
function updateAddItemButtonState() {
    const addButton = document.getElementById("addItemBtn");
    if (!addButton) return;
    
    const visibleRows = document.querySelectorAll('.item-row:not(.template-row):not([style*="display: none"])');
    let hasEmptyRow = false;
    
    visibleRows.forEach(row => {
        // Check if row is empty
        const tipoField = row.querySelector('select[name$="-tipo"]');
        const refField = row.querySelector('input[name$="-referencia"]');
        const descField = row.querySelector('input[name$="-designacao"]');
        
        const isEmpty = (
            (!tipoField || tipoField.selectedIndex <= 0) &&
            (!refField || !refField.value.trim()) &&
            (!descField || !descField.value.trim())
        );
        
        if (isEmpty) {
            hasEmptyRow = true;
        }
    });
    
    // Disable add button if there's already an empty row
    addButton.disabled = hasEmptyRow;
}