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
            if poll.poll_type == 'multiple':
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
                # Single choice or yes/no
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


@login_required
@user_passes_test(superuser_required)
def poll_list(request):
    """List all polls with filtering and pagination"""
    
    polls = SecretPoll.objects.all()
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        polls = polls.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )
    elif status_filter == 'completed':
        polls = polls.filter(end_date__lt=timezone.now())
    elif status_filter == 'scheduled':
        polls = polls.filter(start_date__gt=timezone.now())
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        polls = polls.filter(poll_type=type_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        polls = polls.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(polls, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'poll_types': SecretPoll.POLL_TYPES,
        'current_filters': {
            'status': status_filter,
            'type': type_filter,
            'search': search_query,
        }
    }
    
    return render(request, 'secret_chamber/poll_list.html', context)


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
        request=request,
        metadata={'poll_id': poll.id}
    )
    
    # Check if user can vote
    can_vote = poll.can_user_vote(request.user)
    user_has_voted = not can_vote and poll.is_voting_open
    
    # Get poll options
    options = poll.options.all().order_by('order')
    
    # Get vote statistics (if allowed)
    vote_stats = None
    if ChamberPermissions.user_can_view_results(request.user, poll):
        vote_stats = calculate_poll_statistics(poll)
    
    context = {
        'poll': poll,
        'options': options,
        'can_vote': can_vote,
        'user_has_voted': user_has_voted,
        'vote_stats': vote_stats,
        'voting_open': poll.is_voting_open,
        'poll_completed': poll.is_completed,
    }
    
    return render(request, 'secret_chamber/poll_detail.html', context)


@login_required
@user_passes_test(superuser_required)
@require_http_methods(["POST"])
@csrf_protect
def cast_vote(request, poll_id):
    """Cast anonymous vote in a poll"""
    
    poll = get_object_or_404(SecretPoll, id=poll_id)
    
    # Verify user can vote
    if not poll.can_user_vote(request.user):
        messages.error(request, "You cannot vote in this poll.")
        return redirect('secret_chamber:poll_detail', poll_id=poll.id)
    
    try:
        with transaction.atomic():
            # Get vote data from form
            vote_data = {}
            
            if poll.poll_type == 'multiple_choice':
                selected_option = request.POST.get('option')
                if not selected_option:
                    messages.error(request, "Please select an option.")
                    return redirect('secret_chamber:poll_detail', poll_id=poll.id)
                
                vote_data = {
                    'type': 'multiple_choice',
                    'option_id': int(selected_option),
                    'timestamp': timezone.now().isoformat()
                }
            
            elif poll.poll_type == 'rating':
                rating = request.POST.get('rating')
                if not rating:
                    messages.error(request, "Please provide a rating.")
                    return redirect('secret_chamber:poll_detail', poll_id=poll.id)
                
                vote_data = {
                    'type': 'rating',
                    'rating': int(rating),
                    'timestamp': timezone.now().isoformat()
                }
            
            elif poll.poll_type == 'open_response':
                response = request.POST.get('response', '').strip()
                if not response:
                    messages.error(request, "Please provide a response.")
                    return redirect('secret_chamber:poll_detail', poll_id=poll.id)
                
                vote_data = {
                    'type': 'open_response',
                    'response': response,
                    'timestamp': timezone.now().isoformat()
                }
            
            elif poll.poll_type == 'ranking':
                # Handle ranked choices
                ranked_options = []
                for key, value in request.POST.items():
                    if key.startswith('rank_'):
                        option_id = int(key.split('_')[1])
                        rank = int(value)
                        ranked_options.append({'option_id': option_id, 'rank': rank})
                
                if not ranked_options:
                    messages.error(request, "Please rank the options.")
                    return redirect('secret_chamber:poll_detail', poll_id=poll.id)
                
                vote_data = {
                    'type': 'ranking',
                    'rankings': ranked_options,
                    'timestamp': timezone.now().isoformat()
                }
            
            elif poll.poll_type == 'approval':
                approval = request.POST.get('approval')
                if approval not in ['approve', 'reject', 'abstain']:
                    messages.error(request, "Please make a valid choice.")
                    return redirect('secret_chamber:poll_detail', poll_id=poll.id)
                
                vote_data = {
                    'type': 'approval',
                    'choice': approval,
                    'timestamp': timezone.now().isoformat()
                }
            
            # Add optional comment if allowed
            if poll.allow_comments:
                comment = request.POST.get('comment', '').strip()
                if comment:
                    vote_data['comment'] = comment
            
            # Create anonymous vote
            vote = AnonymousVote.create_vote(
                poll=poll,
                user=request.user,
                vote_content=vote_data,
                request=request
            )
            
            messages.success(request, "Your vote has been cast successfully!")
            
            # Check if poll should auto-complete
            if should_auto_complete_poll(poll):
                poll.is_active = False
                poll.save()
                messages.info(request, "Poll completed - all eligible voters have participated!")
    
    except Exception as e:
        messages.error(request, f"Error casting vote: {str(e)}")
    
    return redirect('secret_chamber:poll_detail', poll_id=poll.id)


@login_required
@user_passes_test(superuser_required)
def create_poll(request):
    """Create new poll"""
    
    if not ChamberPermissions.user_can_create_poll(request.user):
        return HttpResponseForbidden("You don't have permission to create polls.")
    
    if request.method == 'POST':
        form = PollCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    poll = form.save(commit=False)
                    poll.created_by = request.user
                    poll.save()
                    
                    # Create poll options
                    options_data = request.POST.getlist('options[]')
                    for i, option_text in enumerate(options_data):
                        if option_text.strip():
                            PollOption.objects.create(
                                poll=poll,
                                option_text=option_text.strip(),
                                order=i
                            )
                    
                    # Log poll creation
                    ChamberAuditLog.log_activity(
                        user=request.user,
                        action_type='poll_created',
                        description=f'Created poll: {poll.title}',
                        request=request,
                        metadata={'poll_id': poll.id}
                    )
                    
                    messages.success(request, f"Poll '{poll.title}' created successfully!")
                    return redirect('secret_chamber:poll_detail', poll_id=poll.id)
            
            except Exception as e:
                messages.error(request, f"Error creating poll: {str(e)}")
    
    else:
        form = PollCreationForm()
    
    context = {
        'form': form,
        'poll_types': SecretPoll.POLL_TYPES,
    }
    
    return render(request, 'secret_chamber/create_poll.html', context)


@login_required
@user_passes_test(superuser_required)
def poll_results(request, poll_id):
    """Display detailed poll results"""
    
    poll = get_object_or_404(SecretPoll, id=poll_id)
    
    # Check permission to view results
    if not ChamberPermissions.user_can_view_results(request.user, poll):
        return HttpResponseForbidden("Results not available yet.")
    
    # Log results access
    ChamberAuditLog.log_activity(
        user=request.user,
        action_type='results_viewed',
        description=f'Viewed results for: {poll.title}',
        request=request,
        metadata={'poll_id': poll.id}
    )
    
    # Calculate comprehensive statistics
    results = calculate_detailed_poll_results(poll)
    
    context = {
        'poll': poll,
        'results': results,
        'can_generate_report': True,
    }
    
    return render(request, 'secret_chamber/poll_results.html', context)


@login_required
@user_passes_test(superuser_required)
def reports_list(request):
    """List all generated reports"""
    
    reports = DecisionReport.objects.all().order_by('-generated_at')
    
    # Filter by type if requested
    report_type = request.GET.get('type')
    if report_type:
        reports = reports.filter(report_type=report_type)
    
    context = {
        'reports': reports,
        'report_types': DecisionReport.REPORT_TYPES,
    }
    
    return render(request, 'secret_chamber/reports_list.html', context)


@login_required
@user_passes_test(superuser_required)
def generate_report(request, poll_id):
    """Generate a new report for a poll"""
    
    poll = get_object_or_404(SecretPoll, id=poll_id)
    
    if request.method == 'POST':
        from .reports import create_poll_report
        
        include_comments = request.POST.get('include_comments') == 'on'
        include_statistics = request.POST.get('include_statistics') == 'on'
        
        report = create_poll_report(
            poll=poll,
            generated_by=request.user,
            include_comments=include_comments,
            include_statistics=include_statistics
        )
        
        messages.success(request, f"Report generated successfully!")
        return redirect('secret_chamber:view_report', report_id=report.id)
    
    context = {
        'poll': poll,
    }
    
    return render(request, 'secret_chamber/generate_report.html', context)


@login_required
@user_passes_test(superuser_required)
def view_report(request, report_id):
    """View a generated report"""
    
    report = get_object_or_404(DecisionReport, id=report_id)
    
    context = {
        'report': report,
    }
    
    return render(request, 'secret_chamber/view_report.html', context)


@login_required
@user_passes_test(superuser_required)
def export_report(request, report_id):
    """Export report as markdown file"""
    
    report = get_object_or_404(DecisionReport, id=report_id)
    
    from django.http import HttpResponse
    
    response = HttpResponse(report.report_content, content_type='text/markdown')
    response['Content-Disposition'] = f'attachment; filename="{report.title}.md"'
    
    return response


@login_required
@user_passes_test(superuser_required)
def chamber_analytics(request):
    """Chamber analytics dashboard"""
    
    context = {
        'title': 'Chamber Analytics',
    }
    
    return render(request, 'secret_chamber/analytics.html', context)


@login_required
@user_passes_test(superuser_required)
def participation_analytics(request):
    """Participation analytics"""
    
    context = {
        'title': 'Participation Analytics',
    }
    
    return render(request, 'secret_chamber/participation_analytics.html', context)


@login_required
@user_passes_test(superuser_required)
def trend_analytics(request):
    """Trend analytics"""
    
    context = {
        'title': 'Trend Analytics',
    }
    
    return render(request, 'secret_chamber/trend_analytics.html', context)


@login_required
@user_passes_test(superuser_required)
def audit_log(request):
    """View audit log"""
    
    logs = ChamberAuditLog.objects.all().order_by('-timestamp')[:100]
    
    context = {
        'logs': logs,
    }
    
    return render(request, 'secret_chamber/audit_log.html', context)


@login_required
@user_passes_test(superuser_required)
def security_settings(request):
    """Security settings page"""
    
    context = {
        'title': 'Security Settings',
    }
    
    return render(request, 'secret_chamber/security_settings.html', context)


# API Views
@login_required
@user_passes_test(superuser_required)
def poll_status_api(request, poll_id):
    """API endpoint for poll status"""
    
    poll = get_object_or_404(SecretPoll, id=poll_id)
    
    data = {
        'voting_open': poll.is_voting_open,
        'completed': poll.is_completed,
        'total_votes': poll.total_votes,
        'participation_rate': poll.participation_rate,
    }
    
    return JsonResponse(data)


@login_required
@user_passes_test(superuser_required)
def poll_stats_api(request, poll_id):
    """API endpoint for poll statistics"""
    
    poll = get_object_or_404(SecretPoll, id=poll_id)
    stats = calculate_poll_statistics(poll)
    
    return JsonResponse(stats)


@login_required
@user_passes_test(superuser_required)
def chamber_activity_api(request):
    """API endpoint for chamber activity"""
    
    # Check if there's new activity since last check
    last_check = request.GET.get('last_check')
    
    data = {
        'needs_refresh': False,
        'active_polls': SecretPoll.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).count(),
    }
    
    return JsonResponse(data)


# Helper Functions
def calculate_user_participation_rate(user):
    """Calculate user's participation rate in polls"""
    eligible_polls = SecretPoll.objects.filter(
        start_date__lte=timezone.now()
    ).count()
    
    if eligible_polls == 0:
        return 0
    
    # This is simplified - in real implementation would need to check actual votes
    participated_polls = 5  # Placeholder
    return (participated_polls / eligible_polls) * 100


def calculate_poll_statistics(poll):
    """Calculate basic poll statistics"""
    total_votes = poll.total_votes
    eligible_voters = poll.eligible_voters.count()
    
    return {
        'total_votes': total_votes,
        'eligible_voters': eligible_voters,
        'participation_rate': poll.participation_rate,
        'meets_quorum': poll.meets_quorum,
    }


def calculate_detailed_poll_results(poll):
    """Calculate comprehensive poll results"""
    votes = poll.votes.all()
    results = {
        'total_votes': len(votes),
        'participation_rate': poll.participation_rate,
        'vote_breakdown': {},
        'statistics': {},
        'timeline': []
    }
    
    # Decrypt and analyze votes
    decrypted_votes = []
    for vote in votes:
        try:
            vote_data = vote.decrypt_vote_data()
            if vote_data:
                decrypted_votes.append({
                    'data': vote_data,
                    'timestamp': vote.timestamp
                })
        except:
            continue
    
    # Analyze based on poll type
    if poll.poll_type == 'multiple_choice':
        option_counts = {}
        for vote in decrypted_votes:
            option_id = vote['data'].get('option_id')
            if option_id:
                option_counts[option_id] = option_counts.get(option_id, 0) + 1
        
        results['vote_breakdown'] = option_counts
    
    elif poll.poll_type == 'rating':
        ratings = [vote['data'].get('rating', 0) for vote in decrypted_votes]
        if ratings:
            results['statistics'] = {
                'average_rating': sum(ratings) / len(ratings),
                'min_rating': min(ratings),
                'max_rating': max(ratings),
                'rating_distribution': {i: ratings.count(i) for i in range(1, 11)}
            }
    
    elif poll.poll_type == 'approval':
        choices = [vote['data'].get('choice') for vote in decrypted_votes]
        results['vote_breakdown'] = {
            'approve': choices.count('approve'),
            'reject': choices.count('reject'),
            'abstain': choices.count('abstain')
        }
    
    # Timeline analysis
    results['timeline'] = [
        {
            'date': vote['timestamp'].date(),
            'hour': vote['timestamp'].hour,
        }
        for vote in decrypted_votes
    ]
    
    return results


def should_auto_complete_poll(poll):
    """Check if poll should be automatically completed"""
    if not poll.require_all_admins:
        return False
    
    eligible_voters = poll.eligible_voters.count()
    total_votes = poll.total_votes
    
    return total_votes >= eligible_voters