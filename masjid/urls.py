from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # General
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('donate/<int:tabung_id>/', views.donate_form, name='donate_form'),
    path('donation/slip/pdf/<int:entry_id>/', views.download_slip_pdf, name='download_slip_pdf'),
   


 # President routes
    path('president/dashboard/', views.president_dashboard, name='president_dashboard'),
    path('president/create-ajk/', views.create_ajk, name='create_ajk'),
    path('president/create-tabung/', views.create_tabung, name='create_tabung'),  # ✅ keep only this
    path('president/edit-tabung/<int:tabung_id>/', views.edit_tabung, name='edit_tabung'),
    path('president/delete-tabung/<int:tabung_id>/', views.delete_tabung, name='delete_tabung'),
    path('president/disbursements/', views.approve_disbursement, name='approve_disbursement'),
    path('president/approve/<int:disbursement_id>/', views.approve_request, name='approve_request'),
    path('president/reject/<int:disbursement_id>/', views.reject_request, name='reject_request'),
    path('president/summary/', views.donation_summary, name='donation_summary'),
    path('president/approve-donation/<int:entry_id>/', views.approve_donation, name='approve_donation'),
    path('president/remove-donation/<int:entry_id>/', views.remove_donation, name='remove_donation'),




    # AJK routes
    path('ajk/dashboard/', views.ajk_dashboard, name='ajk_dashboard'),
    path('ajk/profile/', views.ajk_profile, name='ajk_profile'),
    path('ajk/disbursement/submit/', views.submit_disbursement, name='submit_disbursement'),
    path('ajk/disbursement/edit/<int:disbursement_id>/', views.edit_disbursement, name='edit_disbursement'),
    path('ajk/disbursement/cancel/<int:disbursement_id>/', views.cancel_disbursement, name='cancel_disbursement'),
    path('ajk/disbursements/', views.view_disbursements, name='view_disbursements'),
    path('ajk/summary/', views.ajk_donation_summary, name='ajk_donation_summary'),




]
