from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = [
        ('president', 'President Masjid'),
        ('ajk', 'AJK Masjid'),
        ('donor', 'Donor'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

# 2. Donation/Tabung Model
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Donation(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    bank_account = models.CharField(max_length=50, blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'president'})
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_collected(self):
        return sum(entry.amount for entry in self.donationentry_set.all())

    @property
    def total_disbursed(self):
        return sum(d.amount for d in self.disbursement_set.filter(is_approved=True))

    @property
    def remaining_balance(self):
        return self.total_collected - self.total_disbursed

    def __str__(self):
        return self.name


# 3. Donor Submission (Donation Entry)
class DonationEntry(models.Model):
    donor_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    donation_type = models.ForeignKey(Donation, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_image = models.ImageField(upload_to='receipts/')
    date = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)  # ✅ new field

    def __str__(self):
        return f"{self.donor_name} - {self.donation_type.name}"


# 4. Disbursement Model (Handled by AJK, Approved by President)
class Disbursement(models.Model):
    donation_type = models.ForeignKey(Donation, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.TextField()
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'ajk'})
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approver', limit_choices_to={'role': 'president'})
    is_approved = models.BooleanField(default=False)
    requested_at = models.DateTimeField(auto_now_add=True)
    is_rejected = models.BooleanField(default=False)


    def __str__(self):
        return f"Disbursement: {self.amount} from {self.donation_type.name}"

