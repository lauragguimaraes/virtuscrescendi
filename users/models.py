from django.contrib.auth.models import AbstractUser
from django.db import models
import pyotp
import qrcode
from io import BytesIO
import base64


class User(AbstractUser):
    """
    Modelo de usuário personalizado para o sistema de estoque farmacêutico.
    """
    ROLE_CHOICES = [
        ('funcionario', 'Funcionário'),
        ('chefe', 'Chefe'),
        ('admin', 'Administrador'),
    ]
    
    nome = models.CharField(max_length=150, verbose_name='Nome completo')
    telefone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='funcionario',
        verbose_name='Função'
    )
    empregado_id = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True,
        verbose_name='ID do Empregado'
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    
    # 2FA fields
    totp_secret = models.CharField(max_length=32, blank=True, verbose_name='Chave TOTP')
    two_factor_enabled = models.BooleanField(default=False, verbose_name='2FA Habilitado')
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} ({self.get_role_display()})"
    
    @property
    def is_chefe(self):
        """Verifica se o usuário é chefe ou admin."""
        return self.role in ['chefe', 'admin']
    
    @property
    def is_admin(self):
        """Verifica se o usuário é admin."""
        return self.role == 'admin'
    
    def generate_totp_secret(self):
        """Gera uma nova chave secreta para TOTP."""
        if not self.totp_secret:
            self.totp_secret = pyotp.random_base32()
            self.save()
        return self.totp_secret
    
    def get_totp_uri(self):
        """Retorna a URI para configuração do TOTP."""
        if not self.totp_secret:
            self.generate_totp_secret()
        
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(
            name=self.email,
            issuer_name="Farmácia Estoque"
        )
    
    def verify_totp(self, token):
        """Verifica um token TOTP."""
        if not self.totp_secret:
            return False
        
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)
    
    def get_qr_code(self):
        """Gera QR code para configuração do 2FA."""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(self.get_totp_uri())
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()


class AuditLog(models.Model):
    """
    Log de auditoria para rastrear todas as ações no sistema.
    """
    ACTION_CHOICES = [
        ('create', 'Criação'),
        ('update', 'Atualização'),
        ('delete', 'Exclusão'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('view', 'Visualização'),
        ('export', 'Exportação'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Usuário'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Ação')
    table_name = models.CharField(max_length=100, verbose_name='Tabela')
    record_id = models.CharField(max_length=100, blank=True, verbose_name='ID do Registro')
    old_value = models.JSONField(blank=True, null=True, verbose_name='Valor Anterior')
    new_value = models.JSONField(blank=True, null=True, verbose_name='Novo Valor')
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name='IP')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.timestamp}"
