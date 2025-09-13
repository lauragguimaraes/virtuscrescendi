from django.core.management.base import BaseCommand
from inventory.models import Patient, Unit, StockMovement

class Command(BaseCommand):
    help = 'Corrige a unidade da paciente Rita para Bauru'

    def handle(self, *args, **options):
        try:
            # Buscar unidades
            bauru = Unit.objects.get(codigo='BR')
            
            # Buscar Rita
            rita = Patient.objects.get(nome='Rita (curso)')
            
            self.stdout.write(f'Rita atual: {rita.nome} - Unidade: {rita.unidade_principal.nome}')
            
            # Atualizar unidade
            rita.unidade_principal = bauru
            rita.save()
            
            # Atualizar movimentações da Rita para Bauru
            movs_updated = StockMovement.objects.filter(paciente=rita).update(unit=bauru)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Rita atualizada para unidade Bauru')
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ {movs_updated} movimentações atualizadas')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro: {str(e)}')
            )

