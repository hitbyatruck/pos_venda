document.addEventListener("DOMContentLoaded", function () {
    let equipamentoDeleteUrl = null;

    const confirmModal = document.getElementById("confirmModal");
    const confirmModalBtn = document.getElementById("confirmModalBtn");

    if (!confirmModal || !confirmModalBtn) {
        console.error("Erro: Modal de confirmação ou botão de confirmação não encontrados.");
        return;
    }

    // Inicializa o modal do Bootstrap
    const bsConfirmModal = new bootstrap.Modal(confirmModal);

    // Ao clicar em qualquer botão com a classe "confirm-delete"
    document.querySelectorAll(".confirm-delete").forEach(button => {
        button.addEventListener("click", function () {
            const urlAttr = this.getAttribute("data-url");
            equipamentoDeleteUrl = urlAttr ? urlAttr.trim() : null;
            console.log("URL de exclusão definida:", equipamentoDeleteUrl);
            bsConfirmModal.show();
        });
    });

    // Ao clicar no botão de confirmação do modal
    confirmModalBtn.addEventListener("click", function () {
        if (!equipamentoDeleteUrl) {
            console.error("Erro: URL de exclusão não definida.");
            return;
        }

        // Cria um objeto FormData para enviar o parâmetro force=false
        const formData = new FormData();
        formData.append("force", "false");

        console.log("Enviando requisição de exclusão para:", equipamentoDeleteUrl);
        fetch(equipamentoDeleteUrl, {
            method: "POST",
            body: formData
        })
        .then(response => {
            console.log("Status da resposta:", response.status);
            return response.json();
        })
        .then(data => {
            console.log("Dados retornados:", data);
            if (data.success) {
                window.location.reload();
            } else {
                alert("Erro ao excluir o equipamento: " + data.message);
            }
        })
        .catch(error => {
            console.error("Erro na requisição:", error);
        });

        bsConfirmModal.hide();
    });
});
