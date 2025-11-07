"""
Comprehensive pytest tests for the Secret Chamber Admin Polling System
Tests cover models, views, security, voting, and results functionality
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta, datetime
from unittest.mock import patch, MagicMock
import json

from blog.secret_chamber.models import AdminPoll, PollOption, AdminVote, AdminPollAudit
from blog.secret_chamber.views import superuser_required


# Module-level fixtures for all test classes
@pytest.fixture
def superuser(db):
    """Create a superuser for testing"""
    return User.objects.create_user(
        username='admin_test',
        email='admin@test.com',
        password='SecureTestPass123!',  # Enhanced password for Django validation
        is_superuser=True,
        is_staff=True
    )

@pytest.fixture
def regular_user(db):
    """Create a regular user for testing"""
    return User.objects.create_user(
        username='regular_test',
        email='regular@test.com',
        password='SecureTestPass123!',  # Enhanced password for Django validation
        is_superuser=False,
        is_staff=False
    )

@pytest.fixture
def future_date():
    """Get a future date for poll end dates"""
    return timezone.now() + timedelta(days=7)

@pytest.fixture
def past_date():
    """Get a past date for poll end dates"""
    return timezone.now() - timedelta(days=1)


class TestAdminPollModel:
    """Test the AdminPoll model functionality"""
    
    @pytest.fixture
    def active_poll(self, db, superuser, future_date):
        """Create an active poll for testing"""
        return AdminPoll.objects.create(
            title="Test Active Poll",
            description="This is a test poll",
            poll_type="multiple_choice",
            created_by=superuser,
            end_date=future_date,
            is_active=True
        )
    
    @pytest.fixture
    def closed_poll(self, db, superuser, past_date):
        """Create a closed poll for testing"""
        return AdminPoll.objects.create(
            title="Test Closed Poll",
            description="This is a closed test poll",
            poll_type="yes_no",
            created_by=superuser,
            end_date=past_date,
            is_active=True
        )
    
    def test_poll_creation(self, db, superuser, future_date):
        """Test basic poll creation"""
        poll = AdminPoll.objects.create(
            title="Test Poll Creation",
            description="Testing poll creation functionality",
            poll_type="rating",
            created_by=superuser,
            end_date=future_date,
            is_active=True,
            allow_comments=True
        )
        
        assert poll.title == "Test Poll Creation"
        assert poll.poll_type == "rating"
        assert poll.created_by == superuser
        assert poll.is_active is True
        assert poll.allow_comments is True
        assert str(poll) == "Test Poll Creation"
    
    def test_poll_validation_future_date(self, db, superuser):
        """Test that poll end date must be in the future"""
        past_date = timezone.now() - timedelta(days=1)
        
        poll = AdminPoll(
            title="Invalid Date Poll",
            description="This poll has an invalid end date",
            poll_type="multiple_choice",
            created_by=superuser,
            end_date=past_date,
            is_active=True
        )
        
        with pytest.raises(ValidationError):
            poll.clean()
    
    def test_poll_is_open_property(self, active_poll, closed_poll):
        """Test the is_open property"""
        assert active_poll.is_open is True
        assert closed_poll.is_open is False
    
    def test_poll_is_completed_property(self, active_poll, closed_poll):
        """Test the is_completed property"""
        assert active_poll.is_completed is False
        assert closed_poll.is_completed is True
    
    def test_poll_can_user_vote(self, active_poll, closed_poll, superuser, regular_user):
        """Test voting permissions"""
        # Superuser can vote in active poll
        assert active_poll.can_user_vote(superuser) is True
        
        # Superuser cannot vote in closed poll
        assert closed_poll.can_user_vote(superuser) is False
        
        # Regular user cannot vote (not superuser)
        assert active_poll.can_user_vote(regular_user) is False
    
    def test_poll_eligible_voters(self, active_poll, superuser, regular_user):
        """Test eligible voters property"""
        # Create another superuser
        super2 = User.objects.create_user(
            username='admin2',
            email='admin2@test.com',
            password='test123',
            is_superuser=True,
            is_active=True
        )
        
        eligible_voters = active_poll.eligible_voters
        assert superuser in eligible_voters
        assert super2 in eligible_voters
        assert regular_user not in eligible_voters
        assert eligible_voters.count() == 2
    
    def test_poll_security_modification_prevention(self, db, superuser, future_date):
        """Test that polls cannot be modified after voting starts"""
        poll = AdminPoll.objects.create(
            title="Security Test Poll",
            description="Testing security features",
            poll_type="multiple_choice",
            created_by=superuser,
            end_date=future_date
        )
        
        # Create a poll option
        option = PollOption.objects.create(
            poll=poll,
            option_text="Test Option",
            order=1
        )
        
        # Cast a vote
        AdminVote.objects.create(
            poll=poll,
            voter=superuser,
            selected_option=option
        )
        
        # Try to modify the poll
        poll.title = "Modified Title"
        
        with pytest.raises(ValidationError):
            poll.clean()


class TestPollOptionModel:
    """Test PollOption model functionality"""
    
    @pytest.fixture
    def poll_with_options(self, db, superuser, future_date):
        """Create a poll with multiple options"""
        poll = AdminPoll.objects.create(
            title="Poll With Options",
            description="Testing poll options",
            poll_type="multiple_choice",
            created_by=superuser,
            end_date=future_date
        )
        
        # Create options
        option1 = PollOption.objects.create(
            poll=poll,
            option_text="Option 1",
            order=1
        )
        option2 = PollOption.objects.create(
            poll=poll,
            option_text="Option 2",
            order=2
        )
        
        return poll, option1, option2
    
    def test_option_creation(self, poll_with_options):
        """Test poll option creation"""
        poll, option1, option2 = poll_with_options
        
        assert option1.poll == poll
        assert option1.option_text == "Option 1"
        assert option1.order == 1
        assert str(option1) == "Poll With Options: Option 1"
    
    def test_option_vote_count(self, poll_with_options, superuser):
        """Test option vote counting"""
        poll, option1, option2 = poll_with_options
        
        # Initially no votes
        assert option1.vote_count == 0
        assert option2.vote_count == 0
        
        # Cast vote for option1
        AdminVote.objects.create(
            poll=poll,
            voter=superuser,
            selected_option=option1
        )
        
        assert option1.vote_count == 1
        assert option2.vote_count == 0
    
    def test_unique_option_text_per_poll(self, poll_with_options):
        """Test that option text must be unique within a poll"""
        poll, option1, option2 = poll_with_options
        
        # Try to create duplicate option
        with pytest.raises(Exception):  # IntegrityError in real database
            PollOption.objects.create(
                poll=poll,
                option_text="Option 1",  # Duplicate text
                order=3
            )


class TestAdminVoteModel:
    """Test AdminVote model functionality"""
    
    @pytest.fixture
    def vote_setup(self, db, superuser, future_date):
        """Set up poll and options for voting tests"""
        poll = AdminPoll.objects.create(
            title="Vote Test Poll",
            description="Testing voting functionality",
            poll_type="multiple_choice",
            created_by=superuser,
            end_date=future_date
        )
        
        option = PollOption.objects.create(
            poll=poll,
            option_text="Test Vote Option",
            order=1
        )
        
        return poll, option, superuser
    
    def test_vote_creation(self, vote_setup):
        """Test basic vote creation"""
        poll, option, voter = vote_setup
        
        vote = AdminVote.objects.create(
            poll=poll,
            voter=voter,
            selected_option=option
        )
        
        assert vote.poll == poll
        assert vote.voter == voter
        assert vote.selected_option == option
        assert str(vote) == f"{voter.username} voted on {poll.title}"
    
    def test_one_vote_per_user_per_poll(self, vote_setup):
        """Test that users can only vote once per poll"""
        poll, option, voter = vote_setup
        
        # Create first vote
        AdminVote.objects.create(
            poll=poll,
            voter=voter,
            selected_option=option
        )
        
        # Try to create second vote by same user
        with pytest.raises(Exception):  # IntegrityError in real database
            AdminVote.objects.create(
                poll=poll,
                voter=voter,
                selected_option=option
            )
    
    def test_rating_vote_validation(self, db, superuser, future_date):
        """Test rating vote validation"""
        poll = AdminPoll.objects.create(
            title="Rating Poll",
            description="Testing rating validation",
            poll_type="rating",
            created_by=superuser,
            end_date=future_date
        )
        
        # Valid rating vote
        valid_vote = AdminVote(
            poll=poll,
            voter=superuser,
            rating_value=5
        )
        valid_vote.clean()  # Should not raise
        
        # Invalid rating vote (out of range)
        invalid_vote = AdminVote(
            poll=poll,
            voter=superuser,
            rating_value=15  # Invalid: > 10
        )
        
        with pytest.raises(ValidationError):
            invalid_vote.clean()
    
    def test_open_response_vote(self, db, superuser, future_date):
        """Test open response voting"""
        poll = AdminPoll.objects.create(
            title="Open Response Poll",
            description="Testing open response",
            poll_type="open_response",
            created_by=superuser,
            end_date=future_date
        )
        
        vote = AdminVote.objects.create(
            poll=poll,
            voter=superuser,
            text_response="This is my open response answer."
        )
        
        assert vote.text_response == "This is my open response answer."
        assert vote.selected_option is None
        assert vote.rating_value is None


class TestPollingViews:
    """Test polling system views"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return Client()
    
    @pytest.fixture
    def view_regular_user(self, db):
        """Create regular user for view testing"""
        return User.objects.create_user(
            username='regular_view_test',
            email='regular_view@test.com',
            password='SecureTestPass123!',  # Enhanced password for Django validation
            is_superuser=False
        )
    
    @pytest.fixture
    def test_poll(self, db, superuser):
        """Create test poll for view testing"""
        future_date = timezone.now() + timedelta(days=7)
        poll = AdminPoll.objects.create(
            title="View Test Poll",
            description="Testing poll views",
            poll_type="multiple_choice",
            created_by=superuser,
            end_date=future_date
        )
        
        # Add options
        PollOption.objects.create(
            poll=poll,
            option_text="Option A",
            order=1
        )
        PollOption.objects.create(
            poll=poll,
            option_text="Option B",
            order=2
        )
        
        return poll
    
    def test_dashboard_requires_superuser(self, client, regular_user):
        """Test that dashboard requires superuser access"""
        client.force_login(regular_user)
        
        response = client.get(reverse('secret_chamber:dashboard'))
        
        # Should redirect to admin login
        assert response.status_code == 302
        assert '/admin/login/' in response.url
    
    def test_dashboard_superuser_access(self, client, superuser):
        """Test that superusers can access dashboard"""
        client.force_login(superuser)
        
        response = client.get(reverse('secret_chamber:dashboard'))
        
        assert response.status_code == 200
        assert 'active_polls' in response.context
        assert 'recent_polls' in response.context
    
    def test_poll_detail_view(self, client, superuser, test_poll):
        """Test poll detail view"""
        client.force_login(superuser)
        
        response = client.get(
            reverse('secret_chamber:poll_detail', kwargs={'poll_id': test_poll.id})
        )
        
        assert response.status_code == 200
        assert response.context['poll'] == test_poll
        assert 'user_vote' in response.context
    
    def test_poll_creation_view_get(self, client, superuser):
        """Test poll creation form display"""
        client.force_login(superuser)
        
        response = client.get(reverse('secret_chamber:create_poll'))
        
        assert response.status_code == 200
        assert 'poll_types' in response.context
    
    def test_poll_creation_view_post(self, client, superuser):
        """Test poll creation via POST"""
        client.force_login(superuser)
        
        future_date = (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M')
        
        data = {
            'title': 'Test Created Poll',
            'description': 'This poll was created via test',
            'poll_type': 'multiple_choice',
            'end_date': future_date,
            'allow_comments': 'true',
            'option_1': 'First Option',
            'option_2': 'Second Option',
        }
        
        response = client.post(reverse('secret_chamber:create_poll'), data)
        
        # Should redirect to poll detail
        assert response.status_code == 302
        
        # Check poll was created
        poll = AdminPoll.objects.get(title='Test Created Poll')
        assert poll.description == 'This poll was created via test'
        assert poll.poll_type == 'multiple_choice'
        assert poll.created_by == superuser
        
        # Check options were created
        options = list(poll.options.all())
        assert len(options) == 2
        assert options[0].option_text == 'First Option'
        assert options[1].option_text == 'Second Option'
    
    def test_voting_functionality(self, client, superuser, test_poll):
        """Test voting via POST request"""
        client.force_login(superuser)
        
        option = test_poll.options.first()
        
        # For multiple_choice polls, use 'options' (plural) as expected by the view
        data = {
            'options': [option.id]
        }
        
        response = client.post(
            reverse('secret_chamber:cast_vote', kwargs={'poll_id': test_poll.id}),
            data
        )
        
        # Should redirect back to poll detail
        assert response.status_code == 302
        
        # Check vote was recorded
        vote = AdminVote.objects.get(poll=test_poll, voter=superuser)
        assert vote.selected_option == option
    
    def test_open_response_voting(self, client, superuser):
        """Test open response voting"""
        client.force_login(superuser)
        
        # Create open response poll
        future_date = timezone.now() + timedelta(days=7)
        poll = AdminPoll.objects.create(
            title="Open Response Test",
            description="Testing open response voting",
            poll_type="open_response",
            created_by=superuser,
            end_date=future_date
        )
        
        data = {
            'response_text': 'This is my detailed response to the poll question.'
        }
        
        response = client.post(
            reverse('secret_chamber:cast_vote', kwargs={'poll_id': poll.id}),
            data
        )
        
        assert response.status_code == 302
        
        # Check vote was recorded
        vote = AdminVote.objects.get(poll=poll, voter=superuser)
        assert vote.text_response == 'This is my detailed response to the poll question.'
    
    def test_double_voting_prevention(self, client, superuser, test_poll):
        """Test that users cannot vote twice"""
        client.force_login(superuser)
        
        option = test_poll.options.first()
        
        # First vote - use 'options' (plural) for multiple_choice poll type
        data = {'options': [option.id]}
        response1 = client.post(
            reverse('secret_chamber:cast_vote', kwargs={'poll_id': test_poll.id}),
            data
        )
        assert response1.status_code == 302
        
        # Second vote attempt
        response2 = client.post(
            reverse('secret_chamber:cast_vote', kwargs={'poll_id': test_poll.id}),
            data
        )
        assert response2.status_code == 302
        
        # Should still only have one vote
        votes = AdminVote.objects.filter(poll=test_poll, voter=superuser)
        assert votes.count() == 1
    
    def test_poll_list_view(self, client, superuser, test_poll):
        """Test poll listing view"""
        client.force_login(superuser)
        
        response = client.get(reverse('secret_chamber:poll_list'))
        
        assert response.status_code == 200
        assert test_poll in response.context['polls']
    
    def test_poll_results_display(self, client, superuser, test_poll):
        """Test poll results are displayed correctly"""
        # Close the poll to show results
        test_poll.end_date = timezone.now() - timedelta(hours=1)
        test_poll.save()
        
        client.force_login(superuser)
        
        response = client.get(
            reverse('secret_chamber:poll_detail', kwargs={'poll_id': test_poll.id})
        )
        
        assert response.status_code == 200
        assert response.context['poll'].is_completed is True


class TestPollingSecurityFeatures:
    """Test security features of the polling system"""
    
    @pytest.fixture
    def security_setup(self, db):
        """Set up users and polls for security testing"""
        superuser = User.objects.create_user(
            username='security_admin',
            email='security@test.com',
            password='SecureTestPass123!',  # Enhanced password for Django validation
            is_superuser=True
        )
        
        regular_user = User.objects.create_user(
            username='security_regular',
            email='security_regular@test.com',
            password='SecureTestPass123!',  # Enhanced password for Django validation
            is_superuser=False
        )
        
        future_date = timezone.now() + timedelta(days=7)
        poll = AdminPoll.objects.create(
            title="Security Test Poll",
            description="Testing security features",
            poll_type="multiple_choice",
            created_by=superuser,
            end_date=future_date
        )
        
        option = PollOption.objects.create(
            poll=poll,
            option_text="Security Option",
            order=1
        )
        
        return superuser, regular_user, poll, option
    
    def test_audit_log_creation(self, security_setup):
        """Test that audit logs are created for actions"""
        superuser, regular_user, poll, option = security_setup
        
        # Create a vote
        vote = AdminVote.objects.create(
            poll=poll,
            voter=superuser,
            selected_option=option
        )
        
        # Check if audit log can be created
        audit = AdminPollAudit.objects.create(
            user=superuser,
            action='vote_cast',
            poll=poll,
            description=f'Cast vote in poll: {poll.title}'
        )
        
        assert audit.user == superuser
        assert audit.action == 'vote_cast'
        assert audit.poll == poll
        assert str(audit) == f"{superuser.username} - vote_cast at {audit.timestamp}"
    
    def test_superuser_required_decorator(self):
        """Test the superuser_required function"""
        # Create mock users
        superuser = MagicMock()
        superuser.is_superuser = True
        
        regular_user = MagicMock()
        regular_user.is_superuser = False
        
        # Test superuser passes
        assert superuser_required(superuser) is True
        
        # Test regular user fails
        assert superuser_required(regular_user) is False
    
    def test_poll_tampering_protection(self, security_setup):
        """Test that polls cannot be tampered with after voting"""
        superuser, regular_user, poll, option = security_setup
        
        # Cast a vote
        AdminVote.objects.create(
            poll=poll,
            voter=superuser,
            selected_option=option
        )
        
        # Try to modify critical poll fields
        original_title = poll.title
        poll.title = "Tampered Title"
        
        with pytest.raises(ValidationError):
            poll.clean()
        
        # Poll should remain unchanged
        poll.refresh_from_db()
        assert poll.title == original_title
    
    def test_unauthorized_access_blocked(self, client):
        """Test that unauthorized users cannot access polling views"""
        # Test without login
        response = client.get(reverse('secret_chamber:dashboard'))
        assert response.status_code == 302  # Redirect to login
        
        # Test with regular user
        regular_user = User.objects.create_user(
            username='unauthorized',
            email='unauthorized@test.com',
            password='SecureTestPass123!',  # Enhanced password for Django validation
            is_superuser=False
        )
        
        client.force_login(regular_user)
        response = client.get(reverse('secret_chamber:dashboard'))
        assert response.status_code == 302  # Redirect to admin login


class TestPollingIntegration:
    """Integration tests for the complete polling workflow"""
    
    def test_complete_polling_workflow(self, client, db):
        """Test the complete polling workflow from creation to results"""
        # Create superuser
        admin = User.objects.create_user(
            username='workflow_admin',
            email='workflow@test.com',
            password='testpass123',
            is_superuser=True
        )
        
        # Create second superuser for voting
        admin2 = User.objects.create_user(
            username='workflow_admin2',
            email='workflow2@test.com',
            password='testpass123',
            is_superuser=True
        )
        
        client.force_login(admin)
        
        # 1. Create poll
        future_date = (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M')
        poll_data = {
            'title': 'Workflow Test Poll',
            'description': 'Complete workflow integration test',
            'poll_type': 'multiple_choice',
            'end_date': future_date,
            'allow_comments': 'true',
            'option_1': 'Workflow Option A',
            'option_2': 'Workflow Option B',
        }
        
        response = client.post(reverse('secret_chamber:create_poll'), poll_data)
        assert response.status_code == 302
        
        # Get created poll
        poll = AdminPoll.objects.get(title='Workflow Test Poll')
        assert poll.options.count() == 2
        
        # 2. Vote as first admin
        option_a = poll.options.get(option_text='Workflow Option A')
        vote_data = {'options': [option_a.id]}  # Use 'options' (plural) for multiple_choice poll
        
        response = client.post(
            reverse('secret_chamber:cast_vote', kwargs={'poll_id': poll.id}),
            vote_data
        )
        assert response.status_code == 302
        
        # 3. Vote as second admin
        client.force_login(admin2)
        option_b = poll.options.get(option_text='Workflow Option B')
        vote_data = {'options': [option_b.id]}  # Use 'options' (plural) for multiple_choice poll
        
        response = client.post(
            reverse('secret_chamber:cast_vote', kwargs={'poll_id': poll.id}),
            vote_data
        )
        assert response.status_code == 302
        
        # 4. Check results
        poll.refresh_from_db()
        assert poll.total_votes == 2
        assert option_a.vote_count == 1
        assert option_b.vote_count == 1
        assert poll.participation_rate == 100.0
        
        # 5. View results page
        response = client.get(
            reverse('secret_chamber:poll_detail', kwargs={'poll_id': poll.id})
        )
        assert response.status_code == 200
        assert response.context['poll'].can_view_results is True
    
    def test_early_results_with_100_percent_participation(self, client, db):
        """Test that results show early when all eligible voters have voted"""
        # Create single superuser (100% of eligible voters)
        admin = User.objects.create_user(
            username='early_results_admin',
            email='early@test.com',
            password='testpass123',
            is_superuser=True
        )
        
        client.force_login(admin)
        
        # Create poll with future end date
        future_date = timezone.now() + timedelta(days=7)
        poll = AdminPoll.objects.create(
            title="Early Results Test",
            description="Testing early results display",
            poll_type="yes_no",
            created_by=admin,
            end_date=future_date
        )
        
        option = PollOption.objects.create(
            poll=poll,
            option_text="Yes",
            order=1
        )
        
        # Vote (this is 100% participation)
        AdminVote.objects.create(
            poll=poll,
            voter=admin,
            selected_option=option
        )
        
        # Check that results can be viewed even though poll hasn't ended
        assert poll.all_admins_voted is True
        assert poll.can_view_results is True
        assert poll.participation_rate == 100.0


# Performance and stress tests
class TestPollingPerformance:
    """Test polling system performance under load"""
    
    @pytest.mark.slow
    def test_large_poll_creation(self, db):
        """Test creating poll with many options"""
        admin = User.objects.create_user(
            username='perf_admin',
            email='perf@test.com',
            password='testpass123',
            is_superuser=True
        )
        
        future_date = timezone.now() + timedelta(days=7)
        poll = AdminPoll.objects.create(
            title="Large Poll Test",
            description="Testing performance with many options",
            poll_type="multiple_choice",
            created_by=admin,
            end_date=future_date
        )
        
        # Create 100 options
        options = []
        for i in range(100):
            options.append(PollOption(
                poll=poll,
                option_text=f"Option {i+1}",
                order=i+1
            ))
        
        PollOption.objects.bulk_create(options)
        
        assert poll.options.count() == 100
        
        # Test vote counting performance
        option = poll.options.first()
        vote = AdminVote.objects.create(
            poll=poll,
            voter=admin,
            selected_option=option
        )
        
        # This should complete quickly even with many options
        assert option.vote_count == 1
        assert poll.total_votes == 1
    
    @pytest.mark.slow
    def test_many_voters_performance(self, db):
        """Test performance with many voters"""
        # Create 50 superusers
        voters = []
        for i in range(50):
            voter = User.objects.create_user(
                username=f'voter_{i}',
                email=f'voter_{i}@test.com',
                password='testpass123',
                is_superuser=True
            )
            voters.append(voter)
        
        admin = voters[0]
        future_date = timezone.now() + timedelta(days=7)
        poll = AdminPoll.objects.create(
            title="Many Voters Test",
            description="Testing performance with many voters",
            poll_type="yes_no",
            created_by=admin,
            end_date=future_date
        )
        
        yes_option = PollOption.objects.create(
            poll=poll,
            option_text="Yes",
            order=1
        )
        
        no_option = PollOption.objects.create(
            poll=poll,
            option_text="No",
            order=2
        )
        
        # All voters vote
        votes = []
        for i, voter in enumerate(voters):
            option = yes_option if i % 2 == 0 else no_option
            votes.append(AdminVote(
                poll=poll,
                voter=voter,
                selected_option=option
            ))
        
        AdminVote.objects.bulk_create(votes)
        
        # Check results performance
        assert poll.total_votes == 50
        assert yes_option.vote_count == 25
        assert no_option.vote_count == 25
        assert poll.participation_rate == 100.0


# Pytest configuration and fixtures
@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Allow database access for all tests"""
    pass


@pytest.fixture
def django_settings(settings):
    """Configure Django settings for testing"""
    settings.DEBUG = True
    settings.SECRET_KEY = 'test-secret-key-for-polling-tests'
    return settings