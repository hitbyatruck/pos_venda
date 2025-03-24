/**
 * Handles deassociation of equipment from clients.
 * Used in the client management interface.
 * This will only remove the link between equipment and client.
 */

document.addEventListener("DOMContentLoaded", function() {
    // Initialize Bootstrap modals
    const confirmModal = new bootstrap.Modal(document.getElementById("confirmModal"));
    const warningModal = new bootstrap.Modal(document.getElementById("warningModal"));
    
    let equipamentoIdToDelete = null;
    let deleteUrl = null;

    // Function to clean up modal artifacts
    function cleanupModals() {
        // Hide modals
        confirmModal.hide();
        warningModal.hide();
        
        // Remove backdrop if it exists
        const backdrops = document.getElementsByClassName('modal-backdrop');
        while(backdrops.length > 0) {
            backdrops[0].remove();
        }
        
        // Clean up body
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('padding-right');
        document.body.style.removeProperty('overflow');
    }

    // Add click handlers to all deassociate buttons
    document.querySelectorAll(".deassociate-equipment").forEach(button => {
        button.addEventListener("click", function(e) {
            e.preventDefault();
            equipamentoIdToDelete = this.getAttribute("data-id");
            deleteUrl = this.getAttribute("data-url");
            confirmModal.show();
        });
    });

    // Handle cancel buttons on both modals
    document.querySelectorAll('[data-bs-dismiss="modal"]').forEach(button => {
        button.addEventListener('click', cleanupModals);
    });

    // Confirm button in first modal
    document.getElementById("confirmModalBtn")?.addEventListener("click", function() {
        desassociarEquipamento(false);
    });

    // Warning modal confirm button
    document.getElementById("warningModalBtn")?.addEventListener("click", function() {
        desassociarEquipamento(true);
    });

    function desassociarEquipamento(force = false) {
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
                const row = document.getElementById(`equipment-row-${equipamentoIdToDelete}`);
                if (row) {
                    row.remove();
                    cleanupModals();
                    
                    // Also remove associated PAT rows if they exist
                    if (data.removedPats) {
                        data.removedPats.forEach(patId => {
                            const patRow = document.getElementById(`pat-row-${patId}`);
                            if (patRow) patRow.remove();
                        });
                    }
                } else {
                    window.location.reload();
                }
            } else if (data.status === 'warning' && data.requireForce) {
                document.getElementById("warningModalBody").textContent = data.message;
                confirmModal.hide();
                warningModal.show();
            } else {
                alert(data.message);
                cleanupModals();
            }
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Erro ao desassociar equipamento: " + error);
            cleanupModals();
        });
    }

    function getCSRFToken() {
        const name = "csrftoken";
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Handle ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            cleanupModals();
        }
    });
});