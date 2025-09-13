from django.core.management.base import BaseCommand
from inventory.models import Patient, Unit, StockMovement

class Command(BaseCommand):
    help = 'Corrige a unidade da paciente Beatriz para Bauru'

    def handle(self, *args, **options):
        try:
            # Buscar unidades
            bauru = Unit.objects.get(codigo='BR')
            
            # Buscar Beatriz
            beatriz = Patient.objects.get(nome='Beatriz Mendes')
            
            # Atualizar unidade
            beatriz.unidade_principal = bauru
            beatriz.save()
            
            # Atualizar movimentações da Beatriz para Bauru
            StockMovement.objects.filter(paciente=beatriz).update(unit=bauru)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Beatriz atualizada para unidade Bauru')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro: {str(e)}')
            )

