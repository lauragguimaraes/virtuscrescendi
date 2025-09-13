from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from inventory.models import ProtocolTemplate, ProtocolSubstance, Substance
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Carrega protocolos de exemplo baseados nos dados reais da clínica'

    def handle(self, *args, **options):
        self.stdout.write('Carregando protocolos de exemplo...')
        
        # Buscar usuário admin
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            admin_user = User.objects.first()
        
        # Protocolo 1: Antioxidante (baseado no Dr. Antonio)
        protocol_antioxidante, created = ProtocolTemplate.objects.get_or_create(
            name='Protocolo Antioxidante',
            defaults={
                'description': 'Protocolo focado em antioxidantes para combate ao estresse oxidativo e envelhecimento celular.',
                'default_sessions': 4,
                'is_active': True,
                'created_by': admin_user
            }
        )
        
        if created:
            # Substâncias do protocolo antioxidante
            substances_antioxidante = [
                ('Coenzima Q10', Decimal('1.0'), False, 1),
                ('Curcumina', Decimal('1.0'), False, 2),
                ('Magnésio', Decimal('1.0'), False, 3),
                ('Cafeína', Decimal('1.0'), True, 4),  # Opcional
            ]
            
            for substance_name, quantity, is_optional, order in substances_antioxidante:
                try:
                    substance = Substance.objects.get(nome_comum=substance_name)
                    ProtocolSubstance.objects.get_or_create(
                        protocol=protocol_antioxidante,
                        substance=substance,
                        defaults={
                            'default_quantity': quantity,
                            'is_optional': is_optional,
                            'order': order,
                            'notes': f'Dosagem padrão para {substance_name}'
                        }
                    )
                except Substance.DoesNotExist:
                    self.stdout.write(f'Substância {substance_name} não encontrada')
        
        # Protocolo 2: Complexo B (baseado na Rita e Beatriz)
        protocol_complexo_b, created = ProtocolTemplate.objects.get_or_create(
            name='Protocolo Complexo B',
            defaults={
                'description': 'Protocolo com vitaminas do complexo B para energia e metabolismo celular.',
                'default_sessions': 3,
                'is_active': True,
                'created_by': admin_user
            }
        )
        
        if created:
            # Substâncias do protocolo complexo B
            substances_complexo_b = [
                ('Complexo B', Decimal('1.0'), False, 1),
                ('Metilfolato', Decimal('1.0'), False, 2),
                ('Metilcobalamina', Decimal('1.0'), False, 3),
                ('Acetilcisteina', Decimal('1.0'), False, 4),
            ]
            
            for substance_name, quantity, is_optional, order in substances_complexo_b:
                try:
                    substance = Substance.objects.get(nome_comum=substance_name)
                    ProtocolSubstance.objects.get_or_create(
                        protocol=protocol_complexo_b,
                        substance=substance,
                        defaults={
                            'default_quantity': quantity,
                            'is_optional': is_optional,
                            'order': order,
                            'notes': f'Dosagem padrão para {substance_name}'
                        }
                    )
                except Substance.DoesNotExist:
                    self.stdout.write(f'Substância {substance_name} não encontrada')
        
        # Protocolo 3: Vitamina D (baseado na Beatriz)
        protocol_vitamina_d, created = ProtocolTemplate.objects.get_or_create(
            name='Protocolo Vitamina D',
            defaults={
                'description': 'Protocolo com alta dose de Vitamina D para deficiência severa (apenas primeira sessão).',
                'default_sessions': 1,
                'is_active': True,
                'created_by': admin_user
            }
        )
        
        if created:
            # Substâncias do protocolo vitamina D
            substances_vitamina_d = [
                ('Vitamina D 600', Decimal('1.0'), False, 1),
                ('Complexo B', Decimal('1.0'), True, 2),  # Opcional
                ('Metilfolato', Decimal('1.0'), True, 3),  # Opcional
            ]
            
            for substance_name, quantity, is_optional, order in substances_vitamina_d:
                try:
                    substance = Substance.objects.get(nome_comum=substance_name)
                    ProtocolSubstance.objects.get_or_create(
                        protocol=protocol_vitamina_d,
                        substance=substance,
                        defaults={
                            'default_quantity': quantity,
                            'is_optional': is_optional,
                            'order': order,
                            'notes': 'Apenas na primeira sessão' if substance_name == 'Vitamina D 600' else f'Dosagem padrão para {substance_name}'
                        }
                    )
                except Substance.DoesNotExist:
                    self.stdout.write(f'Substância {substance_name} não encontrada')
        
        # Protocolo 4: Performance Esportiva
        protocol_performance, created = ProtocolTemplate.objects.get_or_create(
            name='Protocolo Performance Esportiva',
            defaults={
                'description': 'Protocolo para atletas e pessoas ativas, focado em performance e recuperação.',
                'default_sessions': 6,
                'is_active': True,
                'created_by': admin_user
            }
        )
        
        if created:
            # Substâncias do protocolo performance
            substances_performance = [
                ('Carnitina', Decimal('1.0'), False, 1),
                ('HMB', Decimal('1.0'), False, 2),
                ('Beta alanina', Decimal('1.0'), False, 3),
                ('Cafeína', Decimal('1.0'), False, 4),
                ('Magnésio', Decimal('1.0'), True, 5),  # Opcional
                ('Glicina', Decimal('1.0'), True, 6),  # Opcional
            ]
            
            for substance_name, quantity, is_optional, order in substances_performance:
                try:
                    substance = Substance.objects.get(nome_comum=substance_name)
                    ProtocolSubstance.objects.get_or_create(
                        protocol=protocol_performance,
                        substance=substance,
                        defaults={
                            'default_quantity': quantity,
                            'is_optional': is_optional,
                            'order': order,
                            'notes': f'Dosagem padrão para {substance_name}'
                        }
                    )
                except Substance.DoesNotExist:
                    self.stdout.write(f'Substância {substance_name} não encontrada')
        
        # Protocolo 5: Anti-aging
        protocol_antiaging, created = ProtocolTemplate.objects.get_or_create(
            name='Protocolo Anti-aging',
            defaults={
                'description': 'Protocolo completo para longevidade e anti-envelhecimento.',
                'default_sessions': 8,
                'is_active': True,
                'created_by': admin_user
            }
        )
        
        if created:
            # Substâncias do protocolo anti-aging
            substances_antiaging = [
                ('Coenzima Q10', Decimal('1.0'), False, 1),
                ('PQQ', Decimal('1.0'), False, 2),
                ('Curcumina', Decimal('1.0'), False, 3),
                ('Gluthathion', Decimal('1.0'), False, 4),
                ('Vitamina C', Decimal('1.0'), False, 5),
                ('Metilfolato', Decimal('1.0'), True, 6),  # Opcional
                ('Metilcobalamina', Decimal('1.0'), True, 7),  # Opcional
            ]
            
            for substance_name, quantity, is_optional, order in substances_antiaging:
                try:
                    substance = Substance.objects.get(nome_comum=substance_name)
                    ProtocolSubstance.objects.get_or_create(
                        protocol=protocol_antiaging,
                        substance=substance,
                        defaults={
                            'default_quantity': quantity,
                            'is_optional': is_optional,
                            'order': order,
                            'notes': f'Dosagem padrão para {substance_name}'
                        }
                    )
                except Substance.DoesNotExist:
                    self.stdout.write(f'Substância {substance_name} não encontrada')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Protocolos carregados com sucesso!\n'
                f'- Protocolo Antioxidante: {protocol_antioxidante.substances.count()} substâncias\n'
                f'- Protocolo Complexo B: {protocol_complexo_b.substances.count()} substâncias\n'
                f'- Protocolo Vitamina D: {protocol_vitamina_d.substances.count()} substâncias\n'
                f'- Protocolo Performance Esportiva: {protocol_performance.substances.count()} substâncias\n'
                f'- Protocolo Anti-aging: {protocol_antiaging.substances.count()} substâncias'
            )
        )

