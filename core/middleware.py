from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class RoleBasedAccessMiddleware:
    """
    Middleware para controlar acesso baseado em roles.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs que requerem permissões específicas
        self.admin_only_urls = [
            '/admin/',
            '/users/audit-logs/',
        ]
        
        self.chefe_admin_only_urls = [
            '/inventory/entrada/',
        ]
        
        # URLs públicas (não requerem login)
        self.public_urls = [
            '/users/login/',
            '/login/',
        ]
    
    def __call__(self, request):
        # Verificar se é uma URL pública
        if any(request.path.startswith(url) for url in self.public_urls):
            response = self.get_response(request)
            return response
        
        # Verificar se o usuário está autenticado
        if not request.user.is_authenticated:
            if request.path != reverse('users:login'):
                return redirect('users:login')
        else:
            # Verificar permissões específicas
            if any(request.path.startswith(url) for url in self.admin_only_urls):
                if not (request.user.role == 'admin'):
                    messages.error(request, 'Acesso negado. Apenas administradores.')
                    return redirect('core:dashboard')
            
            elif any(request.path.startswith(url) for url in self.chefe_admin_only_urls):
                if not (request.user.role in ['chefe', 'admin']):
                    messages.error(request, 'Acesso negado. Apenas chefes e administradores.')
                    return redirect('core:dashboard')
        
        response = self.get_response(request)
        return response

