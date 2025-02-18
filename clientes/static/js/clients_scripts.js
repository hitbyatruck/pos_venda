document.addEventListener("DOMContentLoaded", function() {
    let clientIdToDelete = null;
    let clientDeleteUrl = "";
    const clientConfirmModalEl = document.getElementById("clientConfirmModal");
    const clientWarningModalEl = document.getElementById("clientWarningModal");

    if (!clientConfirmModalEl || !clientWarningModalEl) {
        console.error("Modais de exclusão de clientes não encontrados.");
        return;
    }
    const clientConfirmModal = new bootstrap.Modal(clientConfirmModalEl);
    const clientWarningModal = new bootstrap.Modal(clientWarningModalEl);

    // Ao clicar nos botões de exclusão (classe "client-delete")
    document.querySelectorAll(".client-delete").forEach(function(button) {
        button.addEventListener("click", function() {
            clientIdToDelete = this.getAttribute("data-id");
            clientDeleteUrl = this.getAttribute("data-url");
            clientConfirmModal.show();
        });
    });

    // Botão "Confirmar" no modal de confirmação inicial
    document.getElementById("clientConfirmModalBtn").addEventListener("click", function() {
        excluirCliente(false);
    });

    // Botão "Confirmar Exclusão" no modal de aviso extra
    document.getElementById("clientWarningModalBtn").addEventListener("click", function() {
        excluirCliente(true);
    });

    function excluirCliente(force) {
        fetch(clientDeleteUrl, {
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
                let row = document.getElementById("client-row-" + clientIdToDelete);
                if (row) {
                    row.remove();
                }
                clientConfirmModal.hide();
                clientWarningModal.hide();
            } else {
                // Se houver mensagem, exibe o modal de aviso extra sem alert()
                if (data.message) {
                    document.getElementById("clientWarningModalBody").textContent = data.message;
                    clientConfirmModal.hide();
                    clientWarningModal.show();
                } else {
                    clientConfirmModal.hide();
                    clientWarningModal.hide();
                }
            }
        })
        .catch(error => {
            console.error("Erro:", error);
            clientConfirmModal.hide();
            clientWarningModal.hide();
        });
    }

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
});
