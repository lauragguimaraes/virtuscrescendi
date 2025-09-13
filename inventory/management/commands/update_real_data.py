from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from inventory.models import Unit, Substance, Batch, Patient, StockMovement
from datetime import datetime, date
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Atualiza dados reais do sistema baseado nos dados fornecidos'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Iniciando atualização de dados reais...')
        
        # Buscar usuário admin
        admin_user = User.objects.get(username='admin')
        
        # Buscar unidades
        rp_unit = Unit.objects.get(codigo='RP')
        bauru_unit = Unit.objects.get(codigo='BR')
        
        # 1. CRIAR NOVOS PACIENTES REAIS
        self.stdout.write('📝 Criando pacientes reais...')
        
        # Pacientes Ribeirão Preto
        patients_rp = [
            {'codigo': 'PAC006', 'nome': 'Vera Lucia', 'observacoes': 'Paciente regular'},
            {'codigo': 'PAC007', 'nome': 'Nelma', 'observacoes': 'Primeira sessão'},
            {'codigo': 'PAC008', 'nome': 'Paloma', 'observacoes': 'Tratamento com ferro'},
            {'codigo': 'PAC009', 'nome': 'Regina Comini', 'observacoes': 'Paciente experiente - 11 sessões'},
            {'codigo': 'PAC010', 'nome': 'Zenilda', 'observacoes': 'Primeira sessão'},
            {'codigo': 'PAC011', 'nome': 'Claudi Gricio', 'observacoes': 'Primeira sessão'},
            {'codigo': 'PAC012', 'nome': 'Tatiane', 'observacoes': 'Primeira sessão'},
        ]
        
        # Pacientes Bauru  
        patients_bauru = [
            {'codigo': 'PAC013', 'nome': 'Andreia Pozza', 'observacoes': 'Suplente do curso'},
        ]
        
        # Criar pacientes RP
        for patient_data in patients_rp:
            patient, created = Patient.objects.get_or_create(
                codigo=patient_data['codigo'],
                defaults={
                    'nome': patient_data['nome'],
                    'observacoes': patient_data['observacoes'],
                    'unidade_principal': rp_unit,
                    'ativo': True
                }
            )
            if created:
                self.stdout.write(f'✅ Criado: {patient.nome} ({patient.codigo})')
        
        # Criar pacientes Bauru
        for patient_data in patients_bauru:
            patient, created = Patient.objects.get_or_create(
                codigo=patient_data['codigo'],
                defaults={
                    'nome': patient_data['nome'],
                    'observacoes': patient_data['observacoes'],
                    'unidade_principal': bauru_unit,
                    'ativo': True
                }
            )
            if created:
                self.stdout.write(f'✅ Criado: {patient.nome} ({patient.codigo})')
        
        # 2. ATUALIZAR ESTOQUES REAIS
        self.stdout.write('📦 Atualizando estoques reais...')
        
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
        
        # Estoque Bauru (29/08/25 - após transferências)
        estoque_bauru = {
            'Ácido Alfa lipoico': 8,  # Era 28, transferiu 20
            'Acetilcisteina': 14,
            'Beta alanina': 4,
            'Cafeína': 5,
            'Complexo B': 9,  # Era 21, transferiu 12
            'Coenzima Q10': 0,
            'Curcumina': 13,
            'Gluthathion': 25,
            'HMB': 34,
            'Carnitina': 26,
            'Glicina': 10,
            'Magnésio': 8,  # Era 14, transferiu 6
            'Metilfolato': 11,  # Era 23, transferiu 12
            'Metilcobalamina': 8,  # Era 18, transferiu 10
            'Metionina': 7,
            'PQQ': 31,
            'Piracetan': 6,
            'Pool de minerais': 3,
            'Vitamina D 100': 11,
            'Vitamina D 600': 8,
            'Vitamina C': 34,
            'Vitamina B3': 10,
            'Vitamina B6': 14,
            'Eritropoetina': 3,
            'Eritropoetina geladeira': 9,
            'Noripurum': 3,
            'Ferropurum': 16,  # Recebeu 10
            'Diprospan': 13,  # Recebeu 10
        }
        
        # Atualizar estoques
        for nome, quantidade in estoque_rp.items():
            try:
                # Busca mais específica para evitar múltiplos resultados
                if 'Vitamina D 100' in nome:
                    substance = Substance.objects.get(nome_comum='Vitamina D 100')
                elif 'Vitamina D 600' in nome:
                    substance = Substance.objects.get(nome_comum='Vitamina D 600.000ui')
                elif 'Eritropoetina geladeira' in nome:
                    substance = Substance.objects.get(nome_comum='Eritropoetina geladeira')
                elif 'Ácido Alfa lipoico' in nome:
                    substance = Substance.objects.get(nome_comum='Ácido Alfa lipoico')
                else:
                    substance = Substance.objects.filter(nome_comum__icontains=nome.split()[0]).first()
                
                if substance:
                    # Buscar lote da unidade RP
                    batch = Batch.objects.filter(
                        substance=substance,
                        unit=rp_unit
                    ).first()
                    
                    if batch:
                        batch.quantidade_inicial = Decimal(str(quantidade))
                        batch.save()
                        self.stdout.write(f'✅ RP - {nome}: {quantidade}')
                else:
                    self.stdout.write(f'⚠️  Substância não encontrada: {nome}')
            except Exception as e:
                self.stdout.write(f'⚠️  Erro com {nome}: {str(e)}')
        
        for nome, quantidade in estoque_bauru.items():
            try:
                # Busca mais específica para evitar múltiplos resultados
                if 'Vitamina D 100' in nome:
                    substance = Substance.objects.get(nome_comum='Vitamina D 100')
                elif 'Vitamina D 600' in nome:
                    substance = Substance.objects.get(nome_comum='Vitamina D 600.000ui')
                elif 'Eritropoetina geladeira' in nome:
                    substance = Substance.objects.get(nome_comum='Eritropoetina geladeira')
                elif 'Ácido Alfa lipoico' in nome:
                    substance = Substance.objects.get(nome_comum='Ácido Alfa lipoico')
                else:
                    substance = Substance.objects.filter(nome_comum__icontains=nome.split()[0]).first()
                
                if substance:
                    # Buscar lote da unidade Bauru
                    batch = Batch.objects.filter(
                        substance=substance,
                        unit=bauru_unit
                    ).first()
                    
                    if batch:
                        batch.quantidade_inicial = Decimal(str(quantidade))
                        batch.save()
                        self.stdout.write(f'✅ BR - {nome}: {quantidade}')
                else:
                    self.stdout.write(f'⚠️  Substância não encontrada: {nome}')
            except Exception as e:
                self.stdout.write(f'⚠️  Erro com {nome}: {str(e)}')
        
        # 3. CRIAR SESSÕES REAIS
        self.stdout.write('💉 Criando sessões reais...')
        
        # Sessão Vera Lucia (18/08/2025)
        vera = Patient.objects.get(codigo='PAC006')
        self.create_session(vera, admin_user, date(2025, 8, 18), 2, [
            'Complexo B', 'Metilfolato', 'Metilcobalamina', 'Acetilcisteina', 'Curcumina'
        ])
        
        # Sessão Rita (18/08/2025) - Atualizar paciente existente
        rita = Patient.objects.get(codigo='PAC002')
        self.create_session(rita, admin_user, date(2025, 8, 18), 3, [
            'Complexo B', 'Metilfolato', 'Metilcobalamina', 'Curcumina', 'Acetilcisteina', 'Ácido Alfa lipoico'
        ])
        
        self.stdout.write('✅ Dados reais atualizados com sucesso!')
    
    def create_session(self, patient, user, session_date, session_number, substances):
        """Criar sessão com substâncias utilizadas"""
        for substance_name in substances:
            try:
                substance = Substance.objects.get(nome_comum__icontains=substance_name.split()[0])
                batch = Batch.objects.filter(
                    substance=substance,
                    unit=patient.unidade_principal
                ).first()
                
                if batch and batch.get_estoque_atual() > 0:
                    # Criar movimentação de saída
                    StockMovement.objects.create(
                        substance=substance,
                        batch=batch,
                        unit=patient.unidade_principal,
                        tipo='saida',
                        quantidade=1,
                        paciente=patient,
                        user=user,
                        data_hora=datetime.combine(session_date, datetime.now().time())
                    )
                    
                    # Atualizar estoque
                    batch.quantidade_inicial -= 1
                    batch.save()
                    
                    self.stdout.write(f'✅ Sessão {patient.nome}: {substance_name}')
            except Substance.DoesNotExist:
                self.stdout.write(f'⚠️  Substância não encontrada: {substance_name}')

