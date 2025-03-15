document.addEventListener("DOMContentLoaded", function() {
    console.log("assistencia_scripts.js carregado.");

    /* ========================================
       Atualização do Dropdown de Equipamentos
       ======================================== */
    const clienteSelect = document.getElementById("id_cliente");
    const equipamentoSelect = document.getElementById("id_equipamento");

    if (!clienteSelect || !equipamentoSelect) {
        console.error("Dropdowns de Cliente ou Equipamento não encontrados!");
    } else {
        function updateEquipamentoDropdown(clienteId) {
            console.log("Atualizando equipamentos para cliente ID:", clienteId);
            if (!clienteId) {
                equipamentoSelect.innerHTML = '<option value="">Selecione um Cliente Primeiro</option>';
                return;
            }
            fetch(`/assistencia/equipamentos-por-cliente/?cliente_id=${clienteId}`)
                .then(response => response.json())
                .then(data => {
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
                    console.log("Dropdown Equipamento atualizado.");
                })
                .catch(error => {
                    console.error("Erro ao buscar equipamentos:", error);
                    equipamentoSelect.innerHTML = '<option value="">Erro ao carregar equipamentos</option>';
                });
        }
    
        clienteSelect.addEventListener("change", function() {
            console.log("Cliente selecionado (change event):", this.value);
            updateEquipamentoDropdown(this.value);
        });
    
        if (clienteSelect.value) {
            console.log("Cliente pré-selecionado:", clienteSelect.value);
            updateEquipamentoDropdown(clienteSelect.value);
        }
    }

    /* ========================================
       Manipulação da Tabela de Itens
       ======================================== */
    const addItemBtn = document.getElementById("addItemBtn");
    const totalFormsInput = document.getElementById("id_itens-TOTAL_FORMS");
    const itensTableBody = document.querySelector("#itensTable tbody");
    const grandTotalElem = document.getElementById("grandTotalValue");
    const templateRow = itensTableBody.querySelector("tr.template-row");

    if (!addItemBtn) {
        console.error("Botão 'Adicionar Item' não encontrado.");
    }
    if (!totalFormsInput) {
        console.error("Campo de total de formulários não encontrado.");
    }
    if (!templateRow) {
        console.error("Linha template não encontrada. Certifique-se de que há uma linha com a classe 'template-row' oculta na tabela.");
    }

    // Função para atualizar o total de uma linha
    function updateRowTotal(row) {
        const quantidadeInput = row.querySelector("input.quantidade");
        const precoInput = row.querySelector("input.preco");
        let quantidade = parseFloat(quantidadeInput ? quantidadeInput.value : 0) || 0;
        let preco = parseFloat(precoInput ? precoInput.value : 0) || 0;
        let total = quantidade * preco;
        const rowTotalElem = row.querySelector(".row-total");
        if (rowTotalElem) {
            rowTotalElem.textContent = total.toFixed(2);
        }
        updateGrandTotal();
    }

    // Função para atualizar o total geral
    function updateGrandTotal() {
        let total = 0;
        const rows = itensTableBody.querySelectorAll("tr.item-row:not(.template-row)");
        rows.forEach(row => {
            const rowTotalElem = row.querySelector(".row-total");
            total += parseFloat(rowTotalElem.textContent) || 0;
        });
        if (grandTotalElem) {
            grandTotalElem.textContent = total.toFixed(2);
        }
    }

    // Adiciona listeners para atualizar o total quando os inputs mudam
    function addCalculationListeners(row) {
        const quantidadeInput = row.querySelector("input.quantidade");
        const precoInput = row.querySelector("input.preco");
        if (quantidadeInput) {
            quantidadeInput.addEventListener("input", function() {
                updateRowTotal(row);
            });
        }
        if (precoInput) {
            precoInput.addEventListener("input", function() {
                updateRowTotal(row);
            });
        }
    }

    // Inicializa listeners para as linhas já existentes
    const existingRows = itensTableBody.querySelectorAll("tr.item-row:not(.template-row)");
    existingRows.forEach(row => {
        addCalculationListeners(row);
        updateRowTotal(row);
    });
    updateGrandTotal();

    // Função para atualizar o total de formulários
    function updateTotalForms() {
        const rows = itensTableBody.querySelectorAll("tr.item-row:not(.template-row)");
        if (totalFormsInput) {
            totalFormsInput.value = rows.length;
        }
    }

    // Função para adicionar uma nova linha de item
    function addNewItemRow() {
        if (!templateRow) {
            console.error("Template row not found.");
            return;
        }
        let currentFormCount = parseInt(totalFormsInput.value);
        let newRow = templateRow.cloneNode(true);
        newRow.style.display = "";
        newRow.classList.remove("template-row");
        newRow.classList.add("item-row");
        // Atualiza os atributos name e id dos inputs da nova linha
        newRow.querySelectorAll("input, select, textarea").forEach(element => {
            if (element.name) {
                element.name = element.name.replace("__prefix__", currentFormCount);
            }
            if (element.id) {
                element.id = element.id.replace("__prefix__", currentFormCount);
            }
            element.value = "";
        });
        // Insere a nova linha antes da linha de Total Geral
        const grandTotalRow = document.getElementById("grandTotalRow");
        itensTableBody.insertBefore(newRow, grandTotalRow);
        if (totalFormsInput) {
            totalFormsInput.value = currentFormCount + 1;
        }
        addCalculationListeners(newRow);
        // Configura o botão de exclusão da nova linha
        const deleteBtn = newRow.querySelector(".item-delete");
        if (deleteBtn) {
            deleteBtn.addEventListener("click", function() {
                newRow.remove();
                updateTotalForms();
                updateGrandTotal();
            });
        }
        updateTotalForms();
        updateGrandTotal();
    }

    if (addItemBtn) {
        addItemBtn.addEventListener("click", function() {
            addNewItemRow();
        });
    }
});
