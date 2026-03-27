from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from .models import User, Donation, DonationEntry, Disbursement

# Home Page (Donor view)
def home(request):
    tabung_list = Donation.objects.all()
    return render(request, 'home.html', {'tabung_list': tabung_list})

# Login
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        selected_role = request.POST.get('userRole')

        user = authenticate(request, username=username, password=password)
        if user:
            if user.role != selected_role:
                messages.error(request, "Login failed: Role mismatch.")
                return redirect('login')
            login(request, user)
            if user.role == 'president':
                return redirect('president_dashboard')
            elif user.role == 'ajk':
                return redirect('ajk_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')

    return render(request, 'login.html')

# President Dashboard
@login_required
def president_dashboard(request):
    return render(request, 'president_dashboard.html')

# AJK Dashboard
@login_required
def ajk_dashboard(request):
    return render(request, 'ajk_dashboard.html')

# Create AJK
@login_required
def create_ajk(request):
    if request.user.role != 'president':
        messages.error(request, "Only President can create AJK accounts.")
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        phone = request.POST.get('phone_number')
        email = request.POST.get('email')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            User.objects.create(
                username=username,
                password=make_password(password),
                role='ajk',
                phone_number=phone,
                email=email
            )
            messages.success(request, f"AJK '{username}' created successfully!")
            return redirect('president_dashboard')

    return render(request, 'create_ajk.html')

# Manage Tabung (Create)
@login_required
def create_tabung(request):
    if request.user.role != 'president':
        messages.error(request, "Only President can manage tabungs.")
        return redirect('home')

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        bank_account = request.POST.get('bank_account')
        qr_code = request.FILES.get('qr_code')

        if name:
            Donation.objects.create(
                name=name,
                description=description,
                bank_account=bank_account,
                qr_code=qr_code,
                created_by=request.user
            )
            messages.success(request, 'New tabung created!')
            return redirect('create_tabung')

    tabungs = Donation.objects.all()
    return render(request, 'create_tabung.html', {'tabungs': tabungs})

# Edit Tabung
@login_required
def edit_tabung(request, tabung_id):
    tabung = get_object_or_404(Donation, id=tabung_id)
    if request.user.role != 'president':
        return redirect('home')

    if request.method == 'POST':
        tabung.name = request.POST.get('name')
        tabung.description = request.POST.get('description')
        tabung.bank_account = request.POST.get('bank_account')
        if request.FILES.get('qr_code'):
            tabung.qr_code = request.FILES['qr_code']
        tabung.save()
        messages.success(request, 'Tabung updated.')
        return redirect('create_tabung')

    return render(request, 'edit_tabung.html', {'tabung': tabung})

# Delete Tabung
@login_required
def delete_tabung(request, tabung_id):
    tabung = get_object_or_404(Donation, id=tabung_id)
    if request.user.role == 'president':
        tabung.delete()
        messages.success(request, "Tabung deleted.")
    return redirect('create_tabung')

# Disbursement Approval
@login_required
def approve_disbursement(request):
    if request.user.role != 'president':
        return redirect('home')
    requests = Disbursement.objects.filter(is_approved=False, is_rejected=False)
    return render(request, 'approve_disbursement.html', {'requests': requests})

@login_required
def approve_request(request, disbursement_id):
    disb = get_object_or_404(Disbursement, id=disbursement_id)
    disb.is_approved = True
    disb.approved_by = request.user
    disb.save()
    messages.success(request, "Approved successfully.")
    return redirect('approve_disbursement')

@login_required
def reject_request(request, disbursement_id):
    disb = get_object_or_404(Disbursement, id=disbursement_id)
    disb.is_rejected = True
    disb.save()
    messages.info(request, "Rejected successfully.")
    return redirect('approve_disbursement')

# President Summary View
@login_required
def donation_summary(request):
    if request.user.role != 'president':
        return redirect('home')

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    tabungs = Donation.objects.all()
    entries = DonationEntry.objects.all()

    if start_date and end_date:
        entries = entries.filter(date__date__range=[start_date, end_date])

    return render(request, 'donation_summary.html', {
        'tabungs': tabungs,
        'donor_entries': entries,
        'start_date': start_date,
        'end_date': end_date
    })

# AJK Submit Disbursement
@login_required
def submit_disbursement(request):
    if request.user.role != 'ajk':
        return redirect('home')

    donations = Donation.objects.all()
    if request.method == 'POST':
        donation_id = request.POST.get('donation_type')
        amount = float(request.POST.get('amount'))
        purpose = request.POST.get('purpose')

        donation = get_object_or_404(Donation, id=donation_id)
        if amount > donation.remaining_balance:
            messages.error(request, "Not enough balance.")
        else:
            Disbursement.objects.create(
                donation_type=donation,
                amount=amount,
                purpose=purpose,
                requested_by=request.user
            )
            messages.success(request, "Disbursement submitted.")
            return redirect('ajk_dashboard')

    return render(request, 'submit_disbursement.html', {'donations': donations})

# AJK View Disbursement
@login_required
def view_disbursements(request):
    if request.user.role != 'ajk':
        return redirect('home')

    query = request.GET.get('q', '')
    disbursements = Disbursement.objects.filter(requested_by=request.user)
    if query:
        disbursements = disbursements.filter(purpose__icontains=query)
    disbursements = disbursements.order_by('-requested_at')
    return render(request, 'view_disbursements.html', {'disbursements': disbursements, 'query': query})

# AJK Cancel Disbursement
@login_required
def cancel_disbursement(request, disbursement_id):
    disb = get_object_or_404(Disbursement, id=disbursement_id, requested_by=request.user)
    if not disb.is_approved and not disb.is_rejected:
        disb.delete()
        messages.success(request, "Canceled.")
    return redirect('view_disbursements')

# AJK Edit Disbursement
@login_required
def edit_disbursement(request, disbursement_id):
    disb = get_object_or_404(Disbursement, id=disbursement_id, requested_by=request.user, is_approved=False)
    donations = Donation.objects.all()

    if request.method == 'POST':
        disb.donation_type = get_object_or_404(Donation, id=request.POST.get('donation_type'))
        disb.amount = request.POST.get('amount')
        disb.purpose = request.POST.get('purpose')
        disb.save()
        messages.success(request, "Updated.")
        return redirect('view_disbursements')

    return render(request, 'edit_disbursement.html', {'disbursement': disb, 'tabung_list': donations})

# AJK Profile
@login_required
def ajk_profile(request):
    if request.user.role != 'ajk':
        return redirect('home')

    if request.method == 'POST':
        request.user.first_name = request.POST.get('name')
        request.user.phone_number = request.POST.get('phone_number')
        new_pass = request.POST.get('new_password')
        if new_pass:
            request.user.set_password(new_pass)
            update_session_auth_hash(request, request.user)
        request.user.save()
        messages.success(request, "Profile updated.")
        return redirect('ajk_profile')

    return render(request, 'ajk_profile.html', {'user': request.user})

# AJK View Summary
@login_required
def ajk_donation_summary(request):
    if request.user.role != 'ajk':
        return redirect('home')

    tabungs = Donation.objects.all()
    return render(request, 'ajk_donation_summary.html', {'tabungs': tabungs})

# Donor View & Submit
def donate_form(request, tabung_id):
    tabung = get_object_or_404(Donation, id=tabung_id)

    if request.method == 'POST':
        name = request.POST.get('donor_name')
        phone = request.POST.get('phone_number')
        amount = request.POST.get('amount')
        receipt = request.FILES.get('receipt_image')

        if name and phone and amount and receipt:
            entry = DonationEntry.objects.create(
                donor_name=name,
                phone_number=phone,
                donation_type=tabung,
                amount=amount,
                receipt_image=receipt
            )
            return render(request, 'donation_slip.html', {'entry': entry, 'tabung': tabung})
        else:
            messages.error(request, "All fields are required.")

    return render(request, 'donate_form.html', {'tabung': tabung})

from django.template.loader import get_template
from xhtml2pdf import pisa
import io
def download_slip_pdf(request, entry_id):
    entry = get_object_or_404(DonationEntry, id=entry_id)
    template = get_template("donation_slip_pdf.html")
    html = template.render({"entry": entry})

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="donation_slip_{entry.id}.pdf"'

    pisa_status = pisa.CreatePDF(io.BytesIO(html.encode("UTF-8")), dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)

    return response

# views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

@login_required
def approve_donation(request, entry_id):
    if request.user.role != 'president':
        return redirect('home')

    entry = get_object_or_404(DonationEntry, id=entry_id)
    entry.is_approved = True
    entry.save()
    messages.success(request, "Donation approved.")
    return redirect('donation_summary')

@login_required
def remove_donation(request, entry_id):
    if request.user.role != 'president':
        return redirect('home')

    entry = get_object_or_404(DonationEntry, id=entry_id)
    entry.delete()
    messages.success(request, "Donation removed.")
    return redirect('donation_summary')
