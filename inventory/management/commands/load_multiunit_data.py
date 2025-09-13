from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from inventory.models import Unit, Substance, Batch, Inventory, Patient, StockMovement
from decimal import Decimal
from datetime import date, datetime
import uuid

User = get_user_model()


class Command(BaseCommand):
    help = 'Carrega dados reais da clínica com suporte a multi-unidades'

    def handle(self, *args, **options):
        self.stdout.write('🏗️ Carregando dados com multi-unidades...')
        
        # 1. Criar usuários
        self.create_users()
        
        # 2. Criar unidades
        self.create_units()
        
        # 3. Criar substâncias
        self.create_substances()
        
        # 4. Criar lotes e estoque
        self.create_batches_and_inventory()
        
        # 5. Criar pacientes
        self.create_patients()
        
        # 6. Criar movimentações das sessões
        self.create_sessions()
        
        self.stdout.write(self.style.SUCCESS('✅ Dados carregados com sucesso!'))

    def create_users(self):
        self.stdout.write('👥 Criando usuários...')
        
        # Admin
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@clinica.com',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
        
        # Chefe
        chefe, created = User.objects.get_or_create(
            username='chefe',
            defaults={
                'email': 'chefe@clinica.com',
                'first_name': 'Dr. Antonio',
                'last_name': 'Marcos',
                'role': 'chefe',
                'is_staff': True,
            }
        )
        if created:
            chefe.set_password('chefe123')
            chefe.save()
        
        # Funcionário
        funcionario, created = User.objects.get_or_create(
            username='funcionario',
            defaults={
                'email': 'funcionario@clinica.com',
                'first_name': 'Funcionário',
                'last_name': 'Clínica',
                'role': 'funcionario',
            }
        )
        if created:
            funcionario.set_password('func123')
            funcionario.save()

    def create_units(self):
        self.stdout.write('🏢 Criando unidades...')
        
        # Ribeirão Preto
        self.unit_rp, created = Unit.objects.get_or_create(
            codigo='RP',
            defaults={
                'nome': 'Ribeirão Preto',
                'endereco': 'Ribeirão Preto - SP',
                'telefone': '(16) 9999-9999',
                'email': 'rp@clinica.com',
                'responsavel': 'Dr. Antonio Marcos',
                'ativo': True,
            }
        )
        
        # Bauru
        self.unit_bauru, created = Unit.objects.get_or_create(
            codigo='BR',
            defaults={
                'nome': 'Bauru',
                'endereco': 'Bauru - SP',
                'telefone': '(14) 9999-9999',
                'email': 'bauru@clinica.com',
                'responsavel': 'Equipe Bauru',
                'ativo': True,
            }
        )

    def create_substances(self):
        self.stdout.write('💊 Criando substâncias...')
        
        substances_data = [
            ('Ácido Alfa lipoico', '100mg/ml', 'Ampola', 2.0),
            ('Acetilcisteina', '300mg/ml', 'Ampola', 5.0),
            ('Beta alanina', '500mg/ml', 'Ampola', 3.0),
            ('Cafeína', '50mg/ml', 'Ampola', 5.0),
            ('Complexo B', 'Mix vitaminas', 'Ampola', 10.0),
            ('Coenzima Q10', '30mg/ml', 'Ampola', 15.0),
            ('Curcumina', '100mg/ml', 'Ampola', 8.0),
            ('Gluthathion', '600mg/ml', 'Ampola', 12.0),
            ('HMB', '500mg/ml', 'Ampola', 6.0),
            ('Carnitina', '1g/ml', 'Ampola', 10.0),
            ('Glicina', '500mg/ml', 'Ampola', 4.0),
            ('Magnésio', '100mg/ml', 'Ampola', 7.0),
            ('Metilfolato', '5mg/ml', 'Ampola', 8.0),
            ('Metilcobalamina', '1mg/ml', 'Ampola', 9.0),
            ('Metionina', '250mg/ml', 'Ampola', 6.0),
            ('PQQ', '20mg/ml', 'Ampola', 5.0),
            ('Piracetan', '200mg/ml', 'Ampola', 3.0),
            ('Pool de minerais', 'Mix minerais', 'Ampola', 4.0),
            ('Vitamina D 100', '100.000UI/ml', 'Ampola', 2.0),
            ('Vitamina D 600', '600.000UI/ml', 'Ampola', 2.0),
            ('Vitamina C', '500mg/ml', 'Ampola', 8.0),
            ('Vitamina K', '10mg/ml', 'Ampola', 2.0),
            ('Vitamina B3', '100mg/ml', 'Ampola', 5.0),
            ('Vitamina B6', '100mg/ml', 'Ampola', 5.0),
            ('Eritropoetina', '4000UI/ml', 'Ampola', 3.0),
            ('Eritropoetina geladeira', '4000UI/ml', 'Ampola', 3.0),
            ('Noripurum', '100mg/ml', 'Ampola', 5.0),
            ('Ferropurum', '50mg/ml', 'Ampola', 8.0),
            ('Diprospan', '7mg/ml', 'Ampola', 10.0),
        ]
        
        admin = User.objects.get(username='admin')
        
        for nome, concentracao, apresentacao, estoque_min in substances_data:
            substance, created = Substance.objects.get_or_create(
                nome_comum=nome,
                defaults={
                    'concentracao': concentracao,
                    'apresentacao': apresentacao,
                    'unidade': 'ampola',
                    'estoque_minimo_default': Decimal(str(estoque_min)),
                    'dias_alerta_vencimento': 90,
                    'created_by': admin,
                }
            )

    def create_batches_and_inventory(self):
        self.stdout.write('📦 Criando lotes e estoque...')
        
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
            'Ácido Alfa lipoico': 28,
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
        
        admin = User.objects.get(username='admin')
        
        # Criar lotes e estoque para RP
        for nome_substancia, quantidade in estoque_rp.items():
            if quantidade > 0:
                substance = Substance.objects.get(nome_comum=nome_substancia)
                
                # Criar lote
                batch, created = Batch.objects.get_or_create(
                    substance=substance,
                    unit=self.unit_rp,
                    lote=f'RP-{nome_substancia[:3].upper()}-001',
                    defaults={
                        'validade': date(2025, 12, 31),
                        'quantidade_recebida': Decimal(str(quantidade)),
                        'fornecedor': 'Fornecedor RP',
                        'nota_fiscal_ref': f'NF-RP-{substance.id}',
                        'preco_unitario': Decimal('10.00'),
                        'created_by': admin,
                    }
                )
                
                # Criar estoque
                inventory, created = Inventory.objects.get_or_create(
                    substance=substance,
                    batch=batch,
                    unit=self.unit_rp,
                    defaults={
                        'quantity_on_hand': Decimal(str(quantidade)),
                    }
                )
        
        # Criar lotes e estoque para Bauru
        for nome_substancia, quantidade in estoque_bauru.items():
            if quantidade > 0:
                substance = Substance.objects.get(nome_comum=nome_substancia)
                
                # Criar lote
                batch, created = Batch.objects.get_or_create(
                    substance=substance,
                    unit=self.unit_bauru,
                    lote=f'BR-{nome_substancia[:3].upper()}-001',
                    defaults={
                        'validade': date(2025, 12, 31),
                        'quantidade_recebida': Decimal(str(quantidade)),
                        'fornecedor': 'Fornecedor Bauru',
                        'nota_fiscal_ref': f'NF-BR-{substance.id}',
                        'preco_unitario': Decimal('10.00'),
                        'created_by': admin,
                    }
                )
                
                # Criar estoque
                inventory, created = Inventory.objects.get_or_create(
                    substance=substance,
                    batch=batch,
                    unit=self.unit_bauru,
                    defaults={
                        'quantity_on_hand': Decimal(str(quantidade)),
                    }
                )

    def create_patients(self):
        self.stdout.write('👤 Criando pacientes...')
        
        admin = User.objects.get(username='admin')
        
        # Dr. Antonio
        self.patient_antonio, created = Patient.objects.get_or_create(
            codigo='PAC001',
            defaults={
                'nome': 'Dr. Antonio',
                'unidade_principal': self.unit_rp,
                'observacoes': 'Médico da clínica',
                'ativo': True,
                'created_by': admin,
            }
        )
        
        # Rita (curso)
        self.patient_rita, created = Patient.objects.get_or_create(
            codigo='PAC002',
            defaults={
                'nome': 'Rita (curso)',
                'unidade_principal': self.unit_rp,
                'observacoes': 'Paciente do curso',
                'ativo': True,
                'created_by': admin,
            }
        )
        
        # Beatriz Mendes
        self.patient_beatriz, created = Patient.objects.get_or_create(
            codigo='PAC003',
            defaults={
                'nome': 'Beatriz Mendes',
                'unidade_principal': self.unit_rp,
                'observacoes': 'Paciente regular',
                'ativo': True,
                'created_by': admin,
            }
        )

    def create_sessions(self):
        self.stdout.write('💉 Criando sessões de atendimento...')
        
        admin = User.objects.get(username='admin')
        
        # Sessão Dr. Antonio (16/08/2025)
        sessao_antonio = [
            ('Coenzima Q10', 1),
            ('Magnésio', 1),
            ('Curcumina', 1),
            ('Cafeína', 1),
        ]
        
        for nome_substancia, quantidade in sessao_antonio:
            substance = Substance.objects.get(nome_comum=nome_substancia)
            inventory = Inventory.objects.filter(
                substance=substance,
                unit=self.unit_rp,
                quantity_on_hand__gt=0
            ).first()
            
            if inventory:
                # Criar movimentação
                StockMovement.objects.create(
                    substance=substance,
                    batch=inventory.batch,
                    unit=self.unit_rp,
                    tipo='saida',
                    quantidade=Decimal(str(quantidade)),
                    motivo=f'Sessão 1 - {self.patient_antonio.nome}',
                    paciente=self.patient_antonio,
                    paciente_nome=self.patient_antonio.nome,
                    procedimento='Protocolo antioxidante',
                    user=admin,
                    ip_address='127.0.0.1',
                )
                
                # Atualizar estoque
                inventory.quantity_on_hand -= Decimal(str(quantidade))
                inventory.save()
        
        # Sessão Rita (15/08/2025)
        sessao_rita = [
            ('Complexo B', 1),
            ('Metilfolato', 1),
            ('Metilcobalamina', 1),
            ('Curcumina', 1),
            ('Acetilcisteina', 1),
            ('Ácido Alfa lipoico', 1),  # Acréscimo
        ]
        
        for nome_substancia, quantidade in sessao_rita:
            substance = Substance.objects.get(nome_comum=nome_substancia)
            inventory = Inventory.objects.filter(
                substance=substance,
                unit=self.unit_rp,
                quantity_on_hand__gt=0
            ).first()
            
            if inventory:
                # Criar movimentação
                StockMovement.objects.create(
                    substance=substance,
                    batch=inventory.batch,
                    unit=self.unit_rp,
                    tipo='saida',
                    quantidade=Decimal(str(quantidade)),
                    motivo=f'Sessão 3 - {self.patient_rita.nome}',
                    paciente=self.patient_rita,
                    paciente_nome=self.patient_rita.nome,
                    procedimento='Protocolo Complexo B + acréscimo',
                    user=admin,
                    ip_address='127.0.0.1',
                )
                
                # Atualizar estoque
                inventory.quantity_on_hand -= Decimal(str(quantidade))
                inventory.save()
        
        # Sessão Beatriz (15/08/2025)
        sessao_beatriz = [
            ('Complexo B', 1),
            ('Metilfolato', 1),
            ('Metilcobalamina', 1),
            ('Acetilcisteina', 1),
            ('Vitamina D 600', 1),
        ]
        
        for nome_substancia, quantidade in sessao_beatriz:
            substance = Substance.objects.get(nome_comum=nome_substancia)
            inventory = Inventory.objects.filter(
                substance=substance,
                unit=self.unit_rp,
                quantity_on_hand__gt=0
            ).first()
            
            if inventory:
                # Criar movimentação
                StockMovement.objects.create(
                    substance=substance,
                    batch=inventory.batch,
                    unit=self.unit_rp,
                    tipo='saida',
                    quantidade=Decimal(str(quantidade)),
                    motivo=f'Sessão 1 - {self.patient_beatriz.nome}',
                    paciente=self.patient_beatriz,
                    paciente_nome=self.patient_beatriz.nome,
                    procedimento='Protocolo inicial com Vitamina D',
                    user=admin,
                    ip_address='127.0.0.1',
                )
                
                # Atualizar estoque
                inventory.quantity_on_hand -= Decimal(str(quantidade))
                inventory.save()

