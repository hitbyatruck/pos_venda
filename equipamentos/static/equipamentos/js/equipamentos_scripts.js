/**
 * Handles complete deletion of equipment from the system.
 * Used in the equipment management interface.
 * This will permanently delete the equipment and all its associations.
 */

document.addEventListener("DOMContentLoaded", function() {
    let equipamentoIdToDelete = null;
    let deleteUrl = null;

    // Initialize Bootstrap modals
    const confirmModal = new bootstrap.Modal(document.getElementById("confirmModal"));
    const warningModal = new bootstrap.Modal(document.getElementById("warningModal"));

    // Delete button click handlers
    document.querySelectorAll(".confirm-delete").forEach(function(button) {
        button.addEventListener("click", function(e) {
            e.preventDefault();
            equipamentoIdToDelete = this.getAttribute("data-id");
            deleteUrl = this.getAttribute("data-url");
            confirmModal.show();
        });
    });

    // Confirm button in first modal
    document.getElementById("confirmModalBtn")?.addEventListener("click", function() {
        excluirEquipamento(false);
    });

    // Warning modal confirm button
    document.getElementById("warningModalBtn")?.addEventListener("click", function() {
        excluirEquipamento(true);
    });

    function excluirEquipamento(force = false) {
        const url = force ? `${deleteUrl}?force=true` : deleteUrl;
        
        fetch(url, {
            method: "DELETE",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/json"
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const row = document.getElementById(`row-${equipamentoIdToDelete}`);
                if (row) {
                    row.remove();
                    confirmModal.hide();
                    warningModal.hide();
                    
                } else {
                    console.warn(`Row with id row-${equipamentoIdToDelete} not found`);
                    window.location.reload(); // Fallback: refresh the page
                }
            } else if (data.status === 'warning' && data.requireForce) {
                document.getElementById("warningModalBody").textContent = data.message;
                confirmModal.hide();
                warningModal.show();
            } else {
                alert(data.message);
                confirmModal.hide();
                warningModal.hide();
            }
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Erro ao excluir equipamento: " + error);
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