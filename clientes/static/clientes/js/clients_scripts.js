document.addEventListener("DOMContentLoaded", function () {
    let clientIdToDelete = null;
    let clientDeleteUrl = null;

    const clientConfirmModalEl = document.getElementById("clientConfirmModal");
    const clientConfirmModalBtn = document.getElementById("clientConfirmModalBtn");
    const clientWarningModalEl = document.getElementById("clientWarningModal");
    const clientWarningModalBody = document.getElementById("clientWarningModalBody");
    const clientWarningModalBtn = document.getElementById("clientWarningModalBtn");

    if (!clientConfirmModalEl || !clientConfirmModalBtn || !clientWarningModalEl || !clientWarningModalBtn) {
        console.error("Erro: Modais de exclusão do cliente não encontrados.");
        return;
    }

    const clientConfirmModal = new bootstrap.Modal(clientConfirmModalEl);
    const clientWarningModal = new bootstrap.Modal(clientWarningModalEl);

    document.querySelectorAll(".confirm-delete").forEach(button => {
        button.addEventListener("click", function () {
            clientIdToDelete = this.getAttribute("data-id");
            clientDeleteUrl = this.getAttribute("data-url");
            clientConfirmModal.show();
        });
    });

    clientConfirmModalBtn.addEventListener("click", function () {
        if (!clientDeleteUrl) {
            console.error("Erro: URL de exclusão não definida.");
            return;
        }

        fetch(clientDeleteUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({ force: "false" })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById("client-row-" + clientIdToDelete).remove();
                clientConfirmModal.hide();
            } else {
                // Se a resposta do servidor indicar que há associações, mostrar o modal de aviso
                if (data.message) {
                    clientWarningModalBody.textContent = data.message;
                    clientConfirmModal.hide();
                    clientWarningModal.show();
                } else {
                    alert("Erro ao excluir o cliente.");
                }
            }
        })
        .catch(error => {
            console.error("Erro ao excluir o cliente:", error);
            alert("Erro ao excluir o cliente.");
        });

        clientConfirmModal.hide();
    });

    clientWarningModalBtn.addEventListener("click", function () {
        fetch(clientDeleteUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({ force: "true" })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById("client-row-" + clientIdToDelete).remove();
                clientWarningModal.hide();
            } else {
                alert("Erro ao excluir o cliente.");
            }
        })
        .catch(error => {
            console.error("Erro ao excluir o cliente:", error);
            alert("Erro ao excluir o cliente.");
        });

        clientWarningModal.hide();
    });

    function getCSRFToken() {
        let csrfToken = document.querySelector("meta[name='csrf-token']");
        return csrfToken ? csrfToken.getAttribute("content") : "";
    }
});
