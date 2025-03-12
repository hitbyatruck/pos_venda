document.addEventListener("DOMContentLoaded", function () {
    let equipamentoDeleteUrl = null;

    const confirmDeleteModalEl = document.getElementById("confirmModal");
    const confirmDeleteEquipamentoBtn = document.getElementById("confirmModalBtn");

    if (!confirmDeleteModalEl || !confirmDeleteEquipamentoBtn) {
        console.error("Erro: Modal ou botão de exclusão do equipamento não encontrados.");
        return;
    }

    const confirmDeleteModal = new bootstrap.Modal(confirmDeleteModalEl);

    document.querySelectorAll(".confirm-delete").forEach(button => {
        button.addEventListener("click", function () {
            equipamentoDeleteUrl = this.getAttribute("data-url");
            confirmDeleteModal.show();
        });
    });

    confirmDeleteEquipamentoBtn.addEventListener("click", function () {
        if (!equipamentoDeleteUrl) {
            console.error("Erro: URL de exclusão não definida.");
            return;
        }

        fetch(equipamentoDeleteUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/x-www-form-urlencoded"
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert("Erro ao excluir o equipamento.");
            }
        })
        .catch(error => {
            console.error("Erro ao excluir o equipamento:", error);
        });

        confirmDeleteModal.hide();
    });

    function getCSRFToken() {
        return document.cookie.split("; ").find(row => row.startsWith("csrftoken="))?.split("=")[1];
    }
});
