document.addEventListener("DOMContentLoaded", function () {
    let confirmDeleteButtons = document.querySelectorAll(".confirm-delete");
    let confirmDeleteModal = document.getElementById("confirmDeleteModal");
    let confirmDeleteButton = document.getElementById("confirmDeleteButton");
    let warningDeleteModal = document.getElementById("warningDeleteModal");
    let deleteUrl = "";

    if (!warningDeleteModal) {
        console.error("Erro: Modal warningDeleteModal não foi encontrado!");
    }

    if (confirmDeleteButtons.length > 0 && confirmDeleteModal) {
        confirmDeleteButtons.forEach(button => {
            button.addEventListener("click", function () {
                deleteUrl = this.getAttribute("data-url");

                console.log("Verificando se o cliente tem equipamentos associados...");

                fetch(deleteUrl + "?verificar=1", { method: "GET" })
                .then(response => response.json())
                .then(data => {
                    if (data.tem_equipamentos) {
                        console.log("Cliente tem equipamentos! Abrindo warningDeleteModal...");
                        let modalInstance = new bootstrap.Modal(warningDeleteModal);
                        modalInstance.show();
                    } else {
                        console.log("Cliente não tem equipamentos. Mostrando modal de confirmação.");
                        let modalInstance = new bootstrap.Modal(confirmDeleteModal);
                        modalInstance.show();
                    }
                })
                .catch(error => console.error("Erro ao verificar cliente:", error));
            });
        });

        confirmDeleteButton.addEventListener("click", function () {
            if (deleteUrl) {
                fetch(deleteUrl, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCSRFToken(),
                        "Content-Type": "application/json"
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert(data.message || "Erro ao excluir o cliente.");
                    }
                })
                .catch(error => console.error("Erro:", error));
            }
        });
    }
});

function getCSRFToken() {
    let cookieValue = null;
    let cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.startsWith("csrftoken=")) {
            cookieValue = cookie.substring("csrftoken=".length, cookie.length);
            break;
        }
    }
    return cookieValue;
}


