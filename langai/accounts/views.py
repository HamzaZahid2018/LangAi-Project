from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render
from .forms import RegisterForm, CustomLoginForm, OTPForm
from .models import OTPVerification, UserProfile


def send_otp_email(user, otp_obj):
    subject = 'Your LangAI Verification Code'
    message = f"""
Assalam-o-Alaikum {user.username}

Your LangAI Verification Code Is:

      {otp_obj.otp}

This OTP Expires In 1 Minute.
Do Not Share This Code With Anyone.

LangAI Team
"""
    # Always print OTP to console for easy dev access
    print(f"\n{'='*50}")
    print(f"[OTP] User: {user.username} | Email: {user.email}")
    print(f"[OTP] CODE: {otp_obj.otp}")
    print(f"{'='*50}\n")

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        print(f"[EMAIL] OTP sent successfully to {user.email}")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send OTP: {e}")
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegisterForm()

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, is_verified=True)
            
            # Auto-login after registration (no OTP)
            login(request, user)
            messages.success(
                request,
                f"Welcome to LangAI, {user.first_name or user.username}! 🎉"
            )
            return redirect('dashboard')
        else:
            messages.error(request, "Please fix the errors below.")

    return render(request, 'accounts/register.html', {'form': form})


def verify_otp_view(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        messages.warning(request, "Session expired. Please register or login again.")
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('register')

    form = OTPForm()

    if request.method == 'POST':
        # Resend OTP
        if 'resend' in request.POST:
            otp_obj = OTPVerification.create_for_user(user)
            send_otp_email(user, otp_obj)
            messages.info(request, "A new OTP has been sent to your email.")
            return redirect('verify_otp')

        form = OTPForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']

            # Get latest unused OTP
            latest_otp = OTPVerification.objects.filter(
                user=user, is_used=False
            ).first()

            if not latest_otp:
                messages.error(request, "No active OTP found. Please request a new one.")
            elif not latest_otp.is_valid():
                messages.error(request, "OTP has expired. Please request a new one.")
            elif latest_otp.otp != entered_otp:
                messages.error(request, "Incorrect OTP. Please try again.")
            else:
                # OTP correct — verify account
                latest_otp.is_used = True
                latest_otp.save()

                profile = user.profile
                profile.is_verified = True
                profile.save()

                # Clean session
                del request.session['otp_user_id']

                # Auto-login
                login(request, user)
                messages.success(request, f"Welcome to LangAI, {user.first_name or user.username}! 🎉")
                return redirect('dashboard')
        else:
            messages.error(request, "Please Enter A Valid 6-Digit OTP")

    context = {
        'form': form,
        'email': user.email,
        'masked_email': mask_email(user.email),
    }
    return render(request, 'accounts/verify_otp.html', context)


def mask_email(email):
    try:
        local, domain = email.split('@')
        masked = local[:2] + '***' + local[-1] if len(local) > 3 else local[:1] + '***'
        return f"{masked}@{domain}"
    except Exception:
        return email


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = CustomLoginForm()

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Create profile if doesn't exist
            UserProfile.objects.get_or_create(user=user)
            
            # Direct login - no OTP verification
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}! 👋")

            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')