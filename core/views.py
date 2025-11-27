from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def menu_principal(request):
    return render(request, 'core/menu.html',{
        "user": request.user,
    })

def logout_msg(request):
    return render(request, "core/logout_msg.html")
