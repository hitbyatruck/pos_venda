document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".confirm-delete").forEach(button => {
        button.addEventListener("click", function (event) {
            event.preventDefault();
            let url = this.dataset.url;
            let row = this.closest("tr");

            if (confirm("Tem certeza que deseja excluir este item?")) {
                fetch(url, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCSRFToken()
                    }
                })
                .then(response => response.json())  // Converte resposta para JSON
                .then(data => {
                    if (data.status === "ok") {
                        row.remove();  // Remove a linha da tabela sem recarregar
                    } else {
                        alert("Erro ao excluir: " + (data.error || "Desconhecido"));
                    }
                })
                .catch(error => {
                    alert("Erro ao excluir: " + error.message);
                });
            }
        });
    });
});

// Função para obter o token CSRF
function getCSRFToken() {
    let cookieValue = null;
    let cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.startsWith("csrftoken=")) {
            cookieValue = cookie.substring("csrftoken=".length);
            break;
        }
    }
    return cookieValue;
}
