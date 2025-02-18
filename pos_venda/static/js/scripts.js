document.addEventListener("DOMContentLoaded", function() {
    let equipamentoIdToDelete = null;
    let deleteUrl = null;

    // Obtenha os elementos dos modais (confirme que estes IDs existem no HTML)
    let confirmModalEl = document.getElementById("confirmModal");
    let warningModalEl = document.getElementById("warningModal");

    if (!confirmModalEl || !warningModalEl) {
        console.error("Os modais 'confirmModal' ou 'warningModal' não foram encontrados. Verifique os IDs no template.");
        return;
    }

    // Inicializa os modais via Bootstrap 5
    let confirmModal = new bootstrap.Modal(confirmModalEl);
    let warningModal = new bootstrap.Modal(warningModalEl);

    // Ao clicar em qualquer botão de exclusão (classe "confirm-delete") na listagem:
    document.querySelectorAll(".confirm-delete").forEach(function(button) {
        button.addEventListener("click", function() {
            equipamentoIdToDelete = this.getAttribute("data-id");
            deleteUrl = this.getAttribute("data-url");
            // Exibe o modal de confirmação inicial
            confirmModal.show();
        });
    });

    // Botão "Confirmar" no primeiro modal
    document.getElementById("confirmModalBtn").addEventListener("click", function() {
        excluirEquipamento(false);
    });

    // Botão "Confirmar Exclusão" no modal de aviso extra
    document.getElementById("warningModalBtn").addEventListener("click", function() {
        excluirEquipamento(true);
    });

    function excluirEquipamento(force) {
        fetch(deleteUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({ force: force ? "true" : "false" })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove a linha do equipamento da tabela (assumindo que o <tr> tem id="row-<id>")
                let row = document.getElementById("row-" + equipamentoIdToDelete);
                if (row) {
                    row.remove();
                }
                confirmModal.hide();
                warningModal.hide();
            } else {
                if (!force && data.message) {
                    // Se o equipamento está associado, exibe o segundo modal com o aviso extra
                    document.getElementById("warningModalBody").textContent = data.message;
                    confirmModal.hide();
                    warningModal.show();
                } else {
                    alert("Erro ao excluir: " + data.message);
                    confirmModal.hide();
                    warningModal.hide();
                }
            }
        })
        .catch(error => {
            console.error("Erro:", error);
            confirmModal.hide();
            warningModal.hide();
        });
    }

    function getCSRFToken() {
        let cookieValue = null;
        let cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            if (cookie.startsWith("csrftoken=")) {
                cookieValue = cookie.substring("csrftoken=".length);
                break;
            }
        }
        return cookieValue;
    }
});


document.addEventListener("DOMContentLoaded", function() {
    // Exclusão de Clientes
    let clientDeleteUrl = "";
    let clientIdToDelete = null;
    let clientConfirmModalEl = document.getElementById("clientConfirmModal");
    if (!clientConfirmModalEl) {
        console.error("Modal clientConfirmModal não encontrado!");
        return;
    }
    let clientConfirmModal = new bootstrap.Modal(clientConfirmModalEl);

    // Ao clicar nos botões de exclusão de clientes (classe "client-delete")
    document.querySelectorAll(".client-delete").forEach(function(button) {
        button.addEventListener("click", function() {
            clientIdToDelete = this.getAttribute("data-id");
            clientDeleteUrl = this.getAttribute("data-url");
            clientConfirmModal.show();
        });
    });

    document.getElementById("clientConfirmModalBtn").addEventListener("click", function() {
        // Envia a requisição POST para excluir o cliente
        fetch(clientDeleteUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/x-www-form-urlencoded"
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                let row = document.getElementById("client-row-" + clientIdToDelete);
                if (row) {
                    row.remove();
                }
                clientConfirmModal.hide();
            } else {
                alert("Erro ao excluir cliente: " + data.message);
                clientConfirmModal.hide();
            }
        })
        .catch(error => {
            console.error("Erro:", error);
            clientConfirmModal.hide();
        });
    });

    function getCSRFToken() {
        let cookieValue = null;
        let cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            if (cookie.startsWith("csrftoken=")) {
                cookieValue = cookie.substring("csrftoken=".length);
                break;
            }
        }
        return cookieValue;
    }
});
