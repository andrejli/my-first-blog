"""
Admin Polling System - Phase 1: Simple URL Configuration
Basic routing for admin polls
"""
from django.urls import path

from . import views


app_name = 'secret_chamber'

urlpatterns = [
    # Main dashboard
    path('', views.admin_poll_dashboard, name='dashboard'),
    
    # Poll management
    path('polls/', views.poll_list, name='poll_list'),
    path('polls/create/', views.create_simple_poll, name='create_poll'),
    path('polls/<int:poll_id>/', views.poll_detail, name='poll_detail'),
    path('polls/<int:poll_id>/vote/', views.cast_simple_vote, name='cast_vote'),
    path('polls/<int:poll_id>/results/', views.poll_results, name='poll_results'),
    
    # API endpoints
    path('api/poll/<int:poll_id>/status/', views.poll_status_api, name='poll_status_api'),
]