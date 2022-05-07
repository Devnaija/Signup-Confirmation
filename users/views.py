from django.core.mail import EmailMessage,send_mail

from django.shortcuts import redirect, render

from django.contrib.auth.models import User
from django.contrib.auth import authenticate,logout,login

from core import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes,force_str

from . tokens import generate_token
from django.contrib import messages
# Create your views here.
def index(request):
    return render(request,'users/index.html')
def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        
        if pass1!=pass2:
            messages.success(request, 'Password not match.')
            return redirect('signup')
        if User.objects.filter(username = username):
            messages.error(request, 'Username already exist.')
            return redirect('signup')
        if User.objects.filter(email = email):
            messages.error(request, 'Email already exist.')
            return redirect('signup')
        if len(username)>10:
            messages.error(request, 'Username most be under 10 character.')
            return redirect('signup')
        if not pass1.isalnum():
            messages.success(request, 'Password must contain number.')
            return redirect('signup')

        user = User.objects.create_user(username, email, pass1)
        user.first_name = fname
        user.last_name = lname
        user.is_active = False
        user.save()

        messages.success(request, 'You have successfully registered.')

        # welcome email
        subject = "Welcome to Simple Confirmation Site"
        message = f"Hello {user.first_name} \n Welcome to Ncode \n Thank you for signing up \n we have sent you a confirmation email, please confirm your email address in other to activate your account \n\n Thank you"
        from_email = settings.EMAIL_HOST_USER
        to_email = [user.email]
        send_mail(subject, message, from_email,to_email, fail_silently=True)
        
        # confirmation email
        current_site = get_current_site(request)
        email_sub = f"Confirm your email"
        message2 = render_to_string('emailconfirm.html',{
            'name':user.first_name,
            'domain':current_site.domain,
            'uid':urlsafe_base64_encode(force_bytes(user.pk)),
            'token': generate_token.make_token(user),
        })
        email = EmailMessage(
            email_sub,
            message2,
            settings.EMAIL_HOST_USER,
            [user.email],
        )
        email.fail_silently = True
        email.send()
        return redirect('signin')

    return render(request,'users/signup.html')


def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']

        user = authenticate(username=username, password = pass1)
        if user is not None:
            login(request,user)
            fname = user.first_name
            context={
                'fname':fname
            }
            return render (request,'users/index.html',context)
        else:
            messages.error(request, 'Username/Password not correct')
            return redirect('index')
    return render(request,'users/signin.html')

def signout(request):
    logout(request)
    messages.error(request, 'Logged out successfully')
    return redirect('index')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError,ValueError,OverflowError, User.DoesNotExist):
        user = None
    if user is not None and generate_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request,user)
        return redirect('index')
    else:
        return render(request, 'failed.html')
