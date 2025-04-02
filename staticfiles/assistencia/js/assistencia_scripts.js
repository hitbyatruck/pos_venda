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
                // Apenas prevenir o comportamento padrão se for um botão de exclusão
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

function deleteRow(row) {
    const deleteCheckbox = row.querySelector('input[name$="-DELETE"]');
    
    if (deleteCheckbox) {
        // Item existente - marcar para exclusão
        console.log("Marcando item para exclusão via checkbox");
        deleteCheckbox.checked = true;
        row.style.display = "none";
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

// TOTAL CALCULATIONS - MODIFICADO PARA CORRIGIR PRESERVAÇÃO DOS PREÇOS
function updateRowTotal(row) {
    const qtyInput = row.querySelector(".quantidade");
    const priceInput = row.querySelector(".preco");
    const totalCell = row.querySelector(".row-total");
    
    if (qtyInput && priceInput && totalCell) {
        // Valores garantidamente numéricos
        const qty = parseInt(qtyInput.value) || 1;
        let price = priceInput.value.replace(/[^\d.,]/g, '').replace(',', '.');
        price = parseFloat(price) || 0;
        
        const total = qty * price;
        
        // Atualizar valores nos elementos
        totalCell.textContent = total.toFixed(2);
        qtyInput.value = qty;
    }
    
    // CORREÇÃO: Recuperar preço do backup se estiver vazio
    if (priceInput.value === "" || priceInput.value === "None" || isNaN(parseFloat(priceInput.value))) {
        // Tentar recuperar do data-original-value
        if (priceInput.dataset.originalValue && priceInput.dataset.originalValue !== "None") {
            priceInput.value = priceInput.dataset.originalValue;
        } 
        // Ou tentar campo backup
        else {
            const backupInput = row.querySelector(`input[name="${priceInput.name}_backup"]`);
            if (backupInput && backupInput.value) {
                priceInput.value = backupInput.value;
            } else {
                priceInput.value = "0.00";
            }
        }
    }
    
    // CORREÇÃO: Converter para números explicitamente com garantias de tipo
    const qty = Math.floor(parseInt(qtyInput.value) || 1);  // Sempre inteiro e pelo menos 1
    const price = parseFloat(priceInput.value.toString().replace(',', '.')) || 0;  // Converter vírgulas
    const total = qty * price;
    
    console.log(`Calculando (corrigido): ${qty} x ${price} = ${total}`);
    
    // Atualizar valores nos campos
    qtyInput.value = qty.toString();
    priceInput.value = price.toFixed(2);
    totalCell.textContent = total.toFixed(2);
    
    // CORREÇÃO: Definir atributos value explicitamente 
    qtyInput.setAttribute('value', qty.toString());
    priceInput.setAttribute('value', price.toFixed(2));
    
    updateGrandTotal();
}

// Adicione um inicializador especial depois da função setupItemFunctionality
function specialInitializeItems() {
    console.log("Inicialização especial dos itens");
    
    // Inicializar os campos antes de calcular totais
    document.querySelectorAll('.item-row:not(.template-row)').forEach(row => {
        const qtyInput = row.querySelector(".quantidade");
        const priceInput = row.querySelector(".preco");
        
        if (qtyInput) {
            // Verificar valores problemáticos
            console.log(`Quantidade original: "${qtyInput.value}"`);
            if (qtyInput.value === "" || qtyInput.value === "None") {
                qtyInput.value = "1";
                qtyInput.setAttribute('value', "1");
            }
        }
        
        if (priceInput) {
            // Verificar valores problemáticos e log detalhado
            console.log(`Preço original: "${priceInput.value}"`);
            
            // Limpar possíveis problemas de formatação
            let cleanValue = (priceInput.value || "")
                .toString()
                .replace(/[^\d.,]/g, '') // remover caracteres não numéricos exceto ponto e vírgula
                .replace(',', '.'); // substituir vírgula por ponto
                
            if (cleanValue === "" || cleanValue === "None") {
                priceInput.value = "0.00";
            } else {
                try {
                    // Normalizar para formato de número com 2 casas decimais
                    let numValue = parseFloat(cleanValue);
                    priceInput.value = numValue.toFixed(2);
                } catch (e) {
                    console.error("Erro ao converter preço:", e);
                    priceInput.value = "0.00";
                }
            }
            
            // Definir explicitamente o atributo value
            priceInput.setAttribute('value', priceInput.value);
            console.log(`Preço normalizado: "${priceInput.value}"`);
        }
        
        // Calcular o total da linha
        updateRowTotal(row);
    });
    
    // Atualizar o total geral
    updateGrandTotal();
}

function updateGrandTotal() {
    const grandTotalElement = document.getElementById("grandTotalValue");
    const totalGeralInput = document.getElementById("total_geral_input");
    
    if (!grandTotalElement) return;
    
    let total = 0;
    
    document.querySelectorAll('.item-row:not(.template-row):not([style*="display: none"])').forEach(row => {
        const totalCell = row.querySelector(".row-total");
        if (totalCell) {
            // Garantir que o valor é um número
            const lineTotal = parseFloat(totalCell.textContent) || 0;
            total += lineTotal;
            console.log(`Linha com total: ${lineTotal}`);
        }
    });
    
    grandTotalElement.textContent = total.toFixed(2);
    
    // Atualizar o campo hidden do total geral
    if (totalGeralInput) {
        totalGeralInput.value = total.toFixed(2);
        console.log(`Total geral atualizado: ${total.toFixed(2)}`);
    }
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

document.addEventListener("DOMContentLoaded", function() {
    // Detectar se estamos na página de edição de PAT
    if (document.getElementById("patForm")) {
        console.log("Página com formulário PAT detectada");
        
        // Inicializar preços e totais com atraso para garantir carregamento completo
        setTimeout(function() {
            console.log("Inicializando valores para edição de PAT");
            inicializarValoresItens();
        }, 200);
    }
});

// Função única para inicializar valores
function inicializarValoresItens() {
    console.log("Inicializando valores dos itens");
    
    // Processar cada linha de item existente
    document.querySelectorAll('.item-row:not(.template-row)').forEach((row, index) => {
        const qtyInput = row.querySelector('.quantidade');
        const priceInput = row.querySelector('.preco');
        const totalCell = row.querySelector('.row-total');
        
        if (qtyInput && priceInput && totalCell) {
            // 1. Obter valor do atributo data-original-value no preço
            const originalPrice = priceInput.dataset.originalValue || 
                                 priceInput.getAttribute('data-original-value');
            
            // 2. Forçar valores nos inputs
            if (originalPrice && originalPrice !== "None" && originalPrice !== "0.00") {
                console.log(`Item ${index+1}: Usando preço original: ${originalPrice}`);
                priceInput.value = originalPrice;
            } else if (priceInput.value === "" || priceInput.value === "None" || priceInput.value === "0.00") {
                // Verificar se o preço está definido diretamente no elemento
                const backupValue = priceInput.getAttribute('value');
                if (backupValue && backupValue !== "None" && backupValue !== "0.00") {
                    priceInput.value = backupValue;
                } else {
                    // Se ainda não tivermos valor, tentar encontrar no data-original
                    const originalFromData = priceInput.getAttribute('data-original');
                    if (originalFromData && originalFromData !== "None") {
                        priceInput.value = originalFromData;
                    }
                }
            }
            
            // 3. Garantir que a quantidade seja um número inteiro
            if (qtyInput.value.includes('.') || qtyInput.value.includes(',')) {
                qtyInput.value = Math.floor(parseFloat(qtyInput.value.replace(',', '.')));
            }
            
            if (!qtyInput.value || qtyInput.value === "None") {
                qtyInput.value = "1";
            }
            
            // 4. Calcular o total da linha
            const qty = parseInt(qtyInput.value) || 1;
            const price = parseFloat(priceInput.value.replace(',', '.')) || 0;
            const total = qty * price;
            
            // 5. Atualizar campos
            totalCell.textContent = total.toFixed(2);
            
            // 6. Garantir que os valores permaneçam nos inputs
            qtyInput.setAttribute('value', qty);
            priceInput.setAttribute('value', price.toFixed(2));
            
            console.log(`Item ${index+1} inicializado: ${qty} x ${price.toFixed(2)} = ${total.toFixed(2)}`);
        }
    });
    
    // Atualizar o total geral
    updateGrandTotal();
}

// Função de debug
function debugFormValues() {
    console.group("DEBUG VALORES DO FORMULÁRIO");
    
    document.querySelectorAll('.item-row:not(.template-row)').forEach((row, i) => {
        const precoInput = row.querySelector('.preco');
        if (precoInput) {
            console.log(`Item ${i+1} Preço:`);
            console.log(`  - Valor no campo: "${precoInput.value}"`);
            console.log(`  - Tipo de dado: ${typeof precoInput.value}`);
            console.log(`  - Atributo value: "${precoInput.getAttribute('value')}"`);
            console.log(`  - Conversão parseFloat: ${parseFloat(precoInput.value)}`);
            
            // Verificar possíveis problemas de formatação
            if (precoInput.value.includes(',')) {
                console.warn(`  - ALERTA: Valor contém vírgula em vez de ponto decimal`);
            }
            
            if (isNaN(parseFloat(precoInput.value))) {
                console.error(`  - ERRO: Valor não pode ser convertido para número`);
            }
        }
    });
    
    console.groupEnd();
}

// CORREÇÃO: Manipulador de eventos de formulário atualizado
document.addEventListener('DOMContentLoaded', function() {
    console.log("Configurando manipulador de envio do formulário");
    
    const patForm = document.getElementById('patForm');
    if (patForm) {
        // Remover manipuladores existentes para evitar conflitos
        const clonedForm = patForm.cloneNode(true);
        patForm.parentNode.replaceChild(clonedForm, patForm);
        
        // Adicionar novo manipulador de eventos
        clonedForm.addEventListener('submit', function(event) {
            console.log("Formulário está sendo enviado");
            
            // Recalcular todos os totais antes do envio
            document.querySelectorAll('.item-row:not(.template-row)').forEach(function(row) {
                if (row.style.display !== 'none') {
                    // Obter os valores atuais
                    const qtyInput = row.querySelector('.quantidade');
                    const priceInput = row.querySelector('.preco');
                    
                    if (qtyInput && priceInput) {
                        // Garantir que são números válidos
                        const qty = parseInt(qtyInput.value) || 1;
                        let price = priceInput.value.replace(/[^\d.,]/g, '').replace(',', '.');
                        price = parseFloat(price) || 0;
                        
                        // Definir valores formatados
                        qtyInput.value = qty;
                        priceInput.value = price.toFixed(2);
                        
                        console.log(`Enviar linha: quantidade=${qty}, preço=${price.toFixed(2)}`);
                    }
                }
            });
            
            // Não impede o envio - permite submissão normal
            return true;
        });
    }
});