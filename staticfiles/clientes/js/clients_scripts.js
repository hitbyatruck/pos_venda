/**
 * Handles client management operations including:
 * - Client deletion with dependency checks
 * - Modal management for client operations
 * - CSRF token handling for client requests
 */

document.addEventListener("DOMContentLoaded", function() {
    console.log("clients_scripts.js loaded");

    // Initialize variables
    let clientIdToDelete = null;
    let clientDeleteUrl = null;

    // Initialize modals
    const clientConfirmModalEl = document.getElementById("clientConfirmModal");
    const clientWarningModalEl = document.getElementById("clientWarningModal");
    
    if (!clientConfirmModalEl || !clientWarningModalEl) {
        console.error("Client deletion modals not found");
        return;
    }

    const clientConfirmModal = new bootstrap.Modal(clientConfirmModalEl);
    const clientWarningModal = new bootstrap.Modal(clientWarningModalEl);

    // Delete button click handler
    document.addEventListener("click", function(event) {
        const deleteBtn = event.target.closest(".client-delete");
        if (deleteBtn) {
            event.preventDefault();
            clientIdToDelete = deleteBtn.getAttribute("data-id");
            clientDeleteUrl = deleteBtn.getAttribute("data-url");
            console.log("Delete requested for client:", clientIdToDelete);
            clientConfirmModal.show();
        }
    });

    // Initial confirmation button handler
    document.getElementById("clientConfirmModalBtn").addEventListener("click", function() {
        console.log("Initial confirmation for client:", clientIdToDelete);
        excluirCliente(false);
    });

    // Warning confirmation button handler
    document.getElementById("clientWarningModalBtn").addEventListener("click", function() {
        console.log("Force delete confirmation for client:", clientIdToDelete);
        excluirCliente(true);
    });

    function excluirCliente(force) {
        console.log(`Attempting to delete client ${clientIdToDelete} (force: ${force})`);
        
        fetch(clientDeleteUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({ force: force ? "true" : "false" })
        })
        .then(response => response.json())
        .then(data => {
            console.log("Server response:", data);
            if (data.success) {
                const row = document.getElementById(`client-row-${clientIdToDelete}`);
                if (row) {
                    row.remove();
                }
                clientConfirmModal.hide();
                clientWarningModal.hide();
            } else if (data.has_dependencies) {
                document.getElementById("clientWarningModalBody").textContent = data.message;
                clientConfirmModal.hide();
                clientWarningModal.show();
            } else {
                throw new Error(data.message || "Erro ao excluir cliente");
            }
        })
        .catch(error => {
            console.error("Error:", error);
            alert(error.message);
            clientConfirmModal.hide();
            clientWarningModal.hide();
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
});

$(document).ready(function() {
    // Script para mostrar/ocultar campos de endereço quando checkbox mudar
    function toggleAddressFields() {
        var useCompanyAddress = $('#id_endereco_igual_empresa').is(':checked');
        var companySelected = $('#id_empresa').val() !== '';
        
        if (useCompanyAddress && companySelected) {
            $('#id_morada, #id_codigo_postal, #id_localidade, #id_cidade, #id_pais').closest('.col-md-12, .col-md-4').fadeOut();
        } else {
            $('#id_morada, #id_codigo_postal, #id_localidade, #id_cidade, #id_pais').closest('.col-md-12, .col-md-4').fadeIn();
        }
    }
    
    // Inicializar campos
    toggleAddressFields();
    
    // Adicionar event listeners
    $('#id_endereco_igual_empresa, #id_empresa').change(function() {
        toggleAddressFields();
    });
    
    // Manter a aba ativa após submit com erro
    var activeTab = sessionStorage.getItem('activeClienteTab');
    if (activeTab) {
        $('#clienteTabs button[data-bs-target="' + activeTab + '"]').tab('show');
    }
    
    // Salvar aba ativa quando trocar
    $('#clienteTabs button').on('shown.bs.tab', function (e) {
        var target = $(e.target).data('bs-target');
        sessionStorage.setItem('activeClienteTab', target);
    });
});