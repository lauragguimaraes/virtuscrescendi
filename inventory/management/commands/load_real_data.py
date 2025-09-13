from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from inventory.models import Substance, Batch, Inventory, StockMovement, Patient
from users.models import User
from datetime import datetime, date
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Carrega dados reais da clínica'

    def handle(self, *args, **options):
        self.stdout.write('Carregando dados reais da clínica...')
        
        # Criar usuário admin se não existir
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'nome': 'Dr. Antonio Marcos',
                'email': 'admin@clinica.com',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('Usuário admin criado')

        # Limpar dados de exemplo anteriores
        Substance.objects.filter(nome_comum__in=[
            'Ácido Hialurônico', 'Toxina Botulínica Tipo A', 'Lidocaína', 
            'Vitamina C', 'Colágeno Hidrolisado'
        ]).delete()
        
        # Substâncias reais da clínica
        substancias_reais = [
            {'nome_comum': 'Ácido Alfa lipoico', 'concentracao': '100mg/ml', 'apresentacao': 'Ampola 5ml', 'unidade': 'ampola', 'estoque_minimo': 10},
            {'nome_comum': 'Acetilcisteina', 'concentracao': '300mg/ml', 'apresentacao': 'Ampola 3ml', 'unidade': 'ampola', 'estoque_minimo': 15},
            {'nome_comum': 'Beta alanina', 'concentracao': '500mg/ml', 'apresentacao': 'Ampola 2ml', 'unidade': 'ampola', 'estoque_minimo': 8},
            {'nome_comum': 'Cafeína', 'concentracao': '50mg/ml', 'apresentacao': 'Ampola 2ml', 'unidade': 'ampola', 'estoque_minimo': 10},
            {'nome_comum': 'Complexo B', 'concentracao': 'Mix vitaminas', 'apresentacao': 'Ampola 3ml', 'unidade': 'ampola', 'estoque_minimo': 20},
            {'nome_comum': 'Coenzima Q10', 'concentracao': '30mg/ml', 'apresentacao': 'Ampola 2ml', 'unidade': 'ampola', 'estoque_minimo': 15},
            {'nome_comum': 'Curcumina', 'concentracao': '100mg/ml', 'apresentacao': 'Ampola 2ml', 'unidade': 'ampola', 'estoque_minimo': 12},
            {'nome_comum': 'Gluthathion', 'concentracao': '600mg/ml', 'apresentacao': 'Ampola 5ml', 'unidade': 'ampola', 'estoque_minimo': 20},
            {'nome_comum': 'HMB', 'concentracao': '500mg/ml', 'apresentacao': 'Ampola 2ml', 'unidade': 'ampola', 'estoque_minimo': 10},
            {'nome_comum': 'Carnitina', 'concentracao': '1g/ml', 'apresentacao': 'Ampola 5ml', 'unidade': 'ampola', 'estoque_minimo': 15},
            {'nome_comum': 'Glicina', 'concentracao': '500mg/ml', 'apresentacao': 'Ampola 2ml', 'unidade': 'ampola', 'estoque_minimo': 12},
            {'nome_comum': 'Magnésio', 'concentracao': '100mg/ml', 'apresentacao': 'Ampola 10ml', 'unidade': 'ampola', 'estoque_minimo': 15},
            {'nome_comum': 'Metilfolato', 'concentracao': '5mg/ml', 'apresentacao': 'Ampola 2ml', 'unidade': 'ampola', 'estoque_minimo': 18},
            {'nome_comum': 'Metilcobalamina', 'concentracao': '1mg/ml', 'apresentacao': 'Ampola 1ml', 'unidade': 'ampola', 'estoque_minimo': 15},
            {'nome_comum': 'Metionina', 'concentracao': '250mg/ml', 'apresentacao': 'Ampola 2ml', 'unidade': 'ampola', 'estoque_minimo': 10},
            {'nome_comum': 'PQQ', 'concentracao': '20mg/ml', 'apresentacao': 'Ampola 1ml', 'unidade': 'ampola', 'estoque_minimo': 15},
            {'nome_comum': 'Piracetan', 'concentracao': '200mg/ml', 'apresentacao': 'Ampola 5ml', 'unidade': 'ampola', 'estoque_minimo': 8},
            {'nome_comum': 'Pool de minerais', 'concentracao': 'Mix minerais', 'apresentacao': 'Ampola 10ml', 'unidade': 'ampola', 'estoque_minimo': 10},
            {'nome_comum': 'Vitamina D 100', 'concentracao': '100.000UI/ml', 'apresentacao': 'Ampola 1ml', 'unidade': 'ampola', 'estoque_minimo': 5},
            {'nome_comum': 'Vitamina D 600', 'concentracao': '600.000UI/ml', 'apresentacao': 'Ampola 1ml', 'unidade': 'ampola', 'estoque_minimo': 8},
            {'nome_comum': 'Vitamina C', 'concentracao': '500mg/ml', 'apresentacao': 'Ampola 20ml', 'unidade': 'ampola', 'estoque_minimo': 20},
            {'nome_comum': 'Vitamina K', 'concentracao': '10mg/ml', 'apresentacao': 'Ampola 1ml', 'unidade': 'ampola', 'estoque_minimo': 5},
            {'nome_comum': 'Vitamina B3', 'concentracao': '100mg/ml', 'apresentacao': 'Ampola 2ml', 'unidade': 'ampola', 'estoque_minimo': 12},
            {'nome_comum': 'Vitamina B6', 'concentracao': '100mg/ml', 'apresentacao': 'Ampola 2ml', 'unidade': 'ampola', 'estoque_minimo': 12},
            {'nome_comum': 'Eritropoetina', 'concentracao': '4000UI/ml', 'apresentacao': 'Ampola 1ml', 'unidade': 'ampola', 'estoque_minimo': 5},
            {'nome_comum': 'Eritropoetina geladeira', 'concentracao': '4000UI/ml', 'apresentacao': 'Ampola 1ml', 'unidade': 'ampola', 'estoque_minimo': 10},
            {'nome_comum': 'Noripurum', 'concentracao': '100mg/ml', 'apresentacao': 'Ampola 5ml', 'unidade': 'ampola', 'estoque_minimo': 8},
            {'nome_comum': 'Ferropurum', 'concentracao': '50mg/ml', 'apresentacao': 'Ampola 2ml', 'unidade': 'ampola', 'estoque_minimo': 15},
            {'nome_comum': 'Diprospan', 'concentracao': '7mg/ml', 'apresentacao': 'Ampola 1ml', 'unidade': 'ampola', 'estoque_minimo': 20},
        ]

        # Criar substâncias
        for sub_data in substancias_reais:
            substance, created = Substance.objects.get_or_create(
                nome_comum=sub_data['nome_comum'],
                defaults={
                    'concentracao': sub_data['concentracao'],
                    'apresentacao': sub_data['apresentacao'],
                    'unidade': sub_data['unidade'],
                    'estoque_minimo': sub_data['estoque_minimo'],
                    'created_by': admin_user,
                }
            )
            if created:
                self.stdout.write(f'Substância criada: {substance.nome_comum}')

        # Estoque Ribeirão Preto (18/08/25)
        estoque_rp = {
            'Ácido Alfa lipoico': 5,
            'Acetilcisteina': 16,
            'Beta alanina': 3,
            'Cafeína': 8,
            'Complexo B': 4,
            'Coenzima Q10': 99,
            'Curcumina': 30,
            'Gluthathion': 16,
            'HMB': 25,
            'Carnitina': 38,
            'Glicina': 8,
            'Magnésio': 7,
            'Metilfolato': 17,
            'Metilcobalamina': 10,
            'Metionina': 8,
            'PQQ': 44,
            'Piracetan': 3,
            'Pool de minerais': 4,
            'Vitamina D 100': 0,
            'Vitamina D 600': 14,
            'Vitamina C': 18,
            'Vitamina K': 0,
            'Vitamina B3': 10,
            'Vitamina B6': 10,
            'Eritropoetina': 0,
            'Eritropoetina geladeira': 22,
            'Noripurum': 0,
            'Ferropurum': 35,
            'Diprospan': 50,
        }

        # Estoque Bauru (18/08/25)
        estoque_bauru = {
            'Ácido Alfa lipoico': 28,  # Note: "lipídico" no original, assumindo ser o mesmo
            'Acetilcisteina': 16,
            'Beta alanina': 10,
            'Cafeína': 5,
            'Complexo B': 21,
            'Coenzima Q10': 0,
            'Curcumina': 15,
            'Gluthathion': 25,
            'HMB': 34,
            'Carnitina': 26,
            'Glicina': 10,
            'Magnésio': 14,
            'Metilfolato': 23,
            'Metilcobalamina': 18,
            'Metionina': 7,
            'PQQ': 31,
            'Piracetan': 6,
            'Pool de minerais': 3,
            'Vitamina D 100': 11,
            'Vitamina D 600': 9,
            'Vitamina C': 34,
            'Vitamina B3': 10,
            'Vitamina B6': 14,
            'Eritropoetina': 3,
            'Eritropoetina geladeira': 9,
            'Noripurum': 3,
            'Ferropurum': 6,
            'Diprospan': 3,
        }

        # Criar lotes e estoque para Ribeirão Preto
        for nome_sub, quantidade in estoque_rp.items():
            if quantidade > 0:
                try:
                    substance = Substance.objects.get(nome_comum=nome_sub)
                    
                    # Criar lote
                    batch, created = Batch.objects.get_or_create(
                        substance=substance,
                        lote=f'RP-{nome_sub[:3].upper()}-001',
                        defaults={
                            'validade': date(2025, 6, 1),
                            'quantidade_recebida': Decimal(str(quantidade)),
                            'fornecedor': 'Fornecedor RP',
                            'created_by': admin_user,
                        }
                    )
                    
                    # Criar entrada no estoque
                    inventory, inv_created = Inventory.objects.get_or_create(
                        substance=substance,
                        batch=batch,
                        defaults={'quantity_on_hand': Decimal(str(quantidade))}
                    )
                    
                    if not inv_created:
                        inventory.quantity_on_hand = Decimal(str(quantidade))
                        inventory.save()
                    
                    # Registrar movimentação de entrada
                    StockMovement.objects.create(
                        substance=substance,
                        batch=batch,
                        tipo='entrada',
                        quantidade=Decimal(str(quantidade)),
                        motivo='Estoque inicial Ribeirão Preto',
                        user=admin_user,
                    )
                    
                except Substance.DoesNotExist:
                    self.stdout.write(f'Substância não encontrada: {nome_sub}')

        # Criar lotes e estoque para Bauru
        for nome_sub, quantidade in estoque_bauru.items():
            if quantidade > 0:
                try:
                    substance = Substance.objects.get(nome_comum=nome_sub)
                    
                    # Criar lote
                    batch, created = Batch.objects.get_or_create(
                        substance=substance,
                        lote=f'BR-{nome_sub[:3].upper()}-001',
                        defaults={
                            'validade': date(2025, 6, 1),
                            'quantidade_recebida': Decimal(str(quantidade)),
                            'fornecedor': 'Fornecedor Bauru',
                            'created_by': admin_user,
                        }
                    )
                    
                    # Criar entrada no estoque
                    inventory, inv_created = Inventory.objects.get_or_create(
                        substance=substance,
                        batch=batch,
                        defaults={'quantity_on_hand': Decimal(str(quantidade))}
                    )
                    
                    if not inv_created:
                        inventory.quantity_on_hand = Decimal(str(quantidade))
                        inventory.save()
                    
                    # Registrar movimentação de entrada
                    StockMovement.objects.create(
                        substance=substance,
                        batch=batch,
                        tipo='entrada',
                        quantidade=Decimal(str(quantidade)),
                        motivo='Estoque inicial Bauru',
                        user=admin_user,
                    )
                    
                except Substance.DoesNotExist:
                    self.stdout.write(f'Substância não encontrada: {nome_sub}')

        # Criar pacientes
        pacientes = [
            {
                'id_interno': 'PAC001',
                'nome': 'Dr. Antonio',
                'data_nascimento': date(1975, 3, 15),
                'contato': '(16) 99999-1111',
            },
            {
                'id_interno': 'PAC002',
                'nome': 'Rita (curso)',
                'data_nascimento': date(1985, 7, 22),
                'contato': '(16) 99999-2222',
            },
            {
                'id_interno': 'PAC003',
                'nome': 'Beatriz Mendes',
                'data_nascimento': date(1990, 11, 8),
                'contato': '(16) 99999-3333',
            },
        ]

        for pac_data in pacientes:
            patient, created = Patient.objects.get_or_create(
                id_interno=pac_data['id_interno'],
                defaults=pac_data
            )
            if created:
                self.stdout.write(f'Paciente criado: {patient.nome}')

        # Registrar sessões realizadas
        # Dr Antonio - 16/08/2025 - Sessão 1
        dr_antonio = Patient.objects.get(id_interno='PAC001')
        data_sessao = date(2025, 8, 16)
        
        substancias_dr_antonio = [
            ('Coenzima Q10', 1),
            ('Magnésio', 1),
            ('Curcumina', 1),
            ('Cafeína', 1),
        ]
        
        for nome_sub, qtd in substancias_dr_antonio:
            try:
                substance = Substance.objects.get(nome_comum=nome_sub)
                # Pegar lote de RP (assumindo que foi atendido em RP)
                batch = Batch.objects.filter(
                    substance=substance,
                    lote__startswith='RP-'
                ).first()
                
                if batch:
                    # Registrar saída
                    StockMovement.objects.create(
                        substance=substance,
                        batch=batch,
                        tipo='saida',
                        quantidade=Decimal(str(qtd)),
                        motivo=f'Sessão 1 - {dr_antonio.nome}',
                        user=admin_user,
                        paciente_nome=dr_antonio.nome,
                        data_hora=datetime.combine(data_sessao, datetime.min.time()),
                    )
                    
                    # Atualizar estoque
                    inventory = Inventory.objects.get(batch=batch)
                    inventory.quantity_on_hand -= Decimal(str(qtd))
                    inventory.save()
                    
            except (Substance.DoesNotExist, Inventory.DoesNotExist):
                self.stdout.write(f'Erro ao processar {nome_sub} para Dr Antonio')

        # Rita - 15/08/2025 - Sessão 3
        rita = Patient.objects.get(id_interno='PAC002')
        data_sessao = date(2025, 8, 15)
        
        substancias_rita = [
            ('Complexo B', 1),
            ('Metilfolato', 1),
            ('Metilcobalamina', 1),
            ('Curcumina', 1),
            ('Acetilcisteina', 1),
            ('Ácido Alfa lipoico', 1),  # Acréscimo
        ]
        
        for nome_sub, qtd in substancias_rita:
            try:
                substance = Substance.objects.get(nome_comum=nome_sub)
                batch = Batch.objects.filter(
                    substance=substance,
                    lote__startswith='RP-'
                ).first()
                
                if batch:
                    StockMovement.objects.create(
                        substance=substance,
                        batch=batch,
                        tipo='saida',
                        quantidade=Decimal(str(qtd)),
                        motivo=f'Sessão 3 - {rita.nome}',
                        user=admin_user,
                        paciente_nome=rita.nome,
                        data_hora=datetime.combine(data_sessao, datetime.min.time()),
                    )
                    
                    inventory = Inventory.objects.get(batch=batch)
                    inventory.quantity_on_hand -= Decimal(str(qtd))
                    inventory.save()
                    
            except (Substance.DoesNotExist, Inventory.DoesNotExist):
                self.stdout.write(f'Erro ao processar {nome_sub} para Rita')

        # Beatriz - 15/08/2025 - Sessão 1
        beatriz = Patient.objects.get(id_interno='PAC003')
        
        substancias_beatriz = [
            ('Complexo B', 1),
            ('Metilfolato', 1),
            ('Metilcobalamina', 1),
            ('Acetilcisteina', 1),
            ('Vitamina D 600', 1),
        ]
        
        for nome_sub, qtd in substancias_beatriz:
            try:
                substance = Substance.objects.get(nome_comum=nome_sub)
                batch = Batch.objects.filter(
                    substance=substance,
                    lote__startswith='RP-'
                ).first()
                
                if batch:
                    StockMovement.objects.create(
                        substance=substance,
                        batch=batch,
                        tipo='saida',
                        quantidade=Decimal(str(qtd)),
                        motivo=f'Sessão 1 - {beatriz.nome}',
                        user=admin_user,
                        paciente_nome=beatriz.nome,
                        data_hora=datetime.combine(data_sessao, datetime.min.time()),
                    )
                    
                    inventory = Inventory.objects.get(batch=batch)
                    inventory.quantity_on_hand -= Decimal(str(qtd))
                    inventory.save()
                    
            except (Substance.DoesNotExist, Inventory.DoesNotExist):
                self.stdout.write(f'Erro ao processar {nome_sub} para Beatriz')

        self.stdout.write(
            self.style.SUCCESS('Dados reais carregados com sucesso!')
        )
        self.stdout.write('29 substâncias cadastradas')
        self.stdout.write('Estoque de Ribeirão Preto e Bauru carregado')
        self.stdout.write('3 pacientes cadastrados')
        self.stdout.write('Movimentações das sessões registradas')

