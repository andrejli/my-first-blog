from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import datetime, timedelta
from blog.models import Event, Course, UserProfile
import tempfile
import os


class EventModelTest(TestCase):
    """Test cases for the Event model and its functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users with unique names
        self.admin_user = User.objects.create_user(
            username='admin_eventmodel',
            email='admin_eventmodel@test.com',
            password='testpass123'
        )
        self.student_user = User.objects.create_user(
            username='student_eventmodel', 
            email='student_eventmodel@test.com',
            password='testpass123'
        )
        
        # Update user profiles (auto-created by signals)
        admin_profile = UserProfile.objects.get(user=self.admin_user)
        admin_profile.role = 'admin'
        admin_profile.save()
        
        student_profile = UserProfile.objects.get(user=self.student_user)
        student_profile.role = 'student'
        student_profile.save()
        
        # Create a test course
        self.course = Course.objects.create(
            title='Advanced Python Programming',
            description='Master advanced Python concepts including decorators, metaclasses, and async programming',
            course_code='CS350',
            instructor=self.admin_user,
            max_students=25,
            duration_weeks=3
        )
        
        # Create test events with rich content
        self.public_event = Event.objects.create(
            title='Python Workshop: Building REST APIs with Django',
            description='''Join us for an intensive workshop on building scalable REST APIs using Django and Django REST Framework. 
            
            What you'll learn:
            • Setting up Django REST Framework
            • Creating serializers and viewsets
            • Implementing authentication and permissions
            • API documentation with Swagger
            • Best practices for API design
            
            Prerequisites: Basic Python and Django knowledge
            Duration: 4 hours with breaks
            Materials: Laptop required, development environment setup guide will be sent
            
            This hands-on workshop includes practical exercises and real-world examples.''',
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=7, hours=4),
            event_type='workshop',
            priority='high',
            visibility='public',
            created_by=self.admin_user,
            course=self.course,
            is_published=True,
            is_featured=True
        )
        
        self.registered_event = Event.objects.create(
            title='Final Exam: Advanced Python Concepts',
            description='''Comprehensive final examination covering all topics from the Advanced Python Programming course.
            
            Exam Coverage:
            • Object-oriented programming principles
            • Advanced data structures and algorithms
            • Decorators and context managers
            • Metaclasses and descriptors
            • Async/await programming
            • Testing and debugging techniques
            • Performance optimization
            
            Exam Format:
            • Duration: 3 hours
            • Mixed format: Multiple choice, coding problems, and essay questions
            • Open book (course materials and notes allowed)
            • No internet access during exam
            
            Important Notes:
            • Arrive 15 minutes early for check-in
            • Bring valid student ID
            • Laptops will be provided for coding sections
            • Make-up exams available only with valid documentation''',
            start_date=timezone.now() + timedelta(days=30),
            event_type='exam',
            priority='urgent',
            visibility='registered',
            created_by=self.admin_user,
            course=self.course,
            all_day=False,
            is_published=True
        )
        
        self.holiday_event = Event.objects.create(
            title='Spring Break - Campus Closed',
            description='''University spring break period. All academic buildings will be closed.
            
            Closure Details:
            • No classes or exams scheduled
            • Library closed (online resources available)
            • Administrative offices closed
            • Campus dining services limited
            • Residence halls remain open
            • Emergency services available 24/7
            
            Important Dates:
            • Last day of classes: Day before break
            • Campus reopens: Monday after break
            • Make-up classes: See individual course schedules
            
            Students traveling: Please update emergency contact information
            International students: Check visa requirements for travel''',
            start_date=timezone.now() + timedelta(days=45),
            end_date=timezone.now() + timedelta(days=52),
            event_type='holiday',
            priority='normal',
            visibility='public',
            created_by=self.admin_user,
            all_day=True,
            is_published=True
        )
        
        self.assignment_deadline = Event.objects.create(
            title='Project Submission: Web Scraping Assignment',
            description='''Final deadline for the web scraping project assignment.
            
            Assignment Requirements:
            • Build a web scraper using Python (BeautifulSoup, Scrapy, or requests)
            • Target website: Choose from approved list
            • Data storage: CSV or database format
            • Error handling and rate limiting required
            • Documentation and code comments mandatory
            
            Submission Guidelines:
            • Submit via course portal before 11:59 PM
            • Include: Source code, documentation, and sample output
            • File naming: lastname_firstname_webscraper.zip
            • Late submissions: -10% per day
            
            Grading Criteria:
            • Code quality and structure (30%)
            • Functionality and accuracy (40%)
            • Documentation and comments (20%)
            • Error handling and edge cases (10%)
            
            Need help? Office hours available Monday-Wednesday 2-4 PM''',
            start_date=timezone.now() + timedelta(days=14),
            event_type='deadline',
            priority='urgent',
            visibility='registered',
            created_by=self.admin_user,
            course=self.course,
            is_published=True
        )
        
        # Create an event with file attachments
        self.workshop_with_files = Event.objects.create(
            title='Machine Learning Workshop: Introduction to Neural Networks',
            description='''Comprehensive introduction to neural networks and deep learning using Python and TensorFlow.
            
            Workshop Agenda:
            Day 1: Fundamentals
            • Introduction to machine learning concepts
            • Linear regression and classification
            • Understanding neural network architecture
            • Hands-on: Building your first neural network
            
            Day 2: Deep Learning
            • Convolutional Neural Networks (CNNs)
            • Recurrent Neural Networks (RNNs)
            • Model training and optimization
            • Hands-on: Image classification project
            
            Day 3: Advanced Topics
            • Transfer learning and pre-trained models
            • Model deployment and production considerations
            • Ethics in AI and bias detection
            • Final project presentations
            
            Prerequisites:
            • Python programming experience
            • Basic statistics and linear algebra
            • Laptop with 8GB+ RAM recommended
            
            Provided Materials:
            • Complete dataset for hands-on exercises
            • Pre-configured Jupyter notebooks
            • Reference guides and cheat sheets
            • Certificate of completion
            
            Industry Speakers:
            • Dr. Sarah Chen - Google AI Research
            • Mark Rodriguez - Tesla Autopilot Team
            • Prof. Emily Watson - MIT Computer Science''',
            start_date=timezone.now() + timedelta(days=21),
            end_date=timezone.now() + timedelta(days=23),
            event_type='workshop',
            priority='high',
            visibility='public',
            created_by=self.admin_user,
            is_published=True,
            is_featured=True
        )
        
        self.client = Client()
    
    def test_event_creation(self):
        """Test event model creation and validation"""
        self.assertEqual(self.public_event.title, 'Python Workshop: Building REST APIs with Django')
        self.assertEqual(self.public_event.event_type, 'workshop')
        self.assertEqual(self.public_event.visibility, 'public')
        self.assertTrue(self.public_event.is_published)
        self.assertTrue(self.public_event.is_featured)
    
    def test_event_properties(self):
        """Test event model properties and methods"""
        # Test upcoming event
        self.assertTrue(self.public_event.is_upcoming)
        
        # Test string representation
        expected_str = f"{self.public_event.title} - {self.public_event.start_date.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(self.public_event), expected_str)
        
        # Test duration calculation
        duration = self.public_event.get_duration()
        self.assertEqual(duration, "4h")
    
    def test_event_file_properties(self):
        """Test event file attachment properties"""
        # Test without files
        self.assertFalse(self.public_event.has_poster)
        self.assertFalse(self.public_event.has_materials)
        self.assertIsNone(self.public_event.get_poster_url)
        self.assertIsNone(self.public_event.get_materials_url)
    
    def test_event_visibility_filtering(self):
        """Test event visibility and filtering"""
        # Public events should be visible to all
        public_events = Event.objects.filter(visibility='public', is_published=True)
        self.assertIn(self.public_event, public_events)
        self.assertIn(self.holiday_event, public_events)
        
        # Registered events should be separate
        registered_events = Event.objects.filter(visibility='registered', is_published=True)
        self.assertIn(self.registered_event, registered_events)
        self.assertIn(self.assignment_deadline, registered_events)


class CalendarViewTest(TestCase):
    """Test cases for calendar views and functionality"""
    
    def setUp(self):
        """Set up test data for calendar views"""
        self.admin_user = User.objects.create_user(
            username='calendar_admin',
            email='admin@calendar.com',
            password='testpass123'
        )
        self.student_user = User.objects.create_user(
            username='calendar_student',
            email='student@calendar.com', 
            password='testpass123'
        )
        
        # Update user profiles (auto-created by signals)
        admin_profile = UserProfile.objects.get(user=self.admin_user)
        admin_profile.role = 'admin'
        admin_profile.save()
        
        student_profile = UserProfile.objects.get(user=self.student_user)
        student_profile.role = 'student'
        student_profile.save()
        
        # Create events for calendar testing
        self.current_month_event = Event.objects.create(
            title='Tech Talk: Future of Web Development',
            description='''Explore the cutting-edge trends shaping the future of web development.
            
            Topics Covered:
            • WebAssembly and performance optimization
            • Progressive Web Apps (PWAs)
            • JAMstack architecture and static site generators
            • Serverless computing and edge functions
            • AI integration in web applications
            • Accessibility and inclusive design
            
            Speaker: Alex Thompson
            • Senior Engineer at Vercel
            • Creator of popular open-source tools
            • 10+ years in web development
            • Regular contributor to web standards
            
            Event Format:
            • 45-minute presentation
            • 15-minute Q&A session
            • Networking reception (light refreshments)
            • Recording available for registered attendees
            
            Target Audience:
            • Web developers (all levels)
            • Computer science students
            • Tech entrepreneurs
            • Anyone interested in web technology trends''',
            start_date=timezone.now().replace(day=15, hour=14, minute=0),
            event_type='meeting',
            visibility='public',
            created_by=self.admin_user,
            is_published=True
        )
        
        self.client = Client()
    
    def test_calendar_view_anonymous(self):
        """Test calendar view for anonymous users - should redirect to login"""
        response = self.client.get(reverse('event_calendar'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue(response['Location'].endswith('login/?next=/calendar/'))  # Should redirect to login page
    
    def test_calendar_view_authenticated(self):
        """Test calendar view for authenticated users"""
        self.client.login(username='calendar_student', password='testpass123')
        response = self.client.get(reverse('event_calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Event Calendar')
    
    def test_calendar_navigation(self):
        """Test calendar month navigation"""
        # Login first since calendar requires authentication
        self.client.login(username='calendar_student', password='testpass123')
        
        # Test next month
        next_month = timezone.now().replace(day=1) + timedelta(days=32)
        response = self.client.get(reverse('event_calendar'), {
            'month': next_month.month,
            'year': next_month.year
        })
        self.assertEqual(response.status_code, 200)
    
    def test_event_management_view_admin(self):
        """Test event management view for admin users"""
        # Make sure our admin user profile is saved
        admin_profile = UserProfile.objects.get(user=self.admin_user)
        admin_profile.role = 'admin'
        admin_profile.save()
        
        login_success = self.client.login(username='calendar_admin', password='testpass123')
        self.assertTrue(login_success, "Login should succeed")
        
        response = self.client.get(reverse('event_management'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Event Management')
        self.assertContains(response, 'Tech Talk: Future of Web Development')


class EventIntegrationTest(TestCase):
    """Integration tests for event system with other components"""
    
    def setUp(self):
        """Set up comprehensive test environment"""
        # Create instructor
        self.instructor = User.objects.create_user(
            username='prof_smith',
            email='smith@university.edu',
            password='instructor123',
            first_name='John',
            last_name='Smith'
        )
        
        # Create students
        self.student1 = User.objects.create_user(
            username='alice_student',
            email='alice@student.edu', 
            password='student123',
            first_name='Alice',
            last_name='Johnson'
        )
        
        self.student2 = User.objects.create_user(
            username='bob_student',
            email='bob@student.edu',
            password='student123', 
            first_name='Bob',
            last_name='Wilson'
        )
        
        # Update profiles (auto-created by signals)
        instructor_profile = UserProfile.objects.get(user=self.instructor)
        instructor_profile.role = 'instructor'
        instructor_profile.save()
        
        student1_profile = UserProfile.objects.get(user=self.student1)
        student1_profile.role = 'student'
        student1_profile.save()
        
        student2_profile = UserProfile.objects.get(user=self.student2)
        student2_profile.role = 'student'
        student2_profile.save()
        
        # Create course with rich content
        self.course = Course.objects.create(
            title='Full-Stack Web Development',
            description='''Comprehensive course covering modern full-stack web development from frontend to backend.
            
            Course Objectives:
            By the end of this course, students will be able to:
            • Build responsive web applications using HTML5, CSS3, and JavaScript
            • Develop interactive user interfaces with React.js
            • Create RESTful APIs using Node.js and Express
            • Implement database design and management with MongoDB
            • Deploy applications to cloud platforms
            • Apply security best practices in web development
            • Use version control and collaborative development workflows
            
            Course Structure:
            • 16 weeks of instruction
            • 3 lectures per week (50 minutes each)
            • 1 lab session per week (2 hours)
            • 4 major projects + final capstone
            • Midterm and final examinations
            
            Grading:
            • Projects: 40%
            • Exams: 30% 
            • Lab participation: 20%
            • Attendance and participation: 10%
            
            Required Materials:
            • Laptop capable of running development tools
            • "Modern Web Development" textbook (latest edition)
            • Access to cloud services (AWS/Heroku credits provided)
            
            Prerequisites:
            • CS 101: Introduction to Programming
            • CS 201: Data Structures and Algorithms
            • Basic understanding of HTML and CSS''',
            course_code='CS425',
            instructor=self.instructor,
            max_students=30,
            duration_weeks=16,
            status='published'
        )
        
        # Create comprehensive event schedule
        self.create_course_events()
        
        self.client = Client()
    
    def create_course_events(self):
        """Create a realistic schedule of course events"""
        base_date = timezone.now()
        
        # Course introduction
        Event.objects.create(
            title='Course Introduction & Development Environment Setup',
            description='''Welcome to Full-Stack Web Development! First class overview and lab setup.
            
            Agenda:
            • Course introduction and expectations
            • Review of syllabus and grading policy
            • Development environment setup
            • Git and GitHub workflow introduction
            • HTML5 and CSS3 refresher
            • First coding exercise: Personal portfolio page
            
            What to Bring:
            • Laptop with admin privileges
            • GitHub account (create if needed)
            • Notebook for taking notes
            
            Lab Setup Includes:
            • VS Code installation and configuration
            • Node.js and npm setup
            • Git configuration
            • Browser developer tools overview
            • Extension recommendations
            
            Homework Assignment:
            Complete the personal portfolio page started in class and push to GitHub''',
            start_date=base_date + timedelta(days=1),
            end_date=base_date + timedelta(days=1, hours=3),
            event_type='general',
            course=self.course,
            created_by=self.instructor,
            visibility='registered',
            is_published=True
        )
        
        # Project deadlines
        Event.objects.create(
            title='Project 1 Due: Responsive Portfolio Website',
            description='''First major project submission deadline for responsive portfolio website.
            
            Project Requirements:
            • Fully responsive design (mobile-first approach)
            • Modern CSS techniques (Grid, Flexbox)
            • Interactive elements with vanilla JavaScript
            • Cross-browser compatibility (Chrome, Firefox, Safari, Edge)
            • Accessibility compliance (WCAG 2.1 AA)
            • Performance optimization (images, CSS, JS)
            
            Technical Specifications:
            • Valid HTML5 semantic markup
            • CSS3 with preprocessor (Sass recommended)
            • ES6+ JavaScript features
            • Progressive enhancement principles
            • SEO optimization basics
            
            Deliverables:
            1. Source code repository on GitHub
            2. Live deployment URL (GitHub Pages, Netlify, or Vercel)
            3. Project documentation (README.md)
            4. Self-assessment reflection (500 words)
            
            Grading Rubric:
            • Design and usability: 25%
            • Technical implementation: 35%
            • Code quality and organization: 20%
            • Documentation and deployment: 15%
            • Creativity and innovation: 5%
            
            Late Policy: -10% per day, maximum 3 days late accepted''',
            start_date=base_date + timedelta(days=21),
            event_type='deadline',
            course=self.course,
            created_by=self.instructor,
            priority='urgent',
            visibility='registered',
            is_published=True
        )
        
        # Midterm exam
        Event.objects.create(
            title='Midterm Examination: Frontend Development',
            description='''Comprehensive midterm exam covering all frontend development topics.
            
            Exam Coverage:
            Unit 1: HTML5 and Semantic Markup
            • Document structure and semantic elements
            • Forms and input validation
            • Accessibility considerations
            • SEO optimization techniques
            
            Unit 2: Advanced CSS
            • CSS Grid and Flexbox layouts
            • Responsive design principles
            • CSS animations and transitions
            • Preprocessors (Sass/SCSS)
            
            Unit 3: JavaScript Fundamentals
            • ES6+ syntax and features
            • DOM manipulation and events
            • Asynchronous programming (Promises, async/await)
            • Modern JavaScript patterns
            
            Unit 4: Development Tools
            • Version control with Git
            • Browser developer tools
            • Build tools and bundlers
            • Debugging techniques
            
            Exam Format:
            • Duration: 2 hours
            • Section A: Multiple choice (30 questions, 30 points)
            • Section B: Short answer (5 questions, 35 points)
            • Section C: Coding problems (3 problems, 35 points)
            
            Allowed Materials:
            • One 8.5x11" handwritten cheat sheet (both sides)
            • Basic calculator (no programming calculators)
            • No electronic devices or internet access
            
            Preparation Tips:
            • Review all lecture slides and notes
            • Complete practice problems from textbook
            • Attend review session (scheduled for day before exam)
            • Join study groups for collaborative learning''',
            start_date=base_date + timedelta(days=56),
            end_date=base_date + timedelta(days=56, hours=2),
            event_type='exam',
            course=self.course,
            created_by=self.instructor,
            priority='urgent',
            visibility='registered',
            is_published=True
        )
        
        # Guest lecture
        Event.objects.create(
            title='Guest Lecture: Industry Best Practices in Web Development',
            description='''Special guest lecture by industry professionals on real-world web development.
            
            Guest Speakers:
            Sarah Chen - Senior Frontend Engineer at Airbnb
            • 8 years experience in frontend development
            • Expert in React.js and modern JavaScript
            • Contributor to open-source projects
            • Focus: "Scaling Frontend Architecture"
            
            Michael Rodriguez - Full-Stack Developer at Stripe
            • 6 years in fintech and payment systems
            • Specialist in secure web applications
            • Author of popular development blog
            • Focus: "Security in Modern Web Apps"
            
            Topics to be Covered:
            • Industry trends and emerging technologies
            • Code review and collaboration practices
            • Performance optimization in production
            • Security considerations and best practices
            • Career advice and professional development
            • Common mistakes and how to avoid them
            
            Interactive Elements:
            • Live coding demonstrations
            • Q&A session with both speakers
            • Code review of student projects
            • Networking opportunity (15 minutes after lecture)
            
            Preparation:
            • Prepare thoughtful questions about web development careers
            • Bring examples of your work for potential feedback
            • Review company websites and recent tech blog posts
            
            This lecture counts toward your participation grade and provides valuable industry insights!''',
            start_date=base_date + timedelta(days=42),
            end_date=base_date + timedelta(days=42, hours=1.5),
            event_type='meeting',
            course=self.course,
            created_by=self.instructor,
            priority='high',
            visibility='public',
            is_published=True,
            is_featured=True
        )
    
    def test_course_event_integration(self):
        """Test integration between courses and events"""
        course_events = Event.objects.filter(course=self.course)
        self.assertEqual(course_events.count(), 4)
        
        # Test event visibility for course participants
        for event in course_events:
            self.assertEqual(event.course, self.course)
            self.assertEqual(event.created_by, self.instructor)
    
    def test_event_calendar_with_course_context(self):
        """Test calendar view with course-specific events"""
        self.client.login(username='alice_student', password='student123')
        response = self.client.get(reverse('event_calendar'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Full-Stack Web Development')
        self.assertContains(response, 'Course Introduction')


class EventAccessibilityTest(TestCase):
    """Test accessibility and usability features of the event system"""
    
    def setUp(self):
        """Set up accessibility test data"""
        self.user = User.objects.create_user(
            username='accessibility_user',
            password='testpass123'
        )
        
        # Create events with accessibility considerations
        self.accessible_event = Event.objects.create(
            title='Accessibility Workshop: Building Inclusive Web Applications',
            description='''Learn how to create web applications that work for everyone, including users with disabilities.
            
            Workshop Overview:
            This comprehensive workshop covers the essential principles and practices of web accessibility,
            ensuring your applications are usable by people with diverse abilities and needs.
            
            Learning Objectives:
            • Understand WCAG 2.1 guidelines and compliance levels
            • Implement semantic HTML for screen reader compatibility  
            • Design accessible color schemes and typography
            • Create keyboard-navigable interfaces
            • Test applications with assistive technologies
            • Write meaningful alt text and descriptions
            
            Hands-On Activities:
            • Screen reader testing with NVDA and JAWS
            • Keyboard navigation assessment
            • Color contrast evaluation tools
            • Automated accessibility testing with axe-core
            • User testing with accessibility consultants
            
            Workshop Accessibility Features:
            • Live captions provided during presentation
            • Materials available in multiple formats (PDF, HTML, audio)
            • Sign language interpreter available upon request
            • Wheelchair accessible venue with reserved seating
            • Large print materials and high contrast slides
            • Audio descriptions for visual content
            
            Target Audience:
            • Web developers and designers
            • UX/UI professionals
            • Product managers
            • Quality assurance testers
            • Anyone interested in inclusive design
            
            Prerequisite Knowledge:
            • Basic HTML and CSS understanding
            • Familiarity with web development tools
            • No prior accessibility experience required
            
            Certificate:
            Participants will receive a certificate of completion for professional development records.''',
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now() + timedelta(days=10, hours=6),
            event_type='workshop',
            created_by=self.user,
            visibility='public',
            priority='high',
            is_published=True,
            is_featured=True
        )
    
    def test_event_content_accessibility(self):
        """Test that event content follows accessibility guidelines"""
        # Test that event descriptions are comprehensive
        self.assertGreater(len(self.accessible_event.description), 500)
        
        # Test that titles are descriptive
        self.assertIn('Accessibility Workshop', self.accessible_event.title)
        
        # Test event model string representation
        str_repr = str(self.accessible_event)
        self.assertIn(self.accessible_event.title, str_repr)


# Sample test data creation utility
def create_sample_events():
    """Utility function to create rich sample events for development/testing"""
    
    # Create sample users if they don't exist
    try:
        admin = User.objects.get(username='admin')
    except User.DoesNotExist:
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        UserProfile.objects.create(user=admin, role='admin')
    
    # Sample events with rich, realistic content
    sample_events = [
        {
            'title': 'Data Science Bootcamp: From Analytics to AI',
            'description': '''Intensive 3-day bootcamp covering the complete data science pipeline from data collection to AI implementation.
            
            Day 1: Data Fundamentals
            • Data collection and cleaning techniques
            • Exploratory data analysis with pandas and matplotlib
            • Statistical analysis and hypothesis testing
            • Data visualization best practices
            
            Day 2: Machine Learning
            • Supervised learning algorithms (regression, classification)
            • Unsupervised learning (clustering, dimensionality reduction)
            • Model evaluation and cross-validation
            • Feature engineering and selection
            
            Day 3: Advanced Topics
            • Deep learning with TensorFlow and Keras
            • Natural language processing
            • Computer vision applications
            • Model deployment and MLOps
            
            Prerequisites: Python programming, basic statistics
            Materials: Jupyter notebooks, datasets, cloud computing credits provided
            Certificate: Industry-recognized completion certificate
            Career Support: Job placement assistance and portfolio review''',
            'start_date': timezone.now() + timedelta(days=30),
            'end_date': timezone.now() + timedelta(days=32),
            'event_type': 'workshop',
            'priority': 'high',
            'visibility': 'public'
        },
        {
            'title': 'Cybersecurity Awareness Week: Protecting Digital Assets',
            'description': '''Week-long series of events focused on cybersecurity education and awareness.
            
            Monday: Password Security and Multi-Factor Authentication
            • Creating strong, unique passwords
            • Password manager tools and best practices
            • Implementing MFA across personal and professional accounts
            • Recognition of phishing attempts
            
            Tuesday: Network Security and Safe Browsing
            • Understanding VPNs and encrypted connections
            • Safe public Wi-Fi usage
            • Browser security settings and extensions
            • Recognizing malicious websites and downloads
            
            Wednesday: Social Engineering and Privacy Protection
            • Common social engineering tactics
            • Privacy settings on social media platforms
            • Personal information protection strategies
            • Identity theft prevention
            
            Thursday: Mobile Device Security
            • Smartphone and tablet security settings
            • App permissions and privacy considerations
            • Mobile banking and payment security
            • Device encryption and remote wipe capabilities
            
            Friday: Incident Response and Recovery
            • What to do if you're compromised
            • Data backup strategies
            • Reporting security incidents
            • Recovery planning and business continuity
            
            Special Events:
            • Live hacking demonstration (ethical)
            • Panel discussion with cybersecurity professionals
            • Hands-on workshops for security tools
            • Free security assessment for participants
            
            All events include Q&A sessions and take-home resources.''',
            'start_date': timezone.now() + timedelta(days=60),
            'end_date': timezone.now() + timedelta(days=64),
            'event_type': 'workshop',
            'priority': 'high',
            'visibility': 'public'
        }
    ]
    
    created_events = []
    for event_data in sample_events:
        event = Event.objects.create(
            **event_data,
            created_by=admin,
            is_published=True,
            is_featured=True
        )
        created_events.append(event)
    
    return created_events
