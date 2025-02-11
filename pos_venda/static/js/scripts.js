document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".confirm-delete").forEach(button => {
        button.addEventListener("click", function (event) {
            event.preventDefault();
            let deleteUrl = this.getAttribute("data-url");
            let deleteId = this.getAttribute("data-id");

            let modal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));
            document.getElementById('confirmDeleteBtn').setAttribute("data-url", deleteUrl);
            document.getElementById('confirmDeleteBtn').setAttribute("data-id", deleteId);
            modal.show();
        });
    });

    document.getElementById("confirmDeleteBtn").addEventListener("click", function () {
        let deleteUrl = this.getAttribute("data-url");
        let deleteId = this.getAttribute("data-id");

        fetch(deleteUrl, { method: "POST", headers: { "X-CSRFToken": getCookie("csrftoken") } })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById(`row-${deleteId}`).remove();
                    
                    let modalElement = document.getElementById('confirmDeleteModal');
                    let modal = bootstrap.Modal.getInstance(modalElement);
                    modal.hide(); // Fecha o modal corretamente
                    
                    // Remove a classe 'show' do modal
                    modalElement.classList.remove('show');
                    
                    // Remove a sobreposição escura
                    document.querySelector('.modal-backdrop').remove();
                    
                    // Restaura o scroll e os eventos da página
                    document.body.classList.remove('modal-open');
                    document.body.style.removeProperty('padding-right');
                } else {
                    alert("Erro ao excluir.");
                }
            })
            .catch(error => console.error("Erro:", error));
    });

    // Fecha corretamente o modal ao cancelar
    document.querySelectorAll("[data-bs-dismiss='modal']").forEach(button => {
        button.addEventListener("click", function () {
            let modalElement = document.getElementById('confirmDeleteModal');
            let modal = bootstrap.Modal.getInstance(modalElement);
            modal.hide();
            
            // Remove a sobreposição escura
            document.querySelector('.modal-backdrop').remove();
            
            // Restaura o scroll e os eventos da página
            document.body.classList.remove('modal-open');
            document.body.style.removeProperty('padding-right');
        });
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            document.cookie.split(';').forEach(cookie => {
                let trimmedCookie = cookie.trim();
                if (trimmedCookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(trimmedCookie.substring(name.length + 1));
                }
            });
        }
        return cookieValue;
    }
});

document.addEventListener("DOMContentLoaded", function () {
    document.body.addEventListener("click", function (event) {
        if (event.target.classList.contains("confirm-delete")) {
            event.preventDefault();
            let url = event.target.getAttribute("data-url");
            if (confirm("Tem certeza que deseja excluir este item?")) {
                window.location.href = url;
            }
        }
    });
});

/* document.addEventListener("DOMContentLoaded", function () {
    let modalExclusao = document.getElementById("modalConfirmarExclusao");

    if (modalExclusao) {
        modalExclusao.addEventListener("show.bs.modal", function (event) {
            let button = event.relatedTarget;  // Botão que acionou o modal
            let url = button.getAttribute("data-url");

            // Atualizar o botão de exclusão com a URL correta
            let btnConfirmar = document.getElementById("btnConfirmarExclusao");
            btnConfirmar.setAttribute("href", url);
        });
    }
}); */