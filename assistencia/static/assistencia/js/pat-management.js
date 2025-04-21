document.addEventListener('DOMContentLoaded', function() {
    // Status change button handler
    const actionButtons = document.querySelectorAll('.action-btn');

    actionButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.dataset.action;
            const patId = this.dataset.id;

            if (action === 'change-status') {
                // Handle status change
                const modal = new bootstrap.Modal(document.getElementById('changeStatusModal'));
                document.getElementById('statusChangePATId').value = patId;

                // Get current status (optional)
                const currentStatus = this.closest('tr').querySelector('td:nth-child(6) .badge').textContent.trim();

                // Update modal title with PAT number
                const patNumber = this.closest('tr').querySelector('td:nth-child(1)').textContent.trim();
                document.getElementById('changeStatusModalLabel').textContent = `Alterar Status da PAT #${patNumber}`;

                modal.show();
            } else if (action === 'delete') {
                // Handle delete
                if (confirm(`Tem certeza que deseja excluir a PAT #${patId}?`)) {
                    // Send delete request
                    fetch(`/assistencia/excluir/${patId}/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Remove row or refresh page
                            window.location.reload();
                        } else {
                            alert(`Erro ao excluir: ${data.message}`);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert(`Erro ao processar solicitação: ${error}`);
                    });
                }
            }
        });
    });

    // Status change form submission
    document.getElementById('confirmStatusChange').addEventListener('click', function() {
        const form = document.getElementById('statusChangeForm');
        const patId = document.getElementById('statusChangePATId').value;
        const newStatus = document.getElementById('newStatus').value;
        const note = document.getElementById('statusChangeNote').value;

        // Send status change request
        fetch(`/assistencia/mudar-status/${patId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                new_status: newStatus,
                note: note
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close modal and refresh page
                bootstrap.Modal.getInstance(document.getElementById('changeStatusModal')).hide();
                window.location.reload();
            } else {
                alert(`Erro ao mudar status: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Erro ao processar solicitação: ${error}`);
        });
    });

    // Helper function to get CSRF token
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
});
