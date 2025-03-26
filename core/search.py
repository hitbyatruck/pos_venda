from django.db.models import Q
from .utils import normalize_text

class AdvancedSearch:
    """
    Classe utilitária para realizar pesquisas avançadas normalizadas em modelos Django.
    Suporta pesquisa em campos relacionados e normalização de texto.
    """
    
    def __init__(self, request, model_class, fields_to_search=None, related_searches=None):
        """
        Inicializa o serviço de pesquisa.
        
        Args:
            request: O objeto HttpRequest
            model_class: A classe do modelo a ser pesquisado
            fields_to_search: Lista de campos diretos para pesquisar
            related_searches: Dicionário com relacionamentos e seus campos para pesquisa
                              Formato: {'related_name': ['campo1', 'campo2']}
        """
        self.request = request
        self.model_class = model_class
        self.fields_to_search = fields_to_search or []
        self.related_searches = related_searches or {}
        self.query = request.GET.get('q', '').strip()
        self.normalized_query = normalize_text(self.query) if self.query else ''
        
    def search(self, base_queryset=None):
        """
        Executa a pesquisa normalizada.
        """
        # Usar o queryset fornecido ou criar um novo
        queryset = base_queryset if base_queryset is not None else self.model_class.objects.all()
        
        # Se não há termo de pesquisa, retornar todos os registos
        if not self.query:
            return queryset
            
        # Para busca normalizada, precisamos verificar cada objeto
        all_objects = list(queryset)
        filtered_ids = []
        
        # Verificar cada objeto
        for obj in all_objects:
            # Se já está nos filtrados, continuar
            if obj.id in filtered_ids:
                continue
                
            # Verificar campos diretos
            if self._check_direct_fields(obj):
                filtered_ids.append(obj.id)
                continue
                
            # Verificar campos relacionados
            if self._check_related_fields(obj):
                filtered_ids.append(obj.id)
                continue
        
        # Retornar queryset filtrado com os IDs encontrados
        return self.model_class.objects.filter(id__in=filtered_ids)
    
    def _check_direct_fields(self, obj):
        """Verifica se o termo de pesquisa está presente em algum campo direto"""
        for field_name in self.fields_to_search:
            value = self._get_attribute_safely(obj, field_name)
            if value is not None:
                normalized_value = normalize_text(str(value))
                if self.normalized_query in normalized_value:
                    return True
        return False
    
    def _check_related_fields(self, obj):
        """Verifica se o termo de pesquisa está presente em campos relacionados"""
        for relation_name, fields in self.related_searches.items():
            related_obj = self._get_attribute_safely(obj, relation_name)
            
            # Se for uma coleção (ManyToMany, etc)
            if hasattr(related_obj, 'all') and callable(related_obj.all):
                for related_item in related_obj.all():
                    for field_name in fields:
                        value = self._get_attribute_safely(related_item, field_name)
                        if value is not None:
                            normalized_value = normalize_text(str(value))
                            if self.normalized_query in normalized_value:
                                return True
            # Se for um objeto único (ForeignKey)
            elif related_obj is not None:
                for field_name in fields:
                    value = self._get_attribute_safely(related_obj, field_name)
                    if value is not None:
                        normalized_value = normalize_text(str(value))
                        if self.normalized_query in normalized_value:
                            return True
        return False
    
    @staticmethod
    def _get_attribute_safely(obj, attr_name):
        """Obtém um atributo de um objeto de forma segura, suportando acesso aninhado com ponto"""
        if '.' in attr_name:
            parts = attr_name.split('.')
            current = obj
            for part in parts:
                if current is None:
                    return None
                current = getattr(current, part, None)
            return current
        else:
            return getattr(obj, attr_name, None)
    
    @staticmethod
    def apply_filter(queryset, field, value, filter_type='exact'):
        """
        Aplica um filtro simples ao queryset.
        """
        if not value:
            return queryset
            
        filter_kwargs = {f"{field}__{filter_type}": value}
        return queryset.filter(**filter_kwargs)