"""
Admin Polling System - Phase 1: Simple Views
Basic admin polling without complex encryption
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User

from .models import AdminPoll, PollOption, AdminVote, AdminPollReport, AdminPollAudit


def superuser_required(user):
    """Check if user is a superuser"""
    return user.is_superuser


@login_required
@user_passes_test(superuser_required, login_url='/admin/login/')
def admin_poll_dashboard(request):
    """Simple admin polling dashboard"""
    
    # Log access
    AdminPollAudit.objects.create(
        user=request.user,
        action='poll_accessed',
        description='Accessed admin polling dashboard'
    )
    
    # Get active polls
    active_polls = AdminPoll.objects.filter(
        is_active=True,
        end_date__gte=timezone.now()
    ).order_by('end_date')[:5]
    
    # Get recent polls
    recent_polls = AdminPoll.objects.filter(
        end_date__lt=timezone.now()
    ).order_by('-end_date')[:5]
    
    # Get polls user can vote in
    user_can_vote_polls = []
    for poll in active_polls:
        if poll.can_user_vote(request.user):
            user_can_vote_polls.append(poll)
    
    # Calculate stats
    total_polls = AdminPoll.objects.count()
    total_votes = AdminVote.objects.count()
    user_votes = AdminVote.objects.filter(voter=request.user).count()
    
    context = {
        'active_polls': active_polls,
        'recent_polls': recent_polls,
        'user_can_vote_polls': user_can_vote_polls,
        'total_polls': total_polls,
        'total_votes': total_votes,
        'user_votes': user_votes,
        'stats': {
            'active_count': len(active_polls),
            'pending_votes': len(user_can_vote_polls),
        }
    }
    
    return render(request, 'secret_chamber/simple_dashboard.html', context)


@login_required
@user_passes_test(superuser_required)
def poll_detail(request, poll_id):
    """Display poll details and voting interface"""
    
    poll = get_object_or_404(AdminPoll, id=poll_id)
    
    # Log poll access
    AdminPollAudit.objects.create(
        user=request.user,
        action='poll_viewed',
        description=f'Viewed poll: {poll.title}',
        poll_id=poll.id
    )
    
    # Check if user has already voted
    user_vote = AdminVote.objects.filter(poll=poll, voter=request.user).first()
    
    context = {
        'poll': poll,
        'user_vote': user_vote,
    }
    
    return render(request, 'secret_chamber/poll_detail.html', context)


@login_required
@user_passes_test(superuser_required)
@require_http_methods(["POST"])
@csrf_protect
def cast_simple_vote(request, poll_id):
    """Cast vote in a poll - Phase 1 implementation"""
    
    poll = get_object_or_404(AdminPoll, id=poll_id)
    
    # Check if user can vote
    if not poll.can_user_vote(request.user):
        messages.error(request, "You cannot vote in this poll.")
        return redirect('secret_chamber:poll_detail', poll_id=poll.id)
    
    try:
        with transaction.atomic():
            if poll.poll_type == 'open_response':
                # Open response - save text response
                response_text = request.POST.get('response_text', '').strip()
                if not response_text:
                    messages.error(request, "Please provide a response.")
                    return redirect('secret_chamber:poll_detail', poll_id=poll.id)
                
                # Create vote with text response
                AdminVote.objects.create(
                    poll=poll,
                    voter=request.user,
                    text_response=response_text
                )
                
            elif poll.poll_type == 'multiple_choice':
                # Multiple choice - can select multiple options
                option_ids = request.POST.getlist('options')
                if not option_ids:
                    messages.error(request, "Please select at least one option.")
                    return redirect('secret_chamber:poll_detail', poll_id=poll.id)
                
                # Create votes for each selected option
                for option_id in option_ids:
                    option = get_object_or_404(PollOption, id=option_id, poll=poll)
                    AdminVote.objects.create(
                        poll=poll,
                        voter=request.user,
                        selected_option=option
                    )
            
            else:
                # Single choice, yes/no, or rating
                option_id = request.POST.get('option')
                if not option_id:
                    messages.error(request, "Please select an option.")
                    return redirect('secret_chamber:poll_detail', poll_id=poll.id)
                
                option = get_object_or_404(PollOption, id=option_id, poll=poll)
                AdminVote.objects.create(
                    poll=poll,
                    voter=request.user,
                    selected_option=option
                )
            
            # Log the vote
            AdminPollAudit.objects.create(
                user=request.user,
                action='vote_cast',
                poll=poll,
                description=f'Cast vote in poll: {poll.title}'
            )
            
            messages.success(request, "Your vote has been recorded successfully!")
    
    except Exception as e:
        messages.error(request, f"Error recording vote: {str(e)}")
    
    return redirect('secret_chamber:poll_detail', poll_id=poll.id)


@login_required
@user_passes_test(superuser_required)
def create_simple_poll(request):
    """Create new simple poll"""
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create poll
                poll = AdminPoll(
                    title=request.POST.get('title', '').strip(),
                    description=request.POST.get('description', '').strip(),
                    poll_type=request.POST.get('poll_type', 'single'),
                    created_by=request.user,
                    show_results=request.POST.get('show_results') == 'true',
                    allow_comments=request.POST.get('allow_comments') == 'true'
                )
                
                # Set end date
                end_date_str = request.POST.get('end_date')
                if end_date_str:
                    from datetime import datetime
                    poll.end_date = datetime.fromisoformat(end_date_str.replace('T', ' '))
                else:
                    # Default to 7 days from now
                    from datetime import timedelta
                    poll.end_date = timezone.now() + timedelta(days=7)
                
                poll.save()
                
                # Create options
                option_count = 1
                while f'option_{option_count}' in request.POST:
                    option_text = request.POST.get(f'option_{option_count}', '').strip()
                    if option_text:
                        PollOption.objects.create(
                            poll=poll,
                            text=option_text,
                            order=option_count
                        )
                    option_count += 1
                
                # Log poll creation
                AdminPollAudit.objects.create(
                    user=request.user,
                    action='poll_created',
                    poll=poll,
                    description=f'Created poll: {poll.title}'
                )
                
                messages.success(request, f"Poll '{poll.title}' created successfully!")
                return redirect('secret_chamber:poll_detail', poll_id=poll.id)
                
        except Exception as e:
            messages.error(request, f"Error creating poll: {str(e)}")
    
    context = {
        'poll_types': AdminPoll.POLL_TYPES,
    }
    
    return render(request, 'secret_chamber/create_poll.html', context)


@login_required
@user_passes_test(superuser_required)
def poll_list(request):
    """List all polls"""
    
    polls = AdminPoll.objects.all().order_by('-created_at')
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'active':
        polls = polls.filter(is_active=True, end_date__gte=timezone.now())
    elif status == 'closed':
        polls = polls.filter(end_date__lt=timezone.now())
    
    context = {
        'polls': polls,
        'current_status': status,
    }
    
    return render(request, 'secret_chamber/simple_poll_list.html', context)


@login_required
@user_passes_test(superuser_required)
def poll_results(request, poll_id):
    """Display poll results"""
    
    poll = get_object_or_404(AdminPoll, id=poll_id)
    
    context = {
        'poll': poll,
    }
    
    return render(request, 'secret_chamber/poll_detail.html', context)


# API endpoints for AJAX
@login_required
@user_passes_test(superuser_required)
def poll_status_api(request, poll_id):
    """API endpoint for poll status"""
    
    poll = get_object_or_404(AdminPoll, id=poll_id)
    
    data = {
        'is_active': poll.is_active,
        'total_votes': poll.votes.count(),
        'can_user_vote': poll.can_user_vote(request.user),
    }
    
    return JsonResponse(data)
