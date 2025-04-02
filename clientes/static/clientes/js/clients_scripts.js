document.addEventListener('DOMContentLoaded', function() {
    // Processamento dos campos de formulário para estilização
    const formInputs = document.querySelectorAll('input, select, textarea');
    formInputs.forEach(input => {
        // Adicionar classes para tratamento de dark mode e estilo consistente
        if (input.type !== 'checkbox' && input.type !== 'radio') {
            input.classList.add('form-control');
            
            // Adicionar borda arredondada e sombra sutil
            input.style.borderRadius = '.25rem';
            input.style.boxShadow = 'none';
            
            // Ajustar cores para compatibilidade com dark mode
            input.addEventListener('focus', function() {
                this.style.borderColor = '#4e73df';
                this.style.boxShadow = '0 0 0 0.2rem rgba(78, 115, 223, 0.25)';
            });
            
            input.addEventListener('blur', function() {
                this.style.boxShadow = 'none';
            });
        }
    });
    
    // Manipulação do endereço igual à empresa
    const enderecoCheckbox = document.getElementById('id_endereco_igual_empresa');
    const empresaSelect = document.getElementById('id_empresa');
    
    if (enderecoCheckbox && empresaSelect) {
        function toggleEnderecoFields() {
            const enderecoFields = document.querySelectorAll('.endereco-field');
            if (enderecoCheckbox.checked && empresaSelect.value) {
                enderecoFields.forEach(field => {
                    field.style.opacity = '0.5';
                    field.querySelector('input, select').setAttribute('readonly', true);
                });
            } else {
                enderecoFields.forEach(field => {
                    field.style.opacity = '1';
                    field.querySelector('input, select').removeAttribute('readonly');
                });
            }
        }
        
        enderecoCheckbox.addEventListener('change', toggleEnderecoFields);
        empresaSelect.addEventListener('change', toggleEnderecoFields);
        
        // Inicializar estado
        toggleEnderecoFields();
    }
    
    // Lembrar a aba ativa
    const triggerTabList = [].slice.call(document.querySelectorAll('#clienteTabs button'));
    triggerTabList.forEach(function(triggerEl) {
        triggerEl.addEventListener('shown.bs.tab', function(event) {
            localStorage.setItem('activeClienteTab', event.target.getAttribute('data-bs-target'));
        });
    });
    
    // Restaurar aba ativa
    const activeTab = localStorage.getItem('activeClienteTab');
    if (activeTab) {
        const trigger = document.querySelector(`#clienteTabs button[data-bs-target="${activeTab}"]`);
        if (trigger) {
            new bootstrap.Tab(trigger).show();
        }
    }
});