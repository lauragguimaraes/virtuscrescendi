from django.core.management.base import BaseCommand
from inventory.models import Patient, Unit, StockMovement
from django.utils import timezone

class Command(BaseCommand):
    help = 'Corrige as unidades dos pacientes Rita, Beatriz e Andreia'

    def handle(self, *args, **options):
        try:
            # Buscar unidades
            rp_unit = Unit.objects.get(codigo='RP')
            bauru_unit = Unit.objects.get(codigo='BR')
            
            # Corrigir Rita para Bauru
            rita = Patient.objects.get(codigo='PAC002')
            if rita.unidade_principal != bauru_unit:
                self.stdout.write(f'Corrigindo Rita de {rita.unidade_principal.nome} para {bauru_unit.nome}')
                rita.unidade_principal = bauru_unit
                rita.save()
                
                # Atualizar movimentações da Rita
                rita_movements = StockMovement.objects.filter(paciente=rita)
                for movement in rita_movements:
                    if movement.unit != bauru_unit:
                        self.stdout.write(f'Atualizando movimentação da Rita para Bauru')
                        movement.unit = bauru_unit
                        movement.save()
            
            # Corrigir Beatriz para Bauru
            beatriz = Patient.objects.get(codigo='PAC003')
            if beatriz.unidade_principal != bauru_unit:
                self.stdout.write(f'Corrigindo Beatriz de {beatriz.unidade_principal.nome} para {bauru_unit.nome}')
                beatriz.unidade_principal = bauru_unit
                beatriz.save()
                
                # Atualizar movimentações da Beatriz
                beatriz_movements = StockMovement.objects.filter(paciente=beatriz)
                for movement in beatriz_movements:
                    if movement.unit != bauru_unit:
                        self.stdout.write(f'Atualizando movimentação da Beatriz para Bauru')
                        movement.unit = bauru_unit
                        movement.save()
            
            # Verificar Andreia (já deve estar em Bauru)
            try:
                andreia = Patient.objects.get(codigo='PAC005')
                if andreia.unidade_principal != bauru_unit:
                    self.stdout.write(f'Corrigindo Andreia de {andreia.unidade_principal.nome} para {bauru_unit.nome}')
                    andreia.unidade_principal = bauru_unit
                    andreia.save()
                    
                    # Atualizar movimentações da Andreia
                    andreia_movements = StockMovement.objects.filter(paciente=andreia)
                    for movement in andreia_movements:
                        if movement.unit != bauru_unit:
                            self.stdout.write(f'Atualizando movimentação da Andreia para Bauru')
                            movement.unit = bauru_unit
                            movement.save()
                else:
                    self.stdout.write('Andreia já está corretamente em Bauru')
            except Patient.DoesNotExist:
                self.stdout.write('Andreia não encontrada')
            
            self.stdout.write(
                self.style.SUCCESS('✅ Unidades dos pacientes corrigidas com sucesso!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao corrigir unidades: {e}')
            )

