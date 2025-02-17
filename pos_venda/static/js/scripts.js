document.addEventListener("DOMContentLoaded", function() {
    let equipamentoIdToDelete = null;
    let deleteUrl = null;

    // Obter os elementos dos modais (confirme que estes IDs estão definidos em seus templates)
    let confirmModalEl = document.getElementById('confirmModal');
    let warningModalEl = document.getElementById('warningModal');

    if (!confirmModalEl || !warningModalEl) {
        console.error("Os modais 'confirmModal' ou 'warningModal' não foram encontrados no DOM.");
        return;
    }

    // Inicializa os modais (Bootstrap 5)
    let confirmModal = new bootstrap.Modal(confirmModalEl);
    let warningModal = new bootstrap.Modal(warningModalEl);

    // Ao clicar no botão de exclusão (os botões devem ter a classe "confirm-delete")
    document.querySelectorAll('.confirm-delete').forEach(function(button) {
        button.addEventListener('click', function() {
            equipamentoIdToDelete = this.getAttribute('data-id');
            deleteUrl = this.getAttribute('data-url');
            confirmModal.show();
        });
    });

    // Botão "Confirmar" no primeiro modal
    document.getElementById('confirmModalBtn').addEventListener('click', function() {
        excluirEquipamento(false);
    });

    // Botão "Confirmar Exclusão" no modal de aviso extra
    document.getElementById('warningModalBtn').addEventListener('click', function() {
        excluirEquipamento(true);
    });

    function excluirEquipamento(force) {
        fetch(deleteUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({ force: force ? "true" : "false" })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove a linha do equipamento da tabela, assumindo que ela possui ID "row-<equipamentoId>"
                let row = document.getElementById('row-' + equipamentoIdToDelete);
                if (row) {
                    row.remove();
                }
                confirmModal.hide();
                warningModal.hide();
            } else {
                if (!force && data.message) {
                    // Exibe o segundo modal com o aviso extra
                    document.getElementById('warningModalBody').textContent = data.message;
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
