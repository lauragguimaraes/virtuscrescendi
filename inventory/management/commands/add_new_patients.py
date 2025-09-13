from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, date
from inventory.models import Unit, Patient, Substance, Batch, Inventory, StockMovement
from users.models import User


class Command(BaseCommand):
    help = 'Adiciona as novas pacientes Isleila e Andreia'

    def handle(self, *args, **options):
        try:
            # Buscar unidades
            rp_unit = Unit.objects.get(codigo='RP')
            bauru_unit = Unit.objects.get(codigo='BR')
            
            # Buscar usuário admin
            admin_user = User.objects.get(username='admin')
            
            # Criar paciente Isleila
            isleila, created = Patient.objects.get_or_create(
                codigo='PAC004',
                defaults={
                    'nome': 'Isleila',
                    'unidade_principal': rp_unit,
                    'observacoes': 'Paciente - 3ª sessão',
                    'ativo': True,
                    'created_by': admin_user
                }
            )
            
            if created:
                self.stdout.write(f"✅ Paciente Isleila criada: {isleila.codigo}")
            
            # Criar paciente Andreia
            andreia, created = Patient.objects.get_or_create(
                codigo='PAC005',
                defaults={
                    'nome': 'Andreia',
                    'unidade_principal': bauru_unit,
                    'observacoes': 'Suplente do curso - 3ª sessão',
                    'ativo': True,
                    'created_by': admin_user
                }
            )
            
            if created:
                self.stdout.write(f"✅ Paciente Andreia criada: {andreia.codigo}")
            
            # Registrar movimentações da Isleila (RP)
            isleila_substances = [
                ('Complexo B', 1),
                ('Metilfolato', 1),
                ('Metilcobalamina', 1),
                ('Acetilcisteina', 1),
                ('Curcumina', 1),
                ('Carnitina', 1),
                ('Vitamina D 600', 1),
                ('HMB', 1),
            ]
            
            data_sessao = timezone.make_aware(datetime(2025, 8, 26, 18, 0))
            
            for substance_name, quantity in isleila_substances:
                try:
                    substance = Substance.objects.get(nome_comum=substance_name)
                    
                    # Buscar lote disponível em RP
                    inventory = Inventory.objects.filter(
                        substance=substance,
                        unit=rp_unit,
                        quantity_on_hand__gte=quantity
                    ).first()
                    
                    if inventory and inventory.quantity_on_hand >= quantity:
                        # Criar movimentação de saída
                        movement = StockMovement.objects.create(
                            substance=substance,
                            batch=inventory.batch,
                            unit=rp_unit,
                            tipo='saida',
                            quantidade=quantity,
                            paciente=isleila,
                            procedimento=f'3ª Sessão - Isleila',
                            motivo=f'Saída para sessão da paciente Isleila',
                            user=admin_user,
                            data_hora=data_sessao
                        )
                        
                        # Atualizar estoque
                        inventory.quantity_on_hand -= quantity
                        inventory.save()
                        
                        self.stdout.write(f"✅ Saída registrada: {substance_name} - {quantity} ampola(s) - Isleila")
                    else:
                        self.stdout.write(f"⚠️ Estoque insuficiente para {substance_name} em RP")
                        
                except Substance.DoesNotExist:
                    self.stdout.write(f"❌ Substância não encontrada: {substance_name}")
            
            # Registrar movimentações da Andreia (Bauru)
            andreia_substances = [
                ('Acetilcisteina', 1),
                ('Complexo B', 1),
                ('Metilcobalamina', 1),
                ('Metilfolato', 1),
                ('Curcumina', 1),
                ('Vitamina D 100', 1),
            ]
            
            for substance_name, quantity in andreia_substances:
                try:
                    substance = Substance.objects.get(nome_comum=substance_name)
                    
                    # Buscar lote disponível em Bauru
                    inventory = Inventory.objects.filter(
                        substance=substance,
                        unit=bauru_unit,
                        quantity_on_hand__gte=quantity
                    ).first()
                    
                    if inventory and inventory.quantity_on_hand >= quantity:
                        # Criar movimentação de saída
                        movement = StockMovement.objects.create(
                            substance=substance,
                            batch=inventory.batch,
                            unit=bauru_unit,
                            tipo='saida',
                            quantidade=quantity,
                            paciente=andreia,
                            procedimento=f'3ª Sessão - Andreia (suplente do curso)',
                            motivo=f'Saída para sessão da paciente Andreia',
                            user=admin_user,
                            data_hora=data_sessao
                        )
                        
                        # Atualizar estoque
                        inventory.quantity_on_hand -= quantity
                        inventory.save()
                        
                        self.stdout.write(f"✅ Saída registrada: {substance_name} - {quantity} ampola(s) - Andreia")
                    else:
                        self.stdout.write(f"⚠️ Estoque insuficiente para {substance_name} em Bauru")
                        
                except Substance.DoesNotExist:
                    self.stdout.write(f"❌ Substância não encontrada: {substance_name}")
            
            self.stdout.write(self.style.SUCCESS('✅ Novas pacientes e movimentações adicionadas com sucesso!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro: {str(e)}'))

