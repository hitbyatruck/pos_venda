document.addEventListener("DOMContentLoaded", function() {
    console.log("assistencia_scripts.js carregado.");

    const API_ENDPOINTS = {
        EQUIPAMENTOS: '/assistencia/api/equipamentos/por-cliente/'
    };

    // Utility Functions
    function getCSRFToken() {
        const name = "csrftoken";
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Initialize Delete Functionality
    function initializeDelete() {
        const modalEl = document.getElementById("patConfirmModal");
        if (!modalEl || typeof bootstrap === 'undefined') {
            console.error("Modal element or Bootstrap not found");
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

    // Initialize delete functionality if modal exists
    if (document.getElementById("patConfirmModal")) {
        console.log("Initializing delete functionality");
        initializeDelete();
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
    initializeItemsTable();
    
});


// Initialize Items Table and related functionality
function initializeItemsTable() {
    const addItemBtn = document.getElementById("addItemBtn");
    const totalFormsInput = document.getElementById("id_itens-TOTAL_FORMS");
    const itensTableBody = document.querySelector("#itensTable tbody");
    const grandTotalElem = document.getElementById("grandTotalValue");
    const templateRow = itensTableBody ? itensTableBody.querySelector("tr.template-row") : null;

    if (!itensTableBody || !templateRow) {
        console.log("Tabela de itens não encontrada ou não necessária nesta página.");
        return;
    }

    function updateRowTotal(row) {
        const quantidadeInput = row.querySelector("input.quantidade");
        const precoInput = row.querySelector("input.preco");
        let quantidade = parseFloat(quantidadeInput ? quantidadeInput.value : 0) || 0;
        let preco = parseFloat(precoInput ? precoInput.value : 0) || 0;
        let rowTotal = quantidade * preco;
        const rowTotalElem = row.querySelector(".row-total");
        if (rowTotalElem) {
            rowTotalElem.textContent = rowTotal.toFixed(2);
        }
        updateGrandTotal();
    }

    function updateGrandTotal() {
        let grandTotal = 0;
        const rows = itensTableBody.querySelectorAll("tr.item-row:not(.template-row)");
        rows.forEach(row => {
            const rowTotalElem = row.querySelector(".row-total");
            grandTotal += parseFloat(rowTotalElem.textContent) || 0;
        });
        if (grandTotalElem) {
            grandTotalElem.textContent = grandTotal.toFixed(2);
        }
    }

    function addCalculationListeners(row) {
        const quantidadeInput = row.querySelector("input.quantidade");
        const precoInput = row.querySelector("input.preco");
        const tipoField = row.querySelector("[name*='-tipo']");
        const referenciaField = row.querySelector("[name*='-referencia']");
        const designacaoField = row.querySelector("[name*='-designacao']");

        [quantidadeInput, precoInput, tipoField, referenciaField, designacaoField].forEach(field => {
            if (field) {
                field.addEventListener("input", function() {
                    this.setCustomValidity("");
                    if (field === quantidadeInput || field === precoInput) {
                        updateRowTotal(row);
                    }
                });
            }
        });
    }

    function updateTotalForms() {
        const rows = itensTableBody.querySelectorAll("tr.item-row:not(.template-row)");
        if (totalFormsInput) {
            totalFormsInput.value = rows.length;
        }
    }

    function addNewItemRow() {
        let currentCount = parseInt(totalFormsInput.value) || 0;
        let newRow = templateRow.cloneNode(true);
        newRow.style.display = "";
        newRow.classList.remove("template-row");
        newRow.classList.add("item-row");

        newRow.querySelectorAll("input, select").forEach(input => {
            if (input.name) {
                input.name = input.name.replace("__prefix__", currentCount);
                input.id = input.id.replace("__prefix__", currentCount);
                input.value = "";
            }
        });

        itensTableBody.insertBefore(newRow, document.getElementById("grandTotalRow"));
        totalFormsInput.value = currentCount + 1;
        
        addCalculationListeners(newRow);
        newRow.querySelector(".item-delete").addEventListener("click", function() {
            newRow.remove();
            updateTotalForms();
            updateGrandTotal();
        });
        
        updateTotalForms();
        updateGrandTotal();
    }

    function isEmptyRow(row) {
        const fields = row.querySelectorAll('input[type="text"], input[type="number"], select');
        return Array.from(fields).every(field => !field.value.trim());
    }

    // Initialize existing rows
    const existingRows = itensTableBody.querySelectorAll("tr.item-row:not(.template-row)");
    existingRows.forEach(row => {
        addCalculationListeners(row);
        updateRowTotal(row);
        const deleteBtn = row.querySelector(".item-delete");
        if (deleteBtn) {
            deleteBtn.addEventListener("click", function() {
                row.remove();
                updateTotalForms();
                updateGrandTotal();
            });
        }
    });
    updateGrandTotal();

    // Add Item button listener
    if (addItemBtn) {
        addItemBtn.addEventListener("click", function() {
            const existingRows = itensTableBody.querySelectorAll("tr.item-row:not(.template-row)");
            const lastRow = existingRows[existingRows.length - 1];
            
            // Check if there's no rows or if last row is not empty
            if (!existingRows.length || !isEmptyRow(lastRow)) {
                addNewItemRow();
            } else {
                console.log("Cannot add new row: last row is empty");
            }
        });
    }

    // Form submission validation
    const patForm = document.getElementById("patForm");
    if (patForm) {
        patForm.addEventListener("submit", function(event) {
            let invalidRowFound = false;
            const itemRows = itensTableBody.querySelectorAll("tr.item-row:not(.template-row)");
            
            // Clear all previous validations
            itemRows.forEach(row => {
                row.querySelectorAll("input, select").forEach(field => {
                    field.setCustomValidity("");
                });
            });
        
            // Remove all empty rows except the last one
            const emptyRows = Array.from(itemRows).filter(row => isEmptyRow(row));
            emptyRows.slice(0, -1).forEach(row => row.remove());
        
            // Validate non-empty rows
            itemRows.forEach(row => {
                if (!isEmptyRow(row)) {
                    const fields = {
                        tipo: row.querySelector("[name*='-tipo']"),
                        referencia: row.querySelector("[name*='-referencia']"),
                        designacao: row.querySelector("[name*='-designacao']"),
                        quantidade: row.querySelector("input.quantidade"),
                        preco: row.querySelector("input.preco")
                    };
        
                    Object.entries(fields).forEach(([key, field]) => {
                        if (field && !field.value.trim()) {
                            invalidRowFound = true;
                            field.setCustomValidity("Preencha todos os campos ou exclua a linha");
                            field.reportValidity();
                        }
                    });
                }
            });
        

            updateTotalForms();
            if (invalidRowFound) {
                event.preventDefault();
                patForm.reportValidity();
            }
        });
    }
}
