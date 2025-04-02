/**
 * Gerencia a listagem de clientes e funcionalidades associadas
 */
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar variáveis e elementos
    const btnFiltrosToggle = document.querySelector('.btn-filtros-toggle');
    const colunaFiltros = document.querySelector('.col-lg-3');
    
    // Função para alternar entre vistas
    const alternarVistas = function() {
        const btnVisualizacao = document.getElementById('btn-visualizacao');
        const vistaLista = document.getElementById('vista-lista');
        const vistaCards = document.getElementById('vista-cards');
        
        if (btnVisualizacao) {
            btnVisualizacao.addEventListener('click', function() {
                if (vistaLista.style.display !== 'none') {
                    vistaLista.style.display = 'none';
                    vistaCards.style.display = 'flex';
                    this.innerHTML = '<i class="fas fa-table"></i>';
                    localStorage.setItem('clientesVista', 'cards');
                } else {
                    vistaLista.style.display = 'block';
                    vistaCards.style.display = 'none';
                    this.innerHTML = '<i class="fas fa-th-list"></i>';
                    localStorage.setItem('clientesVista', 'lista');
                }
            });
            
            // Carregar a preferência salva
            const vistaPreferida = localStorage.getItem('clientesVista');
            if (vistaPreferida === 'cards') {
                btnVisualizacao.click();
            }
        }
    };
    
    // Função para gerir filtros móveis
    const gerirFiltrosMobile = function() {
        if (btnFiltrosToggle && colunaFiltros) {
            btnFiltrosToggle.addEventListener('click', function() {
                colunaFiltros.classList.toggle('filtros-mobile-expanded');
            });
            
            // Fechar filtros ao clicar fora
            document.addEventListener('click', function(event) {
                if (window.innerWidth < 992 && 
                    !colunaFiltros.contains(event.target) && 
                    !btnFiltrosToggle.contains(event.target) && 
                    colunaFiltros.classList.contains('filtros-mobile-expanded')) {
                    colunaFiltros.classList.remove('filtros-mobile-expanded');
                }
            });
        }
    };
    
    // Função para gerir exclusão de clientes
    const gerirExclusaoClientes = function() {
        const modalExcluir = new bootstrap.Modal(document.getElementById('modal-excluir-cliente'));
        let clienteIdDelete = null;
        
        // Configurar botões de exclusão
        document.querySelectorAll('.btn-excluir-cliente').forEach(btn => {
            btn.addEventListener('click', function() {
                clienteIdDelete = this.getAttribute('data-id');
                document.getElementById('cliente-nome-delete').textContent = this.getAttribute('data-nome');
                modalExcluir.show();
            });
        });
        
        // Configurar botão de confirmação
        document.getElementById('confirmar-exclusao')?.addEventListener('click', function() {
            if (clienteIdDelete) {
                // Obter o token CSRF
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                                  document.cookie.replace(/(?:(?:^|.*;\s*)csrftoken\s*\=\s*([^;]*).*$)|^.*$/, "$1");
                
                // Enviar requisição para excluir
                fetch(`/clientes/excluir/${clienteIdDelete}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    modalExcluir.hide();
                    
                    if (data.status === 'success') {
                        // Remover elementos da UI
                        const elemLista = document.getElementById(`cliente-${clienteIdDelete}`);
                        if (elemLista) elemLista.remove();
                        
                        // Procurar card correspondente
                        const cardsContainer = document.getElementById('vista-cards');
                        if (cardsContainer) {
                            const col = cardsContainer.querySelector(`.col:has(button[data-id="${clienteIdDelete}"])`);
                            if (col) col.remove();
                        }
                        
                        // Mostrar mensagem
                        if (typeof toast !== 'undefined') {
                            toast('success', 'Sucesso', 'Cliente excluído com sucesso.');
                        } else {
                            alert('Cliente excluído com sucesso.');
                        }
                    } else {
                        // Mostrar erro
                        if (typeof toast !== 'undefined') {
                            toast('error', 'Erro', data.message || 'Não foi possível excluir o cliente.');
                        } else {
                            alert(data.message || 'Não foi possível excluir o cliente.');
                        }
                    }
                })
                .catch(error => {
                    console.error('Erro ao excluir cliente:', error);
                    alert('Ocorreu um erro ao processar a sua solicitação.');
                });
            }
        });
    };
    
    // Inicializar funcionalidades
    alternarVistas();
    gerirFiltrosMobile();
    gerirExclusaoClientes();
});