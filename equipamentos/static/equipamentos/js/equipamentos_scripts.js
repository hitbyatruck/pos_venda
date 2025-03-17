document.addEventListener("DOMContentLoaded", function () {
    function getCSRFToken() {
        let cookieValue = null;
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            if (cookie.startsWith("csrftoken=")) {
                cookieValue = cookie.substring("csrftoken=".length);
                break;
            }
        }
        return cookieValue;
    }

    // Excluir PATs na aba "Pedidos de Assistência"
    document.querySelectorAll(".pat-delete").forEach(function (button) {
        button.addEventListener("click", function () {
            if (!confirm("Tem certeza que deseja excluir esta PAT?")) {
                return;
            }
            let patId = this.getAttribute("data-id");
            let url = this.getAttribute("data-url");

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    let row = document.getElementById("pat-row-" + patId);
                    if (row) {
                        row.remove();
                    }
                } else {
                    alert(data.message || "Erro ao excluir a PAT.");
                }
            })
            .catch(error => {
                console.error("Erro ao excluir PAT:", error);
            });
        });
    });

    // Exclusão de Equipamentos
    let equipamentoDeleteUrl = null;
    const confirmModal = document.getElementById("confirmModal");
    const confirmModalBtn = document.getElementById("confirmModalBtn");

    if (confirmModal && confirmModalBtn) {
        const bsConfirmModal = new bootstrap.Modal(confirmModal);

        document.querySelectorAll(".confirm-delete").forEach(button => {
            button.addEventListener("click", function () {
                equipamentoDeleteUrl = this.getAttribute("data-url").trim();
                console.log("URL de exclusão definida:", equipamentoDeleteUrl);
                bsConfirmModal.show();
            });
        });

        confirmModalBtn.addEventListener("click", function () {
            if (!equipamentoDeleteUrl) {
                console.error("Erro: URL de exclusão não definida.");
                return;
            }

            fetch(equipamentoDeleteUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken()
                },
                body: new URLSearchParams({'force': 'false'})
            })
            .then(response => response.json())
            .then(data => {
                console.log("Resposta da exclusão:", data);
                if (data.success) {
                    window.location.href = data.redirect_url;
                } else {
                    alert("Erro ao excluir o equipamento: " + data.message);
                }
            })
            .catch(error => {
                console.error("Erro ao excluir o equipamento:", error);
            });

            bsConfirmModal.hide();
        });
    }

    // Abrir automaticamente a aba "Notas" caso a URL contenha "#notas"
    if (window.location.hash === "#notas") {
        var notasTabTrigger = document.querySelector('a[data-bs-toggle="tab"][href="#notas"]');
        if (notasTabTrigger) {
            var tab = new bootstrap.Tab(notasTabTrigger);
            tab.show();
        }
    }
});

