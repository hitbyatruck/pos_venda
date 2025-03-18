document.addEventListener("DOMContentLoaded", function() {
    console.log("assistencia_scripts.js carregado.");

    /* ========================================================
       Atualização do Dropdown de Equipamentos (baseado no Cliente)
       ======================================================== */
    const clienteSelect = document.getElementById("id_cliente");
    const equipamentoSelect = document.getElementById("id_equipamento");
    const preselectedEquipamento = equipamentoSelect ? equipamentoSelect.value : "";

    function updateEquipamentoDropdown(clienteId, selectedEquipId) {
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
                if (selectedEquipId) {
                    for (let opt of equipamentoSelect.options) {
                        if (opt.value === selectedEquipId) {
                            opt.selected = true;
                            break;
                        }
                    }
                }
                console.log("Dropdown Equipamento atualizado.");
            })
            .catch(error => {
                console.error("Erro ao buscar equipamentos:", error);
                equipamentoSelect.innerHTML = '<option value="">Erro ao carregar equipamentos</option>';
            });
    }

    if (clienteSelect && equipamentoSelect) {
        clienteSelect.addEventListener("change", function() {
            console.log("Cliente selecionado (change event):", this.value);
            updateEquipamentoDropdown(this.value, "");
        });
        if (clienteSelect.value) {
            updateEquipamentoDropdown(clienteSelect.value, preselectedEquipamento);
        }
    } else {
        console.error("Dropdowns de Cliente ou Equipamento não encontrados!");
    }

    /* ========================================================
       Manipulação da Tabela de Itens e Atualização dos Totais
       ======================================================== */
    const addItemBtn = document.getElementById("addItemBtn");
    const totalFormsInput = document.getElementById("id_itens-TOTAL_FORMS");
    const itensTableBody = document.querySelector("#itensTable tbody");
    const grandTotalElem = document.getElementById("grandTotalValue");
    const templateRow = itensTableBody.querySelector("tr.template-row");

    if (!templateRow) {
        console.error("Linha template não encontrada. Certifique-se de que há uma linha com a classe 'template-row' oculta na tabela.");
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
        if (quantidadeInput) {
            quantidadeInput.addEventListener("input", function() {
                this.setCustomValidity("");
                updateRowTotal(row);
            });
        }
        if (precoInput) {
            precoInput.addEventListener("input", function() {
                this.setCustomValidity("");
                updateRowTotal(row);
            });
        }
        if (tipoField) {
            tipoField.addEventListener("change", function() {
                this.setCustomValidity("");
            });
        }
        if (referenciaField) {
            referenciaField.addEventListener("input", function() {
                this.setCustomValidity("");
            });
        }
        if (designacaoField) {
            designacaoField.addEventListener("input", function() {
                this.setCustomValidity("");
            });
        }
    }

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

    if (addItemBtn) {
        addItemBtn.addEventListener("click", function() {
            addNewItemRow();
        });
    } else {
        console.error("Botão 'Adicionar Item' não encontrado.");
    }

    /* ========================================================
       Validação no Submit: Remoção de linhas vazias e verificação de preenchimento parcial
       ======================================================== */
    const patForm = document.getElementById("patForm");
    if (patForm) {
        patForm.addEventListener("submit", function(event) {
            let invalidRowFound = false;
            const itemRows = itensTableBody.querySelectorAll("tr.item-row:not(.template-row)");
            // Limpa customValidity de todos os campos
            itemRows.forEach(row => {
                row.querySelectorAll("input, select").forEach(field => {
                    field.setCustomValidity("");
                });
            });
            itemRows.forEach(row => {
                const tipoField = row.querySelector("[name*='-tipo']");
                const referenciaField = row.querySelector("[name*='-referencia']");
                const designacaoField = row.querySelector("[name*='-designacao']");
                const quantidadeField = row.querySelector("input.quantidade");
                const precoField = row.querySelector("input.preco");

                let tipo = tipoField ? tipoField.value.trim() : "";
                let referencia = referenciaField ? referenciaField.value.trim() : "";
                let designacao = designacaoField ? designacaoField.value.trim() : "";
                let quantidade = quantidadeField ? quantidadeField.value.trim() : "";
                let preco = precoField ? precoField.value.trim() : "";

                // Se todos os campos estiverem vazios, remova a linha
                if ((tipoField ? tipo === "" : true) &&
                    (referenciaField ? referencia === "" : true) &&
                    (designacaoField ? designacao === "" : true) &&
                    (quantidadeField ? quantidade === "" : true) &&
                    (precoField ? preco === "" : true)) {
                    row.remove();
                }
                // Se houver preenchimento parcial, defina customValidity para os campos vazios
                else if ((tipoField && tipo === "") ||
                         (referenciaField && referencia === "") ||
                         (designacaoField && designacao === "") ||
                         (quantidadeField && quantidade === "") ||
                         (precoField && preco === "")) {
                    invalidRowFound = true;
                    if (tipoField && tipo === "") {
                        tipoField.setCustomValidity("Preencha todos os campos ou Exclua a linha");
                        tipoField.reportValidity();
                    }
                    if (referenciaField && referencia === "") {
                        referenciaField.setCustomValidity("Preencha todos os campos ou Exclua a linha");
                        referenciaField.reportValidity();
                    }
                    if (designacaoField && designacao === "") {
                        designacaoField.setCustomValidity("Preencha todos os campos ou Exclua a linha");
                        designacaoField.reportValidity();
                    }
                    if (quantidadeField && quantidade === "") {
                        quantidadeField.setCustomValidity("Preencha todos os campos ou Exclua a linha");
                        quantidadeField.reportValidity();
                    }
                    if (precoField && preco === "") {
                        precoField.setCustomValidity("Preencha todos os campos ou Exclua a linha");
                        precoField.reportValidity();
                    }
                }
            });
            updateTotalForms();
            if (invalidRowFound) {
                event.preventDefault();
                patForm.reportValidity();
            }
        });
    }
});


document.addEventListener("DOMContentLoaded", function() {
    console.log("assistencia_scripts.js carregado corretamente!");

    function getCSRFToken() {
        let cookieValue = null;
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith("csrftoken=")) {
                cookieValue = cookie.substring("csrftoken=".length);
                break;
            }
        }
        return cookieValue;
    }

    let patIdToDelete = null;
    let patDeleteUrl = null;
    const patConfirmModalEl = document.getElementById("patConfirmModal");
    const patConfirmModal = new bootstrap.Modal(patConfirmModalEl);

    // Adiciona o evento a todos os botões de exclusão dinâmicamente
    document.body.addEventListener("click", function(event) {
        if (event.target.classList.contains("pat-delete")) {
            patIdToDelete = event.target.getAttribute("data-id");
            patDeleteUrl = event.target.getAttribute("data-url");
            console.log("Solicitando exclusão para PAT id:", patIdToDelete);
            patConfirmModal.show();
        }
    });

    document.getElementById("patConfirmModalBtn").addEventListener("click", function() {
        console.log("Confirmando exclusão para PAT id:", patIdToDelete);
        fetch(patDeleteUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: ""
        })
        .then(response => response.json())
        .then(data => {
            console.log("Resposta da exclusão:", data);
            if (data.success) {
                const row = document.getElementById("pat-row-" + patIdToDelete);
                if (row) {
                    row.remove();
                }
                patConfirmModal.hide();
            } else {
                alert(data.message || "Erro ao excluir a PAT.");
                patConfirmModal.hide();
            }
        })
        .catch(error => {
            console.error("Erro na exclusão:", error);
            patConfirmModal.hide();
        });
    });
});



