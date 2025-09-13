from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import User, AuditLog
import json


def get_client_ip(request):
    """Obtém o IP do cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_user_action(user, action, request, details=None):
    """Registra ação do usuário no log de auditoria."""
    AuditLog.objects.create(
        user=user,
        action=action,
        table_name='auth',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        new_value=details
    )


def login_view(request):
    """View de login com suporte a 2FA."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        totp_token = request.POST.get('totp_token', '')
        
        if not username or not password:
            messages.error(request, 'Usuário e senha são obrigatórios.')
            return render(request, 'users/login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Verificar se o usuário está ativo
            if not user.is_active:
                messages.error(request, 'Conta desativada. Entre em contato com o administrador.')
                return render(request, 'users/login.html')
            
            # Verificar 2FA para chefes e admins
            if user.is_chefe and user.two_factor_enabled:
                if not totp_token:
                    # Primeira etapa: solicitar token 2FA
                    request.session['pre_2fa_user_id'] = user.id
                    return render(request, 'users/login_2fa.html', {
                        'user': user,
                        'show_qr': not user.totp_secret
                    })
                else:
                    # Segunda etapa: verificar token 2FA
                    if user.verify_totp(totp_token):
                        login(request, user)
                        log_user_action(user, 'login', request, {'2fa': True})
                        messages.success(request, f'Bem-vindo, {user.nome}!')
                        return redirect('core:dashboard')
                    else:
                        messages.error(request, 'Código 2FA inválido.')
                        request.session['pre_2fa_user_id'] = user.id
                        return render(request, 'users/login_2fa.html', {'user': user})
            else:
                # Login sem 2FA ou 2FA não habilitado
                login(request, user)
                log_user_action(user, 'login', request, {'2fa': False})
                messages.success(request, f'Bem-vindo, {user.nome}!')
                return redirect('core:dashboard')
        else:
            messages.error(request, 'Usuário ou senha incorretos.')
            log_user_action(None, 'login', request, {
                'failed_username': username,
                'ip': get_client_ip(request)
            })
    
    return render(request, 'users/login.html')


@login_required
def logout_view(request):
    """View de logout."""
    user = request.user
    log_user_action(user, 'logout', request)
    logout(request)
    messages.info(request, 'Você foi desconectado com sucesso.')
    return redirect('login')


@login_required
def setup_2fa_view(request):
    """View para configurar 2FA."""
    user = request.user
    
    if not user.is_chefe:
        messages.error(request, 'Apenas chefes e administradores podem configurar 2FA.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'enable':
            token = request.POST.get('token')
            if not token:
                messages.error(request, 'Token é obrigatório.')
            elif user.verify_totp(token):
                user.two_factor_enabled = True
                user.save()
                log_user_action(user, 'update', request, {'2fa_enabled': True})
                messages.success(request, '2FA habilitado com sucesso!')
                return redirect('core:dashboard')
            else:
                messages.error(request, 'Token inválido. Tente novamente.')
        
        elif action == 'disable':
            user.two_factor_enabled = False
            user.save()
            log_user_action(user, 'update', request, {'2fa_enabled': False})
            messages.success(request, '2FA desabilitado.')
            return redirect('dashboard')
        
        elif action == 'regenerate':
            user.totp_secret = ''
            user.two_factor_enabled = False
            user.save()
            user.generate_totp_secret()
            log_user_action(user, 'update', request, {'2fa_secret_regenerated': True})
            messages.info(request, 'Nova chave secreta gerada. Configure novamente o 2FA.')
    
    # Gerar chave secreta se não existir
    if not user.totp_secret:
        user.generate_totp_secret()
    
    context = {
        'user': user,
        'qr_code': user.get_qr_code(),
        'totp_uri': user.get_totp_uri(),
    }
    
    return render(request, 'users/setup_2fa.html', context)


@login_required
def profile_view(request):
    """View do perfil do usuário."""
    user = request.user
    
    if request.method == 'POST':
        # Atualizar informações básicas
        nome = request.POST.get('nome', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        
        if nome:
            old_data = {
                'nome': user.nome,
                'telefone': user.telefone
            }
            
            user.nome = nome
            user.telefone = telefone
            user.save()
            
            new_data = {
                'nome': user.nome,
                'telefone': user.telefone
            }
            
            log_user_action(user, 'update', request, {
                'old_value': old_data,
                'new_value': new_data
            })
            
            messages.success(request, 'Perfil atualizado com sucesso!')
        else:
            messages.error(request, 'Nome é obrigatório.')
    
    return render(request, 'users/profile.html', {'user': user})


@login_required
def change_password_view(request):
    """View para alterar senha."""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            messages.error(request, 'Todos os campos são obrigatórios.')
        elif new_password != confirm_password:
            messages.error(request, 'Nova senha e confirmação não coincidem.')
        elif len(new_password) < 8:
            messages.error(request, 'Nova senha deve ter pelo menos 8 caracteres.')
        elif not request.user.check_password(current_password):
            messages.error(request, 'Senha atual incorreta.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            log_user_action(request.user, 'update', request, {'password_changed': True})
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('login')
    
    return render(request, 'users/change_password.html')


class AuditLogView(View):
    """View para visualizar logs de auditoria (apenas para admins)."""
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_admin:
            messages.error(request, 'Acesso negado. Apenas administradores.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:100]
        return render(request, 'users/audit_logs.html', {'logs': logs})


@require_http_methods(["POST"])
@csrf_exempt
def verify_2fa_ajax(request):
    """Endpoint AJAX para verificar token 2FA."""
    if not request.user.is_authenticated:
        return JsonResponse({'valid': False, 'error': 'Não autenticado'})
    
    try:
        data = json.loads(request.body)
        token = data.get('token', '')
        
        if request.user.verify_totp(token):
            return JsonResponse({'valid': True})
        else:
            return JsonResponse({'valid': False, 'error': 'Token inválido'})
    except Exception as e:
        return JsonResponse({'valid': False, 'error': str(e)})
