document.addEventListener("DOMContentLoaded", function () {
    let confirmDeleteButtons = document.querySelectorAll(".confirm-delete");
    let confirmDeleteModal = document.getElementById("confirmDeleteModal");
    let confirmDeleteButton = document.getElementById("confirmDeleteButton");
    let deleteUrl = "";

    if (confirmDeleteButtons.length > 0 && confirmDeleteModal) {
        confirmDeleteButtons.forEach(button => {
            button.addEventListener("click", function () {
                deleteUrl = this.getAttribute("data-url");
                let modal = new bootstrap.Modal(confirmDeleteModal);
                modal.show();
            });
        });

        confirmDeleteButton.addEventListener("click", function () {
            console.log(deleteUrl);
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
                        let currentPage = window.location.pathname;

                        // Se estiver na página de detalhes do equipamento, redireciona para a lista
                        if (currentPage.includes("/equipamentos/") && !currentPage.includes("lista")) {
                            window.location.href = "/equipamentos/fabricados/lista/";
                        } else {
                            location.reload();
                        }
                    } else {
                        alert("Erro ao excluir o item.");
                    }
                })
                .catch(error => console.error("Erro:", error));
            }
        });
    }
});

document.addEventListener("DOMContentLoaded", function () {
    let confirmDeleteModal = document.getElementById("confirmDeleteModal");

    if (confirmDeleteModal) {
        confirmDeleteModal.addEventListener("hidden.bs.modal", function () {
            let backdrop = document.querySelector(".modal-backdrop");
            if (backdrop) {
                backdrop.remove(); // Remove o fundo escurecido
            }
            document.body.classList.remove("modal-open"); // Garante que a rolagem volta ao normal
            document.body.style.overflow = "auto"; // Se necessário, força a rolagem normal
        });
    }
});


function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute("content");
}
