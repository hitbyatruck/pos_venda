/**
 * JavaScript para gerenciar a associação em massa entre peças e fornecedores
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM carregado, inicializando handlers');
    
    // Inicializar sistema de abas
    var firstTab = document.querySelector('#peca-tab');
    if (firstTab) {
        var bsTab = new bootstrap.Tab(firstTab);
        bsTab.show();
    }
    
    // Inicializar filtros e botões
    initFiltros();
    initBotoes();
    
    // Mostrar erros de importação, se houver
    showImportErrors();
    
    // Restaurar a última aba ativa
    restoreActiveTab();
});

/**
 * Inicializa os filtros e eventos relacionados
 */
function initFiltros() {
    // Formulário de filtro de peças
    const formFiltroPecas = document.getElementById('pecaFilterForm');
    if (formFiltroPecas) {
        formFiltroPecas.addEventListener('submit', function(e) {
            e.preventDefault();
            buscarPecas();
        });
        
        // Reset do formulário
        formFiltroPecas.addEventListener('reset', function() {
            setTimeout(function() {
                buscarPecas();
            }, 10);
        });
    }
    
    // Formulário de filtro de fornecedores
    const formFiltroFornecedores = document.getElementById('fornecedorFilterForm');
    if (formFiltroFornecedores) {
        formFiltroFornecedores.addEventListener('submit', function(e) {
            e.preventDefault();
            buscarFornecedores();
        });
        
        // Reset do formulário
        formFiltroFornecedores.addEventListener('reset', function() {
            setTimeout(function() {
                buscarFornecedores();
            }, 10);
        });
    }
    
    // Toggle para mostrar/ocultar filtros de peças
    const btnToggleFiltrosPeca = document.getElementById('toggleFiltrosPeca');
    const containerFiltrosPeca = document.getElementById('filtroPecasContainer');
    
    if (btnToggleFiltrosPeca && containerFiltrosPeca) {
        btnToggleFiltrosPeca.addEventListener('click', function() {
            if (containerFiltrosPeca.style.display === 'none') {
                containerFiltrosPeca.style.display = 'block';
                btnToggleFiltrosPeca.innerHTML = '<i class="fas fa-filter"></i> Ocultar Filtros';
            } else {
                containerFiltrosPeca.style.display = 'none';
                btnToggleFiltrosPeca.innerHTML = '<i class="fas fa-filter"></i> Mostrar Filtros';
            }
        });
    }
    
    // Toggle para mostrar/ocultar filtros de fornecedores
    const btnToggleFiltrosFornecedor = document.getElementById('toggleFiltrosFornecedor');
    const containerFiltrosFornecedor = document.getElementById('filtroFornecedorContainer');
    
    if (btnToggleFiltrosFornecedor && containerFiltrosFornecedor) {
        btnToggleFiltrosFornecedor.addEventListener('click', function() {
            if (containerFiltrosFornecedor.style.display === 'none') {
                containerFiltrosFornecedor.style.display = 'block';
                btnToggleFiltrosFornecedor.innerHTML = '<i class="fas fa-filter"></i> Ocultar Filtros';
            } else {
                containerFiltrosFornecedor.style.display = 'none';
                btnToggleFiltrosFornecedor.innerHTML = '<i class="fas fa-filter"></i> Mostrar Filtros';
            }
        });
    }
}

/**
 * Inicializa os botões e event listeners relacionados
 */
function initBotoes() {
    // Botão para adicionar nova linha de fornecedor
    const addFornecedorBtn = document.getElementById('addFornecedorBtn');
    if (addFornecedorBtn) {
        addFornecedorBtn.addEventListener('click', function() {
            const table = document.getElementById('fornecedoresPecaTable');
            const tbody = table.querySelector('tbody');
            
            // Se a tabela estiver vazia, limpe mensagens de "sem resultados"
            if (tbody.innerText.includes('não tem fornecedores')) {
                tbody.innerHTML = '';
            }
            
            // Adicionar nova linha sem dados pré-existentes
            addFornecedorRow();
        });
    }
    
    // Botão para adicionar nova linha de peça
    const addPecaBtn = document.getElementById('addPecaBtn');
    if (addPecaBtn) {
        addPecaBtn.addEventListener('click', function() {
            const table = document.getElementById('pecasFornecedorTable');
            const tbody = table.querySelector('tbody');
            
            // Se a tabela estiver vazia, limpe mensagens de "sem resultados"
            if (tbody.innerText.includes('não tem peças')) {
                tbody.innerHTML = '';
            }
            
            // Adicionar nova linha sem dados pré-existentes
            addPecaRow();
        });
    }
    
    // Botão para salvar associações de peça
    const salvarAssociacoesPecaBtn = document.getElementById('salvarAssociacoesPeca');
    if (salvarAssociacoesPecaBtn) {
        salvarAssociacoesPecaBtn.addEventListener('click', function() {
            const form = document.getElementById('formAssociacaoPeca');
            if (form) {
                form.submit();
            }
        });
    }
    
    // Botão para salvar associações de fornecedor
    const salvarAssociacoesFornecedorBtn = document.getElementById('salvarAssociacoesFornecedor');
    if (salvarAssociacoesFornecedorBtn) {
        salvarAssociacoesFornecedorBtn.addEventListener('click', function() {
            const form = document.getElementById('formAssociacaoFornecedor');
            if (form) {
                form.submit();
            }
        });
    }
    
    // Garantir que a aba selecionada permaneça ativa
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            localStorage.setItem('activeAssociacaoTab', e.target.id);
        });
    });
}

/**
 * Restaura a última aba ativa
 */
function restoreActiveTab() {
    const activeTab = localStorage.getItem('activeAssociacaoTab');
    if (activeTab) {
        const tabToActivate = document.getElementById(activeTab);
        if (tabToActivate) {
            const tab = new bootstrap.Tab(tabToActivate);
            tab.show();
        }
    }
}

/**
 * Exibe os erros de importação, se houver
 */
function showImportErrors() {
    const container = document.getElementById('importErrorsContainer');
    if (!container) return;
    
    const hasErrors = container.dataset.hasErrors === 'true';
    if (hasErrors) {
        container.classList.remove('d-none');
    }
}

/**
 * Busca peças com base nos filtros
 */
function buscarPecas() {
    const codigo = document.getElementById('filterCodigo')?.value || '';
    const nome = document.getElementById('filterNome')?.value || '';
    const categoria = document.getElementById('filterCategoria')?.value || '';
    const equipamento = document.getElementById('filterEquipamento')?.value || '';
    const fornecedor = document.getElementById('filterFornecedor')?.value || '';
    
    // Construir URL com parâmetros
    let url = '/stock/api/filtrar-pecas/?';
    if (codigo) url += `codigo=${encodeURIComponent(codigo)}&`;
    if (nome) url += `nome=${encodeURIComponent(nome)}&`;
    if (categoria) url += `categoria=${encodeURIComponent(categoria)}&`;
    if (equipamento) url += `equipamento=${encodeURIComponent(equipamento)}&`;
    if (fornecedor) url += `fornecedor=${encodeURIComponent(fornecedor)}&`;
    
    // Mostrar indicador de carregamento
    const tbody = document.querySelector('#resultadosPecasTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" class="text-center"><i class="fas fa-spinner fa-spin"></i> Carregando...</td></tr>';
    
    // Fazer requisição AJAX
    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Limpar tabela
            tbody.innerHTML = '';
            
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhuma peça encontrada com os filtros informados.</td></tr>';
                return;
            }
            
            // Preencher tabela com resultados
            data.forEach(peca => {
                const row = document.createElement('tr');
                
                // Classe de status para o stock
                let statusClass = 'text-success';
                if (peca.status_stock === 'baixo') statusClass = 'text-warning';
                if (peca.status_stock === 'critico' || peca.status_stock === 'esgotado') statusClass = 'text-danger';
                
                row.innerHTML = `
                    <td>${peca.codigo}</td>
                    <td>${peca.nome}</td>
                    <td>${peca.categoria}</td>
                    <td class="${statusClass}">${peca.stock_atual}</td>
                    <td>${peca.qtd_fornecedores}</td>
                    <td>
                        <button type="button" class="btn btn-primary btn-sm selecionar-peca" data-id="${peca.id}" data-codigo="${peca.codigo}" data-nome="${peca.nome}">
                            <i class="fas fa-plus-circle"></i> Selecionar
                        </button>
                    </td>
                `;
                
                tbody.appendChild(row);
            });
            
            // Adicionar evento aos botões de seleção
            document.querySelectorAll('.selecionar-peca').forEach(btn => {
                btn.addEventListener('click', function() {
                    const pecaId = this.dataset.id;
                    const pecaCodigo = this.dataset.codigo;
                    const pecaNome = this.dataset.nome;
                    
                    // Mostrar área de associação
                    document.getElementById('associacaoPecaContainer').classList.remove('d-none');
                    
                    // Atualizar informações
                    document.getElementById('pecaSelecionadaInfo').textContent = `${pecaCodigo} - ${pecaNome}`;
                    document.getElementById('pecaIdHidden').value = pecaId;
                    
                    // Carregar fornecedores da peça
                    carregarFornecedoresPeca(pecaId);
                    
                    // Carregar histórico de preços
                    carregarHistoricoPrecos(pecaId);
                });
            });
        })
        .catch(error => {
            console.error('Erro ao buscar peças:', error);
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Erro ao buscar peças. Tente novamente.</td></tr>';
        });
}

/**
 * Busca fornecedores com base nos filtros
 */

// Variáveis globais para paginação
let fornecedoresPage = 1;
let fornecedoresTotalPages = 1;

/**
 * Busca fornecedores com base nos filtros
 */
function buscarFornecedores() {
    // Capturar todos os valores dos filtros
    const nome = document.getElementById('filterNomeFornecedor')?.value || '';
    const contato = document.getElementById('filterContatoFornecedor')?.value || '';
    const categoria = document.getElementById('filterCategoriaFornecedor')?.value || '';
    const peca = document.getElementById('filterPecaFornecida')?.value || '';
    const precoMax = document.getElementById('filterPrecoMaximo')?.value || '';
    
    // Construir URL com parâmetros
    let url = '/stock/api/filtrar-fornecedores/?';
    if (nome) url += `nome=${encodeURIComponent(nome)}&`;
    if (contato) url += `contato=${encodeURIComponent(contato)}&`;
    if (categoria) url += `categoria=${encodeURIComponent(categoria)}&`;
    if (peca) url += `peca=${encodeURIComponent(peca)}&`;
    if (precoMax) url += `preco_max=${encodeURIComponent(precoMax)}&`;
    
    // Mostrar indicador de carregamento
    const tbody = document.querySelector('#resultadosFornecedoresTable tbody');
    if (!tbody) {
        console.error('Elemento tbody não encontrado');
        return;
    }
    
    tbody.innerHTML = '<tr><td colspan="6" class="text-center"><i class="fas fa-spinner fa-spin"></i> Carregando...</td></tr>';
    
    // Fazer requisição AJAX
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Limpar tabela
            tbody.innerHTML = '';
            
            if (!data || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum fornecedor encontrado com os filtros informados.</td></tr>';
                return;
            }
            
            // Preencher tabela com resultados
            data.forEach(fornecedor => {
                const row = document.createElement('tr');
                
                row.innerHTML = `
                    <td>${fornecedor.nome}</td>
                    <td>${fornecedor.contato || '-'}</td>
                    <td>${fornecedor.telefone || '-'}</td>
                    <td>${fornecedor.email || '-'}</td>
                    <td>${fornecedor.qtd_pecas}</td>
                    <td>
                        <button type="button" class="btn btn-primary btn-sm selecionar-fornecedor" data-id="${fornecedor.id}" data-nome="${fornecedor.nome}">
                            <i class="fas fa-plus-circle"></i> Selecionar
                        </button>
                    </td>
                `;
                
                tbody.appendChild(row);
            });
            
            // Adicionar evento aos botões de seleção
            document.querySelectorAll('.selecionar-fornecedor').forEach(btn => {
                btn.addEventListener('click', function() {
                    const fornecedorId = this.dataset.id;
                    const fornecedorNome = this.dataset.nome;
                    
                    // Mostrar área de associação
                    document.getElementById('associacaoFornecedorContainer').classList.remove('d-none');
                    
                    // Atualizar informações
                    document.getElementById('nomeFornecedorSelecionado').textContent = fornecedorNome;
                    document.getElementById('fornecedorIdHidden').value = fornecedorId;
                    
                    // Carregar peças do fornecedor
                    carregarPecasFornecedor(fornecedorId);
                });
            });
        })
        .catch(error => {
            console.error('Erro ao buscar fornecedores:', error);
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Erro ao buscar fornecedores: ${error.message}</td></tr>`;
        });
}

/**
 * Atualiza os controles de paginação para fornecedores
 */
function updateFornecedoresPagination() {
    const paginationContainer = document.getElementById('fornecedoresPaginacao');
    const prevPageBtn = document.getElementById('fornecedoresPrevPage');
    const nextPageBtn = document.getElementById('fornecedoresNextPage');
    const pageInfo = document.getElementById('fornecedoresPaginaInfo');
    
    if (!paginationContainer) return;
    
    // Mostrar ou ocultar paginação
    if (fornecedoresTotalPages > 1) {
        paginationContainer.classList.remove('d-none');
    } else {
        paginationContainer.classList.add('d-none');
        return;
    }
    
    // Atualizar texto da página atual
    pageInfo.textContent = `${fornecedoresPage} de ${fornecedoresTotalPages}`;
    
    // Ativar/desativar botão de página anterior
    if (fornecedoresPage <= 1) {
        prevPageBtn.classList.add('disabled');
        prevPageBtn.parentElement.classList.add('disabled');
    } else {
        prevPageBtn.classList.remove('disabled');
        prevPageBtn.parentElement.classList.remove('disabled');
        prevPageBtn.onclick = () => buscarFornecedores(fornecedoresPage - 1);
    }
    
    // Ativar/desativar botão de próxima página
    if (fornecedoresPage >= fornecedoresTotalPages) {
        nextPageBtn.classList.add('disabled');
        nextPageBtn.parentElement.classList.add('disabled');
    } else {
        nextPageBtn.classList.remove('disabled');
        nextPageBtn.parentElement.classList.remove('disabled');
        nextPageBtn.onclick = () => buscarFornecedores(fornecedoresPage + 1);
    }
}

/**
 * Carrega fornecedores de uma peça específica
 */
function carregarFornecedoresPeca(pecaId) {
    const tbody = document.querySelector('#fornecedoresPecaTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" class="text-center"><i class="fas fa-spinner fa-spin"></i> Carregando fornecedores...</td></tr>';
    
    fetch(`/stock/api/peca/${pecaId}/fornecedores/`)
        .then(response => response.json())
        .then(data => {
            tbody.innerHTML = '';
            
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">Esta peça não tem fornecedores associados.</td></tr>';
                return;
            }
            
            data.forEach(fornecedor => {
                addFornecedorRow(fornecedor);
            });
        })
        .catch(error => {
            console.error('Erro ao carregar fornecedores:', error);
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Erro ao carregar fornecedores.</td></tr>';
        });
}

/**
 * Carrega peças de um fornecedor específico
 */
function carregarPecasFornecedor(fornecedorId) {
    const tbody = document.querySelector('#pecasFornecedorTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" class="text-center"><i class="fas fa-spinner fa-spin"></i> Carregando peças...</td></tr>';
    
    fetch(`/stock/api/fornecedor/${fornecedorId}/pecas/`)
        .then(response => response.json())
        .then(data => {
            tbody.innerHTML = '';
            
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">Este fornecedor não tem peças associadas.</td></tr>';
                return;
            }
            
            data.forEach(peca => {
                addPecaRow(peca);
            });
        })
        .catch(error => {
            console.error('Erro ao carregar peças:', error);
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Erro ao carregar peças.</td></tr>';
        });
}

/**
 * Adiciona uma linha de fornecedor à tabela de associações
 */
function addFornecedorRow(fornecedorData = null) {
    // Obter a tabela e tbody
    const table = document.getElementById('fornecedoresPecaTable');
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    // Criar nova linha
    const row = tbody.insertRow();
    const rowIndex = tbody.rows.length - 1;
    
    // Célula para seleção de fornecedor
    const cellFornecedor = row.insertCell();
    const selectFornecedor = document.createElement('select');
    selectFornecedor.name = `fornecedor_${rowIndex}`;
    selectFornecedor.className = 'form-select';
    selectFornecedor.required = true;
    
    // Opção padrão
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Selecione um fornecedor';
    selectFornecedor.appendChild(defaultOption);
    
    // Buscar fornecedores disponíveis
    fetch('/stock/api/fornecedores/')
        .then(response => response.json())
        .then(fornecedores => {
            fornecedores.forEach(fornecedor => {
                const option = document.createElement('option');
                option.value = fornecedor.id;
                option.textContent = fornecedor.nome;
                
                // Selecionar o fornecedor correto, se houver dados pré-carregados
                if (fornecedorData && fornecedor.id === fornecedorData.fornecedor_id) {
                    option.selected = true;
                }
                
                selectFornecedor.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Erro ao carregar lista de fornecedores:', error);
        });
    
    cellFornecedor.appendChild(selectFornecedor);
    
    // Célula para referência do fornecedor
    const cellReferencia = row.insertCell();
    const inputReferencia = document.createElement('input');
    inputReferencia.type = 'text';
    inputReferencia.name = `referencia_${rowIndex}`;
    inputReferencia.className = 'form-control';
    inputReferencia.placeholder = 'Referência';
    if (fornecedorData) {
        inputReferencia.value = fornecedorData.referencia_fornecedor || '';
    }
    cellReferencia.appendChild(inputReferencia);
    
    // Célula para preço unitário
    const cellPreco = row.insertCell();
    const inputPreco = document.createElement('input');
    inputPreco.type = 'number';
    inputPreco.name = `preco_${rowIndex}`;
    inputPreco.className = 'form-control';
    inputPreco.placeholder = '0.00';
    inputPreco.min = '0';
    inputPreco.step = '0.01';
    inputPreco.required = true;
    if (fornecedorData) {
        inputPreco.value = fornecedorData.preco_unitario || '';
    }
    cellPreco.appendChild(inputPreco);
    
    // Célula para tempo de entrega
    const cellPrazo = row.insertCell();
    const inputPrazo = document.createElement('input');
    inputPrazo.type = 'number';
    inputPrazo.name = `prazo_${rowIndex}`;
    inputPrazo.className = 'form-control';
    inputPrazo.placeholder = 'Dias';
    inputPrazo.min = '1';
    if (fornecedorData && fornecedorData.tempo_entrega) {
        inputPrazo.value = fornecedorData.tempo_entrega;
    }
    cellPrazo.appendChild(inputPrazo);
    
    // Célula para fornecedor preferencial
    const cellPreferencial = row.insertCell();
    const divCheck = document.createElement('div');
    divCheck.className = 'form-check';
    
    const inputPreferencial = document.createElement('input');
    inputPreferencial.type = 'checkbox';
    inputPreferencial.name = `preferencial_${rowIndex}`;
    inputPreferencial.id = `preferencial_${rowIndex}`;
    inputPreferencial.className = 'form-check-input preferencial-check';
    if (fornecedorData && fornecedorData.fornecedor_preferencial) {
        inputPreferencial.checked = true;
    }
    
    const labelPreferencial = document.createElement('label');
    labelPreferencial.className = 'form-check-label';
    labelPreferencial.htmlFor = `preferencial_${rowIndex}`;
    labelPreferencial.textContent = 'Preferencial';
    
    divCheck.appendChild(inputPreferencial);
    divCheck.appendChild(labelPreferencial);
    cellPreferencial.appendChild(divCheck);
    
    // Célula para ações
    const cellAcoes = row.insertCell();
    const btnRemover = document.createElement('button');
    btnRemover.type = 'button';
    btnRemover.className = 'btn btn-danger btn-sm';
    btnRemover.innerHTML = '<i class="fas fa-trash"></i>';
    btnRemover.addEventListener('click', function() {
        row.remove();
    });
    
    cellAcoes.appendChild(btnRemover);
    
    // Adicionar evento para lidar com checkbox preferencial
    inputPreferencial.addEventListener('change', function() {
        if (this.checked) {
            // Desmarcar outros checkboxes
            document.querySelectorAll('.preferencial-check').forEach(check => {
                if (check !== this) {
                    check.checked = false;
                }
            });
        }
    });
}

/**
 * Adiciona uma linha de peça à tabela de associações
 */
function addPecaRow(pecaData = null) {
    // Obter a tabela e tbody
    const table = document.getElementById('pecasFornecedorTable');
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    // Criar nova linha
    const row = tbody.insertRow();
    const rowIndex = tbody.rows.length - 1;
    
    // Célula para seleção de peça
    const cellPeca = row.insertCell();
    const selectPeca = document.createElement('select');
    selectPeca.name = `peca_${rowIndex}`;
    selectPeca.className = 'form-select';
    selectPeca.required = true;
    
    // Opção padrão
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Selecione uma peça';
    selectPeca.appendChild(defaultOption);
    
    // Buscar peças disponíveis
    fetch('/stock/api/pecas/')
        .then(response => response.json())
        .then(pecas => {
            pecas.forEach(peca => {
                const option = document.createElement('option');
                option.value = peca.id;
                option.textContent = `${peca.codigo} - ${peca.nome}`;
                
                // Selecionar a peça correta, se houver dados pré-carregados
                if (pecaData && peca.id === pecaData.peca_id) {
                    option.selected = true;
                }
                
                selectPeca.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Erro ao carregar lista de peças:', error);
        });
    
    cellPeca.appendChild(selectPeca);
    
    // Demais células (referência, preço, etc.)
    // Similar à função addFornecedorRow, adaptada para peças
    
    // Célula para referência do fornecedor
    const cellReferencia = row.insertCell();
    const inputReferencia = document.createElement('input');
    inputReferencia.type = 'text';
    inputReferencia.name = `referencia_${rowIndex}`;
    inputReferencia.className = 'form-control';
    inputReferencia.placeholder = 'Referência';
    if (pecaData) {
        inputReferencia.value = pecaData.referencia_fornecedor || '';
    }
    cellReferencia.appendChild(inputReferencia);
    
    // Célula para preço unitário
    const cellPreco = row.insertCell();
    const inputPreco = document.createElement('input');
    inputPreco.type = 'number';
    inputPreco.name = `preco_${rowIndex}`;
    inputPreco.className = 'form-control';
    inputPreco.placeholder = '0.00';
    inputPreco.min = '0';
    inputPreco.step = '0.01';
    inputPreco.required = true;
    if (pecaData) {
        inputPreco.value = pecaData.preco_unitario || '';
    }
    cellPreco.appendChild(inputPreco);
    
    // Célula para tempo de entrega
    const cellPrazo = row.insertCell();
    const inputPrazo = document.createElement('input');
    inputPrazo.type = 'number';
    inputPrazo.name = `prazo_${rowIndex}`;
    inputPrazo.className = 'form-control';
    inputPrazo.placeholder = 'Dias';
    inputPrazo.min = '1';
    if (pecaData && pecaData.tempo_entrega) {
        inputPrazo.value = pecaData.tempo_entrega;
    }
    cellPrazo.appendChild(inputPrazo);
    
    // Célula para preferencial
    const cellPreferencial = row.insertCell();
    const divCheck = document.createElement('div');
    divCheck.className = 'form-check';
    
    const inputPreferencial = document.createElement('input');
    inputPreferencial.type = 'checkbox';
    inputPreferencial.name = `preferencial_${rowIndex}`;
    inputPreferencial.id = `preferencial_peca_${rowIndex}`;
    inputPreferencial.className = 'form-check-input preferencial-check-peca';
    if (pecaData && pecaData.fornecedor_preferencial) {
        inputPreferencial.checked = true;
    }
    
    const labelPreferencial = document.createElement('label');
    labelPreferencial.className = 'form-check-label';
    labelPreferencial.htmlFor = `preferencial_peca_${rowIndex}`;
    labelPreferencial.textContent = 'Preferencial';
    
    divCheck.appendChild(inputPreferencial);
    divCheck.appendChild(labelPreferencial);
    cellPreferencial.appendChild(divCheck);
    
    // Célula para ações
    const cellAcoes = row.insertCell();
    const btnRemover = document.createElement('button');
    btnRemover.type = 'button';
    btnRemover.className = 'btn btn-danger btn-sm';
    btnRemover.innerHTML = '<i class="fas fa-trash"></i>';
    btnRemover.addEventListener('click', function() {
        row.remove();
    });
    
    cellAcoes.appendChild(btnRemover);
    
    // Adicionar evento para lidar com checkbox preferencial
    inputPreferencial.addEventListener('change', function() {
        if (this.checked) {
            // Desmarcar outros checkboxes
            document.querySelectorAll('.preferencial-check-peca').forEach(check => {
                if (check !== this) {
                    check.checked = false;
                }
            });
        }
    });
}

/**
 * Carrega e exibe o gráfico de histórico de preços
 */
function carregarHistoricoPrecos(pecaId) {
    fetch(`/stock/api/peca/${pecaId}/historico-precos/`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                document.getElementById('historicoPrecosPecaChart').parentElement.innerHTML = 
                    '<div class="alert alert-info">Não há histórico de preços disponível para esta peça.</div>';
                return;
            }
            
            // Preparar dados para o gráfico
            const datasets = [];
            let labels = [];
            
            data.forEach(fornecedor => {
                // Usar último conjunto de datas como labels
                if (fornecedor.datas.length > labels.length) {
                    labels = fornecedor.datas;
                }
                
                // Estilo para fornecedor preferencial
                const borderWidth = fornecedor.preferencial ? 3 : 1;
                const borderDash = fornecedor.preferencial ? [] : [5, 5];
                
                datasets.push({
                    label: `${fornecedor.fornecedor} (${fornecedor.referencia})`,
                    data: fornecedor.precos,
                    borderColor: getRandomColor(),
                    borderWidth: borderWidth,
                    borderDash: borderDash,
                    fill: false,
                    tension: 0.4
                });
            });
            
            // Criar o gráfico
            const ctx = document.getElementById('historicoPrecosPecaChart').getContext('2d');
            
            // Destruir gráfico existente se houver
            if (window.precosChart) {
                window.precosChart.destroy();
            }
            
            window.precosChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: 'Preço (€)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Data'
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Erro ao carregar histórico de preços:', error);
            document.getElementById('historicoPrecosPecaChart').parentElement.innerHTML = 
                '<div class="alert alert-danger">Erro ao carregar histórico de preços.</div>';
        });
}

/**
 * Gera uma cor aleatória para gráficos
 */
function getRandomColor() {
    const colors = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
        '#5a5c69', '#858796', '#6f42c1', '#20c9a6', '#fd7e14'
    ];
    return colors[Math.floor(Math.random() * colors.length)];
}

