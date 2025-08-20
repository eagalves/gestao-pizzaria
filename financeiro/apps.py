from django.apps import AppConfig


class FinanceiroConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'financeiro'
    verbose_name = 'Financeiro'
    
    def ready(self):
        """Registra os sinais quando o app é carregado."""
        try:
            import financeiro.signals
        except ImportError:
            pass
