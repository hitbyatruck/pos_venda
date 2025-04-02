/**
 * JavaScript para gestão da associação entre peças e fornecedores
 */
document.addEventListener('DOMContentLoaded', function() {
    // Funções para a página de detalhes da peça
    setupPecaFornecedoresHandlers();
    
    // Funções para a página de detalhes do fornecedor
    setupFornecedorPecasHandlers();
});

/**
 * Configura os handlers para a página de detalhes da peça
 */
function setupPecaFornecedoresHandlers() {
    // Editar associação fornecedor-peça
    const editButtons = document.querySelectorAll('.edit-fornecedor');
    if (editButtons) {
        editButtons.forEach(button => {
            button.addEventListener('click', function() {
                const fornecedorPecaId = this.getAttribute('data-fornecedor-peca-id');
                const formAction = document.getElementById('editarFornecedorForm').getAttribute('data-base-url').replace('0', fornecedorPecaId);
                document.getElementById('editarFornecedorForm').action = formAction;
                
                // Carregar dados via AJAX
                fetch(`/stock/fornecedor-peca/${fornecedorPecaId}/api/`)
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('edit_fornecedor_nome').value = data.fornecedor_nome;
                        document.getElementById('edit_referencia_fornecedor').value = data.referencia_fornecedor;
                        document.getElementById('edit_preco_unitario').value = data.preco_unitario;
                        document.getElementById('edit_tempo_entrega').value = data.tempo_entrega || '';
                        document.getElementById('edit_fornecedor_preferencial').checked = data.fornecedor_preferencial;
                        document.getElementById('edit_notas').value = data.notas || '';
                    })
                    .catch(error => console.error('Erro ao carregar dados:', error));
            });
        });
    }
    
    // Excluir associação
    const deleteButtons = document.querySelectorAll('.delete-fornecedor');
    if (deleteButtons) {
        deleteButtons.forEach(button => {
            button.addEventListener('click', function() {
                const fornecedorPecaId = this.getAttribute('data-fornecedor-peca-id');
                const formAction = document.getElementById('confirmarExclusaoForm').getAttribute('data-base-url').replace('0', fornecedorPecaId);
                document.getElementById('confirmarExclusaoForm').action = formAction;
                
                // Carregar dados via AJAX
                fetch(`/stock/fornecedor-peca/${fornecedorPecaId}/api/`)
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('delete_fornecedor_nome').textContent = data.fornecedor_nome;
                        document.getElementById('delete_referencia_fornecedor').textContent = data.referencia_fornecedor;
                    })
                    .catch(error => console.error('Erro ao carregar dados:', error));
            });
        });
    }
}

/**
 * Configura os handlers para a página de detalhes do fornecedor
 */
function setupFornecedorPecasHandlers() {
    // Implementação similar à setupPecaFornecedoresHandlers, 
    // mas para a perspectiva do fornecedor
}