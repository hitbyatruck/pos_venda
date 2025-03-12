document.addEventListener("DOMContentLoaded", function() {
    console.log("assistencia_scripts.js carregado e em execução!");

    const clienteSelect = document.getElementById("id_cliente");
    const equipamentoSelect = document.getElementById("id_equipamento");

    if (!clienteSelect || !equipamentoSelect) {
        console.error("ERRO: Dropdowns de Cliente ou Equipamento não encontrados!");
        return;
    }

    function updateEquipamentoDropdown(clienteId) {
        console.log(`Cliente selecionado: ${clienteId}`);

        if (!clienteId) {
            equipamentoSelect.innerHTML = '<option value="">Selecione um Cliente Primeiro</option>';
            return;
        }

        fetch(`/assistencia/equipamentos-por-cliente/?cliente_id=${clienteId}`)
            .then(response => response.json())
            .then(data => {
                console.log("Equipamentos recebidos:", data);

                equipamentoSelect.innerHTML = "";
                let placeholderOpt = document.createElement("option");
                placeholderOpt.value = "";
                placeholderOpt.text = "Selecione um Equipamento";
                equipamentoSelect.appendChild(placeholderOpt);

                data.equipamentos.forEach(eq => {
                    let option = document.createElement("option");
                    option.value = eq.id;
                    option.textContent = `${eq.nome} (Nº Série: ${eq.numero_serie})`;
                    equipamentoSelect.appendChild(option);
                });

                console.log("Dropdown Equipamento atualizado.");
            })
            .catch(error => {
                console.error("Erro ao buscar equipamentos:", error);
            });
    }

    clienteSelect.addEventListener("change", function() {
        console.log("Evento de mudança de cliente acionado.");
        updateEquipamentoDropdown(this.value);
    });

    if (clienteSelect.value) {
        console.log("Cliente já selecionado na carga da página.");
        updateEquipamentoDropdown(clienteSelect.value);
    }
});
