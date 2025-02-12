document.addEventListener("DOMContentLoaded", function () {
    // Captura os botões "Excluir" e associa ao modal
    document.querySelectorAll(".confirm-delete").forEach(button => {
        button.addEventListener("click", function () {
            const deleteUrl = this.getAttribute("data-url");  // Obtém a URL correta da exclusão
            document.getElementById("confirmDeleteBtn").setAttribute("href", deleteUrl);
        });
    });

    // Fecha o modal corretamente após a exclusão
    document.getElementById("confirmDeleteBtn").addEventListener("click", function (event) {
        event.preventDefault();
        const deleteUrl = this.getAttribute("href");

        fetch(deleteUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/json"
            }
        }).then(response => {
            if (response.ok) {
                location.reload();  // Atualiza a página após a exclusão
            } else {
                alert("Erro ao excluir o item.");
            }
        }).catch(error => console.error("Erro:", error));
    });

    // Função para obter o CSRF Token do cookie
    function getCSRFToken() {
        const cookieValue = document.cookie.match(/csrftoken=([^;]+)/);
        return cookieValue ? cookieValue[1] : "";
    }
});
