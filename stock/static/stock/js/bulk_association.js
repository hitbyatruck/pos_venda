/**
 * Configura os handlers para associação em massa entre peças e fornecedores
 */
function setupBulkAssociationHandlers() {
    const bulkAssociationForm = document.getElementById('bulkAssociationForm');
    
    if (bulkAssociationForm) {
        // Handler para seleção de múltiplas peças
        const selectAllParts = document.getElementById('selectAllParts');
        if (selectAllParts) {
            selectAllParts.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('.part-checkbox');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = this.checked;
                });
            });
        }
        
        // Handler para submissão do formulário de associação em massa
        bulkAssociationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const selectedParts = Array.from(
                document.querySelectorAll('.part-checkbox:checked')
            ).map(checkbox => checkbox.value);
            
            const fornecedorId = document.getElementById('bulk_fornecedor_id').value;
            const referenciaFornecedor = document.getElementById('bulk_referencia_fornecedor').value;
            const precoUnitario = document.getElementById('bulk_preco_unitario').value;
            
            if (selectedParts.length === 0) {
                alert('Por favor, selecione pelo menos uma peça.');
                return;
            }
            
            // Dados para enviar ao servidor
            const data = {
                partes_ids: selectedParts,
                fornecedor_id: fornecedorId,
                referencia_fornecedor: referenciaFornecedor,
                preco_unitario: precoUnitario,
                tempo_entrega: document.getElementById('bulk_tempo_entrega').value,
                fornecedor_preferencial: document.getElementById('bulk_fornecedor_preferencial').checked,
                notas: document.getElementById('bulk_notas').value
            };
            
            // Enviar os dados via AJAX
            fetch('/stock/associar-pecas-fornecedor/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Associação em massa realizada com sucesso!');
                    window.location.reload();
                } else {
                    alert('Erro ao realizar associação: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Ocorreu um erro ao processar a requisição.');
            });
        });
    }
}

// Adicionar a chamada à função setupBulkAssociationHandlers no evento DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    // Funções existentes
    setupPecaFornecedoresHandlers();
    setupFornecedorPecasHandlers();
    
    // Nova função para associação em massa
    setupBulkAssociationHandlers();
});