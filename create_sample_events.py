#!/usr/bin/env python
"""
Sample Event Data Creator
Creates realistic test events for development and demonstration purposes
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from blog.models import Event, Course, UserProfile


def create_comprehensive_sample_data():
    """Create comprehensive sample events for testing and demonstration"""
    
    print("Creating sample users and courses...")
    
    # Create sample users
    admin_user, created = User.objects.get_or_create(
        username='demo_admin',
        defaults={
            'email': 'admin@demo.com',
            'first_name': 'Demo',
            'last_name': 'Administrator',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('demo123')
        admin_user.save()
        UserProfile.objects.get_or_create(user=admin_user, defaults={'role': 'admin'})
    else:
        # Update existing user to be admin
        profile, created = UserProfile.objects.get_or_create(user=admin_user, defaults={'role': 'admin'})
    
    instructor_user, created = User.objects.get_or_create(
        username='prof_demo',
        defaults={
            'email': 'professor@demo.com',
            'first_name': 'Professor',
            'last_name': 'Demo'
        }
    )
    if created:
        instructor_user.set_password('demo123')
        instructor_user.save()
        UserProfile.objects.get_or_create(user=instructor_user, defaults={'role': 'instructor'})
    else:
        # Update existing user to be instructor
        profile, created = UserProfile.objects.get_or_create(user=instructor_user, defaults={'role': 'instructor'})
    
    # Create sample courses
    cs_course, created = Course.objects.get_or_create(
        course_code='CS101',
        defaults={
            'title': 'Introduction to Computer Science',
            'description': 'Fundamental concepts of computer science and programming',
            'instructor': instructor_user,
            'max_students': 50,
            'duration_weeks': 12,
            'status': 'published'
        }
    )
    
    web_course, created = Course.objects.get_or_create(
        course_code='WEB301',
        defaults={
            'title': 'Advanced Web Development',
            'description': 'Advanced concepts in modern web development',
            'instructor': instructor_user,
            'max_students': 30,
            'duration_weeks': 16,
            'status': 'published'
        }
    )
    
    print("Creating sample events...")
    
    # Sample events with rich content
    sample_events = [
        {
            'title': 'AI Ethics Symposium: Responsible Technology Development',
            'description': '''Join leading experts in artificial intelligence and ethics for a thought-provoking symposium on responsible AI development.
            
            Keynote Speakers:
            • Dr. Timnit Gebru - AI Ethics Researcher and Advocate
            • Prof. Stuart Russell - UC Berkeley Computer Science
            • Dr. Cathy O'Neil - Author of "Weapons of Math Destruction"
            • Prof. Safiya Noble - UCLA Information Studies
            
            Panel Discussions:
            Session 1: "Bias in AI Systems"
            • Algorithmic bias detection and mitigation
            • Fairness metrics and evaluation methods
            • Case studies from industry applications
            • Community-centered approaches to AI development
            
            Session 2: "AI Governance and Policy"
            • Current regulatory landscape for AI
            • International cooperation on AI standards
            • Role of governments vs. industry self-regulation
            • Future policy recommendations
            
            Session 3: "AI in Society"
            • Impact on employment and labor markets
            • AI in criminal justice and surveillance
            • Healthcare AI and patient privacy
            • Educational applications and digital divide
            
            Interactive Elements:
            • Live polling and Q&A sessions
            • Breakout discussions with experts
            • Demo stations with ethical AI tools
            • Networking reception with light refreshments
            
            Target Audience:
            • AI researchers and practitioners
            • Policy makers and government officials
            • Technology industry professionals
            • Students and academics
            • Civil society organizations
            • Anyone interested in AI's societal impact
            
            Registration includes:
            • Access to all sessions and materials
            • Digital proceedings and presentation slides
            • Certificate of attendance
            • Networking directory of participants
            
            This event qualifies for continuing education credits in multiple professional organizations.''',
            'start_date': timezone.now() + timedelta(days=45),
            'end_date': timezone.now() + timedelta(days=45, hours=8),
            'event_type': 'meeting',
            'priority': 'high',
            'visibility': 'public',
            'created_by': admin_user,
            'is_published': True,
            'is_featured': True
        },
        
        {
            'title': 'Quantum Computing Workshop: From Theory to Practice',
            'description': '''Comprehensive introduction to quantum computing covering theoretical foundations and practical implementations.
            
            Workshop Overview:
            Explore the fascinating world of quantum computing through hands-on exercises and real-world applications.
            This intensive workshop bridges the gap between quantum theory and practical quantum programming.
            
            Learning Objectives:
            • Understand quantum mechanical principles relevant to computing
            • Master quantum circuit design and quantum gates
            • Program quantum algorithms using Qiskit and IBM Quantum
            • Explore quantum advantage in various problem domains
            • Analyze current limitations and future prospects
            
            Day 1: Quantum Foundations
            Morning Session:
            • Quantum mechanics refresher (superposition, entanglement)
            • Classical vs. quantum computation models
            • Quantum gates and circuit notation
            • Measurement and quantum state collapse
            
            Afternoon Session:
            • Hands-on: Building first quantum circuits
            • Quantum teleportation protocol
            • Quantum key distribution (BB84)
            • Lab: Implementing simple quantum algorithms
            
            Day 2: Quantum Algorithms
            Morning Session:
            • Deutsch-Jozsa algorithm
            • Grover's search algorithm
            • Quantum Fourier Transform
            • Shor's factoring algorithm (theory)
            
            Afternoon Session:
            • Variational Quantum Eigensolver (VQE)
            • Quantum Approximate Optimization Algorithm (QAOA)
            • Quantum machine learning basics
            • Current research frontiers
            
            Day 3: Practical Applications
            Morning Session:
            • Quantum chemistry simulations
            • Optimization problems in logistics
            • Financial modeling applications
            • Cryptography and security implications
            
            Afternoon Session:
            • Final project: Choose and implement quantum algorithm
            • Presentation of results
            • Discussion of quantum hardware platforms
            • Career paths in quantum computing
            
            Prerequisites:
            • Linear algebra (vectors, matrices, eigenvalues)
            • Basic programming experience (Python preferred)
            • Undergraduate physics helpful but not required
            
            Materials Provided:
            • Access to IBM Quantum Experience
            • Comprehensive workbook with exercises
            • Python/Qiskit development environment
            • Quantum computing reference materials
            • Certificate of completion
            
            Industry Partnerships:
            This workshop is developed in collaboration with:
            • IBM Quantum Network
            • Google Quantum AI
            • Microsoft Azure Quantum
            • Rigetti Computing
            
            Career Impact:
            • Growing field with high demand for skilled professionals
            • Average quantum computing engineer salary: $150,000+
            • Opportunities in tech giants, startups, and research institutions
            • Foundation for advanced quantum computing specialization''',
            'start_date': timezone.now() + timedelta(days=21),
            'end_date': timezone.now() + timedelta(days=23),
            'event_type': 'workshop',
            'priority': 'high',
            'visibility': 'public',
            'created_by': admin_user,
            'is_published': True,
            'is_featured': True
        },
        
        {
            'title': 'Final Project Presentations: CS101 Introduction to Computer Science',
            'description': '''Student final project presentations for CS101 - Introduction to Computer Science course.
            
            Presentation Schedule:
            Each student team will present their final project demonstrating the concepts learned throughout the semester.
            
            Presentation Format:
            • 10 minutes presentation + 5 minutes Q&A per team
            • Live demonstration of working software
            • Technical explanation of implementation
            • Discussion of challenges and solutions
            • Reflection on learning outcomes
            
            Project Categories:
            Category A: Console Applications
            • Text-based games (adventure games, puzzles)
            • Utility programs (calculators, converters)
            • Data processing applications
            • Algorithm visualizations
            
            Category B: Web Applications
            • Interactive websites using HTML/CSS/JavaScript
            • Simple web games and simulations
            • Information systems and databases
            • Educational tools and tutorials
            
            Category C: Mobile Applications
            • Native or web-based mobile apps
            • Educational or productivity applications
            • Games suitable for mobile platforms
            • Accessibility-focused applications
            
            Evaluation Criteria:
            Technical Implementation (40%):
            • Code quality and organization
            • Proper use of programming concepts
            • Error handling and edge cases
            • Documentation and comments
            
            Innovation and Creativity (25%):
            • Originality of concept
            • Creative problem-solving approaches
            • User interface design
            • Feature completeness
            
            Presentation Quality (25%):
            • Clear explanation of technical concepts
            • Effective demonstration of functionality
            • Response to questions
            • Professional presentation style
            
            Teamwork and Collaboration (10%):
            • Evidence of equal contribution
            • Effective use of version control
            • Team coordination and communication
            • Peer evaluation feedback
            
            Attendance:
            • Mandatory for all enrolled students
            • Family and friends welcome to attend
            • Industry professionals invited as guest evaluators
            • Photography and recording with permission
            
            Awards and Recognition:
            • Best Technical Implementation
            • Most Creative Solution
            • Best Presentation
            • People's Choice Award (audience voting)
            
            Post-Presentation:
            • Networking session with industry guests
            • Course feedback and reflection
            • Information about advanced courses
            • Career guidance and internship opportunities
            
            This event showcases the culmination of a semester's worth of learning and represents
            students' first major milestone in their computer science journey.''',
            'start_date': timezone.now() + timedelta(days=90),
            'end_date': timezone.now() + timedelta(days=90, hours=4),
            'event_type': 'general',
            'priority': 'normal',
            'visibility': 'registered',
            'created_by': instructor_user,
            'course': cs_course,
            'is_published': True
        },
        
        {
            'title': 'Web Development Assignment Deadline: E-commerce Site Project',
            'description': '''Final deadline for the e-commerce website project - Advanced Web Development course.
            
            Project Overview:
            Build a fully functional e-commerce website using modern web development technologies and best practices.
            
            Technical Requirements:
            Frontend Development:
            • Responsive design using CSS Grid and Flexbox
            • Interactive user interface with React.js or Vue.js
            • Modern JavaScript (ES6+) features
            • State management (Redux, Vuex, or Context API)
            • Form validation and user input handling
            • Accessibility compliance (WCAG 2.1)
            
            Backend Development:
            • RESTful API using Node.js/Express or Python/Django
            • Database design and implementation (PostgreSQL or MongoDB)
            • User authentication and authorization
            • Payment processing integration (Stripe test mode)
            • File upload and image management
            • Email notifications for orders
            
            Key Features Required:
            User Management:
            • User registration and login
            • Profile management and password reset
            • Order history and tracking
            • Wishlist functionality
            
            Product Catalog:
            • Product browsing with categories
            • Search and filtering capabilities
            • Product details with image galleries
            • Inventory management
            • Product reviews and ratings
            
            Shopping Cart:
            • Add/remove items from cart
            • Quantity adjustments
            • Persistent cart across sessions
            • Guest checkout option
            
            Checkout Process:
            • Secure payment processing
            • Shipping address management
            • Order confirmation and receipts
            • Email notifications
            
            Admin Panel:
            • Product management (CRUD operations)
            • Order management and status updates
            • User management capabilities
            • Sales analytics and reporting
            
            Deployment Requirements:
            • Frontend deployed to Netlify, Vercel, or similar
            • Backend deployed to Heroku, DigitalOcean, or AWS
            • Database hosted on cloud service
            • SSL certificate and HTTPS enabled
            • Environment variables for sensitive data
            
            Documentation Requirements:
            README.md file must include:
            • Project description and features
            • Technology stack and dependencies
            • Installation and setup instructions
            • API documentation
            • Testing instructions
            • Deployment guide
            • Screenshots and demo links
            
            Code Quality Standards:
            • Clean, readable, and well-commented code
            • Consistent coding style and formatting
            • Modular architecture and separation of concerns
            • Error handling and input validation
            • Unit tests for critical functionality
            • Performance optimization
            
            Submission Guidelines:
            1. Source code repository on GitHub (public or add instructor)
            2. Live deployment URLs (frontend and backend)
            3. Database schema and seed data
            4. Project documentation and README
            5. Video demo (5-10 minutes) showcasing key features
            6. Self-reflection report (1000 words)
            
            Grading Breakdown (Total: 100 points):
            • Frontend implementation and UI/UX: 25 points
            • Backend API and database design: 25 points
            • Feature completeness and functionality: 20 points
            • Code quality and documentation: 15 points
            • Deployment and performance: 10 points
            • Innovation and extra features: 5 points
            
            Late Submission Policy:
            • Up to 24 hours late: -10 points
            • 24-48 hours late: -20 points
            • 48-72 hours late: -30 points
            • More than 72 hours late: 0 points
            
            Academic Integrity:
            • All code must be original work
            • Third-party libraries and APIs allowed with attribution
            • Collaboration permitted for debugging help only
            • Plagiarism will result in course failure
            
            Resources and Support:
            • Office hours: Monday/Wednesday 2-4 PM
            • Online discussion forum for questions
            • Technical documentation and tutorials
            • Previous semester project examples
            • Industry mentor consultation sessions
            
            This project represents the culmination of advanced web development skills and serves
            as a portfolio piece for future career opportunities.''',
            'start_date': timezone.now() + timedelta(days=14),
            'event_type': 'deadline',
            'priority': 'urgent',
            'visibility': 'registered',
            'created_by': instructor_user,
            'course': web_course,
            'is_published': True
        },
        
        {
            'title': 'Holiday Break: Campus Closed for Winter Recess',
            'description': '''University winter break period with campus closure and limited services.
            
            Closure Period:
            The university will be closed for winter break, allowing students, faculty, and staff
            time to rest and celebrate with family and friends.
            
            Important Dates:
            • Last day of fall semester classes: December 15
            • Final exams period: December 16-20
            • Campus closure begins: December 21 at 5:00 PM
            • Campus reopens: January 8 at 8:00 AM
            • Spring semester classes begin: January 15
            
            Services During Break:
            Closed Services:
            • All academic buildings and classrooms
            • Administrative offices (Registrar, Financial Aid, etc.)
            • Library (physical access - online resources available)
            • Student services and support offices
            • Campus dining facilities
            • Recreational facilities and gymnasium
            • Parking enforcement (free parking during closure)
            
            Limited Services Available:
            • Campus security (24/7 emergency response)
            • Residence hall front desks (reduced hours)
            • Counseling crisis hotline (24/7)
            • IT help desk (remote support only)
            • Facilities maintenance (emergency only)
            
            Residence Hall Information:
            • Residence halls remain open for students who cannot travel
            • Dining plan suspended - local meal options provided
            • Guest policies relaxed for family visits
            • Activities planned for students remaining on campus
            • Break housing application required by December 1
            
            For Students:
            Academic Preparation:
            • Complete all final assignments before departure
            • Check email regularly for spring semester updates
            • Register for spring courses during open registration
            • Apply for financial aid and scholarships
            • Plan ahead for textbook purchases
            
            Health and Safety:
            • Update emergency contact information
            • Secure personal belongings in residence halls
            • Follow travel safety guidelines
            • Maintain health insurance coverage
            • Keep important documents accessible
            
            International Students:
            • Verify visa and travel document validity
            • Understand re-entry requirements
            • Maintain F-1 status during break
            • Contact international services with questions
            • Keep passport and I-20 documents safe
            
            For Faculty and Staff:
            • Complete time sheets and expense reports
            • Secure offices and laboratory spaces
            • Set email auto-replies for extended absence
            • Complete required training modules
            • Plan spring semester course preparations
            
            Emergency Contacts:
            • Campus Security: (555) 123-SAFE (7233)
            • Facilities Emergency: (555) 123-HELP (4357)
            • Counseling Crisis Line: (555) 123-TALK (8255)
            • Medical Emergency: 911
            
            Spring Semester Preparation:
            • Course registration opens: December 1
            • Financial aid priority deadline: January 15
            • Textbook orders due: January 5
            • Parking permit renewals: January 8-12
            • Student organization registration: January 10
            
            Campus Updates:
            During the break, several campus improvements will take place:
            • Library renovation completion
            • New student center opening preparations
            • Technology infrastructure upgrades
            • Sustainability initiatives implementation
            • Accessibility improvements in academic buildings
            
            We wish all members of our university community a safe, restful, and joyful winter break!''',
            'start_date': timezone.now() + timedelta(days=75),
            'end_date': timezone.now() + timedelta(days=93),
            'event_type': 'holiday',
            'priority': 'normal',
            'visibility': 'public',
            'created_by': admin_user,
            'all_day': True,
            'is_published': True
        },
        
        {
            'title': 'Career Fair: Technology and Innovation Companies',
            'description': '''Annual technology career fair featuring top companies in software, hardware, and emerging technologies.
            
            Event Overview:
            Connect with leading technology companies for internships, co-ops, and full-time positions.
            This premier career event brings together students and industry professionals for meaningful
            networking and recruitment opportunities.
            
            Participating Companies:
            
            Software and Web Development:
            • Google - Software Engineering, Product Management
            • Microsoft - Cloud Computing, AI Research
            • Amazon - Web Services, E-commerce Platform
            • Meta (Facebook) - Social Platform Development
            • Netflix - Streaming Technology, Content Delivery
            • Spotify - Music Streaming, Data Analytics
            • Airbnb - Travel Platform, Mobile Development
            • Uber - Transportation Technology, Logistics
            
            Enterprise and Consulting:
            • IBM - Enterprise Solutions, Watson AI
            • Oracle - Database Management, Cloud Services
            • Salesforce - CRM Platform, Business Applications
            • Deloitte - Technology Consulting
            • Accenture - Digital Transformation
            • McKinsey Digital - Strategy and Technology
            
            Emerging Technology:
            • Tesla - Autonomous Vehicles, Energy Systems
            • SpaceX - Aerospace Engineering, Software
            • NVIDIA - Graphics Processing, AI Computing
            • Intel - Semiconductor Design, Hardware
            • AMD - Processor Technology, Gaming
            • Qualcomm - Mobile Technology, 5G
            
            Startups and Scale-ups:
            • Various YC-backed startups
            • Local technology companies
            • Emerging fintech companies
            • Healthcare technology innovators
            • Clean energy technology firms
            
            Available Positions:
            
            Internship Opportunities:
            • Software Engineering Intern
            • Data Science and Analytics Intern
            • Product Management Intern
            • UX/UI Design Intern
            • DevOps and Infrastructure Intern
            • Cybersecurity Intern
            • Mobile Development Intern
            • Machine Learning Research Intern
            
            Full-Time Positions:
            • Entry-level Software Engineer
            • Frontend/Backend Developer
            • Full-Stack Developer
            • Data Scientist
            • Product Manager
            • Systems Administrator
            • Quality Assurance Engineer
            • Technical Writer
            
            Event Schedule:
            
            10:00 AM - 12:00 PM: Company Exhibitions
            • Meet recruiters and learn about companies
            • Collect company information and swag
            • Submit resumes and schedule interviews
            • Network with current employees and alumni
            
            12:00 PM - 1:00 PM: Networking Lunch
            • Informal conversations with company representatives
            • Panel discussion with recent graduates
            • Industry trends and career advice
            • Company-sponsored lunch provided
            
            1:00 PM - 3:00 PM: Technical Workshops
            Workshop Track A: "System Design Interviews"
            • Common system design problems
            • Scalability and performance considerations
            • Database and architecture decisions
            • Live coding and whiteboarding practice
            
            Workshop Track B: "Behavioral Interview Success"
            • STAR method for answering questions
            • Common behavioral interview questions
            • Company culture fit assessment
            • Salary negotiation strategies
            
            3:00 PM - 5:00 PM: On-Site Interviews
            • Pre-scheduled interviews with select companies
            • Technical coding challenges
            • System design discussions
            • Final round interviews for some positions
            
            Preparation Tips:
            
            Before the Event:
            • Research participating companies thoroughly
            • Prepare multiple copies of your resume
            • Practice elevator pitch (30-60 seconds)
            • Prepare thoughtful questions about roles and companies
            • Dress professionally (business or business casual)
            • Bring portfolio of projects and work samples
            
            Technical Preparation:
            • Review data structures and algorithms
            • Practice coding problems on LeetCode/HackerRank
            • Prepare to discuss your projects in detail
            • Review system design fundamentals
            • Understand current technology trends
            
            Resume Tips:
            • Tailor resume for each target company
            • Highlight relevant projects and experiences
            • Include links to GitHub and portfolio
            • Quantify achievements with specific metrics
            • Proofread for errors and formatting
            
            Professional Development:
            This career fair is an excellent opportunity to:
            • Build your professional network
            • Learn about industry trends and opportunities
            • Gain interview experience and feedback
            • Understand career paths in technology
            • Connect with alumni working in tech
            
            Follow-Up Actions:
            • Send thank-you emails within 24 hours
            • Connect on LinkedIn with recruiters met
            • Apply to specific positions discussed
            • Prepare for follow-up interviews
            • Join company talent communities
            
            Success Statistics from Previous Years:
            • 85% of participating students receive at least one interview
            • 60% receive internship or job offers within 3 months
            • Average starting salary for graduates: $95,000
            • 95% satisfaction rate among participating students
            
            This event is free for all students and requires advance registration.
            Career services will provide resume review and interview preparation
            in the weeks leading up to the fair.''',
            'start_date': timezone.now() + timedelta(days=35),
            'end_date': timezone.now() + timedelta(days=35, hours=7),
            'event_type': 'meeting',
            'priority': 'high',
            'visibility': 'public',
            'created_by': admin_user,
            'is_published': True,
            'is_featured': True
        }
    ]
    
    created_events = []
    for event_data in sample_events:
        event, created = Event.objects.get_or_create(
            title=event_data['title'],
            defaults=event_data
        )
        if created:
            created_events.append(event)
            print(f"Created event: {event.title}")
        else:
            print(f"Event already exists: {event.title}")
    
    print(f"\nSample data creation complete!")
    print(f"Created {len(created_events)} new events")
    print(f"Total events in database: {Event.objects.count()}")
    
    return created_events


if __name__ == "__main__":
    print("Creating comprehensive sample event data...")
    create_comprehensive_sample_data()
    print("Done!")