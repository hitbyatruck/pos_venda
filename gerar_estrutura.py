import os

IGNORAR_PASTAS = [
    'venv', '.venv', 'env', '.env', '__pycache__', 
    '.git', 'migrations', 'node_modules', '.idea'
]

def imprimir_estrutura(diretorio_raiz, arquivo_saida='estrutura_projeto.txt'):
    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        for raiz, pastas, arquivos in os.walk(diretorio_raiz):
            # Remover pastas que devem ser ignoradas
            pastas[:] = [p for p in pastas if p not in IGNORAR_PASTAS]
            
            # Calcular nível de indentação
            nivel = raiz.replace(diretorio_raiz, '').count(os.sep)
            indentacao = '    ' * nivel
            
            # Imprimir nome da pasta
            pasta_nome = os.path.basename(raiz)
            if pasta_nome:  # evitar linha em branco para o diretório raiz
                f.write(f"{indentacao}{pasta_nome}/\n")
            
            # Imprimir arquivos
            for arquivo in sorted(arquivos):
                if arquivo.endswith('.pyc') or arquivo.startswith('.'):
                    continue
                f.write(f"{indentacao}    {arquivo}\n")

# Altere para o caminho do seu projeto
imprimir_estrutura('c:/Users/HBT/Documents/pos_venda')

print("Estrutura gerada em 'estrutura_projeto.txt'")