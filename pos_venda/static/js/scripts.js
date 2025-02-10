document.addEventListener("DOMContentLoaded", function () {
    // Confirmação antes de excluir qualquer item
    document.querySelectorAll(".confirm-delete").forEach(button => {
        button.addEventListener("click", function (event) {
            event.preventDefault();
            if (confirm("Tem certeza que deseja excluir este item?")) {
                this.closest("form").submit();
            }
        });
    });
});