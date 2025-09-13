from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from inventory.models import Substance
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Carrega dados iniciais do sistema'

    def handle(self, *args, **options):
        self.stdout.write('Carregando dados iniciais...')
        
        # Criar usuário admin padrão
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@farmacia.com',
                password='admin123',
                nome='Administrador do Sistema',
                role='admin',
                empregado_id='ADM001'
            )
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            self.stdout.write(
                self.style.SUCCESS('Usuário admin criado (admin/admin123)')
            )
        
        # Criar usuário chefe padrão
        if not User.objects.filter(username='chefe').exists():
            chefe_user = User.objects.create_user(
                username='chefe',
                email='chefe@farmacia.com',
                password='chefe123',
                nome='Chefe da Clínica',
                role='chefe',
                empregado_id='CHF001'
            )
            self.stdout.write(
                self.style.SUCCESS('Usuário chefe criado (chefe/chefe123)')
            )
        
        # Criar usuário funcionário padrão
        if not User.objects.filter(username='funcionario').exists():
            func_user = User.objects.create_user(
                username='funcionario',
                email='funcionario@farmacia.com',
                password='func123',
                nome='Funcionário da Clínica',
                role='funcionario',
                empregado_id='FUN001'
            )
            self.stdout.write(
                self.style.SUCCESS('Usuário funcionário criado (funcionario/func123)')
            )
        
        # Substâncias iniciais (algumas das 38 mencionadas)
        substances_data = [
            {
                'nome_comum': 'Ácido Hialurônico',
                'nome_comercial': 'Restylane',
                'concentracao': '20mg/ml',
                'apresentacao': '1ml/seringa',
                'unidade': 'seringa',
                'estoque_minimo': Decimal('5'),
                'observacoes': 'Preenchimento facial'
            },
            {
                'nome_comum': 'Toxina Botulínica Tipo A',
                'nome_comercial': 'Botox',
                'concentracao': '100U',
                'apresentacao': '1 frasco',
                'unidade': 'frasco',
                'estoque_minimo': Decimal('3'),
                'observacoes': 'Aplicação facial e corporal'
            },
            {
                'nome_comum': 'Lidocaína',
                'nome_comercial': 'Xylocaína',
                'concentracao': '2%',
                'apresentacao': '20ml/ampola',
                'unidade': 'ampola',
                'estoque_minimo': Decimal('10'),
                'observacoes': 'Anestésico local'
            },
            {
                'nome_comum': 'Vitamina C',
                'nome_comercial': 'Adant',
                'concentracao': '500mg/ml',
                'apresentacao': '5ml/ampola',
                'unidade': 'ampola',
                'estoque_minimo': Decimal('8'),
                'observacoes': 'Antioxidante para mesoterapia'
            },
            {
                'nome_comum': 'Colágeno Hidrolisado',
                'nome_comercial': 'Sculptra',
                'concentracao': '367mg',
                'apresentacao': '1 frasco',
                'unidade': 'frasco',
                'estoque_minimo': Decimal('2'),
                'observacoes': 'Bioestimulador de colágeno'
            }
        ]
        
        admin_user = User.objects.get(username='admin')
        
        for substance_data in substances_data:
            substance, created = Substance.objects.get_or_create(
                nome_comum=substance_data['nome_comum'],
                concentracao=substance_data['concentracao'],
                defaults={
                    **substance_data,
                    'created_by': admin_user
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Substância criada: {substance.nome_comum}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Dados iniciais carregados com sucesso!')
        )

