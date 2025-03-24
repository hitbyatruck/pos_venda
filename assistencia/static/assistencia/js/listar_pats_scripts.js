document.addEventListener("DOMContentLoaded", function() {
    console.log("Listar PATs JS carregado.");

    // Função para excluir um PAT
    function excluirPat(patId, url) {
        fetch(url, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                document.getElementById(`pat-row-${patId}`).remove();
            } else {
                console.error('Erro ao excluir o PAT.');
            }
        })
        .catch(error => {
            console.error('Erro ao excluir o PAT:', error);
        });
    }

    // Função para obter o CSRF Token dos cookies
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

    // Adiciona evento de clique aos botões de exclusão
    document.querySelectorAll(".pat-delete").forEach(button => {
        button.addEventListener("click", function() {
            const patId = this.getAttribute("data-id");
            const url = this.getAttribute("data-url");
            excluirPat(patId, url);
        });
    });
});