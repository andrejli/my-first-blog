# Terminal LMS 📚⚡

An ultralight Learning Management System (LMS) built with Django, featuring a terminal-inspired dark theme, calendar integration, and focused on simplicity and educational use.

![Terminal Theme](https://img.shields.io/badge/Theme-Terminal-orange?style=flat-square&logo=linux)
![Django](https://img.shields.io/badge/Django-5.2+-success?style=flat-square&logo=django)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-GPL%20v3-blue?style=flat-square)
![Calendar](https://img.shields.io/badge/Events-Calendar-green?style=flat-square&logo=calendar)

## 🎯 Features

### ✅ Core LMS Functionality
- **User Management**: Students, Instructors, and Admins with role-based access
- **Course Catalog**: Browse and discover available courses
- **Enrollment System**: Simple one-click course enrollment
- **Content Delivery**: Structured lessons with progress tracking
- **Progress Tracking**: Mark lessons complete and track learning progress
- **Authentication**: Frontend login/registration separate from admin panel
- **📅 Calendar System**: Integrated event calendar with admin-managed events
- **📁 File Management**: Event posters and materials upload (admin-only)

### 🎨 Design Philosophy
- **Ultralight**: Minimal dependencies, maximum functionality
- **Terminal Theme**: Black background, amber/green text, Ubuntu fonts
- **Educational Focus**: Built for learning and teaching
- **Simple Setup**: SQLite database, no complex configuration

### 🚀 Quick Demo
- **Live Course**: "Introduction to Web Development" with 4 lessons
- **Test Users**: Pre-configured students, instructors, and admin accounts
- **Instant Setup**: Clone and run in minutes

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Test Accounts](#-test-accounts)
- [Project Structure](#-project-structure)
- [Features Overview](#-features-overview)
- [Testing](#-testing)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/andrejli/my-first-blog.git
cd my-first-blog

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

### Access the LMS
- **Main Site**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/

## 🚀 Quick Start

### 1. Browse as Guest
Visit http://127.0.0.1:8000/ to browse the course catalog without logging in.

### 2. Student Experience
```
Register: http://127.0.0.1:8000/register/
→ Create account → Auto-login → Browse courses → Enroll → Learn
```

### 3. Use Test Accounts
- **Student**: `alice_wonder` / `student123`
- **Instructor**: `prof_smith` / `instructor123`
- **Admin**: `admin` / `admin123`

## 👥 Test Accounts

The system comes pre-populated with test data for immediate exploration:

### 🔑 Login Credentials

| Role | Username | Password | Purpose |
|------|----------|----------|---------|
| **Admin** | `admin` | `admin123` | Full system management |
| **Instructors** | `prof_smith` | `instructor123` | John Smith - CS Professor |
| | `dr_johnson` | `instructor123` | Sarah Johnson - Data Science |
| | `prof_davis` | `instructor123` | Michael Davis - Web Dev |
| **Students** | `alice_wonder` | `student123` | CS major interested in web dev |
| | `bob_builder` | `student123` | Engineering student |
| | `charlie_coder` | `student123` | Self-taught programmer |
| | `diana_dev` | `student123` | Frontend enthusiast |
| | `evan_explorer` | `student123` | Career changer |

### 📚 Sample Content
- **Course**: "Introduction to Web Development (WEB101)"
- **Lessons**: HTML, CSS, JavaScript, Responsive Design
- **Instructor**: Prof. John Smith
- **Enrollment**: Alice Wonder is already enrolled for testing

### 📅 Calendar & Events Access ⭐ **NEW!**
- **Calendar View**: http://127.0.0.1:8000/calendar/ (login required)
- **Homepage Events**: Sidebar shows today's events and featured events
- **Admin Event Management**: http://127.0.0.1:8000/admin/blog/event/ (admin only)
- **Sample Events**: Pre-loaded with upcoming events, deadlines, and workshops
- **File Attachments**: Sample event includes poster and materials downloads

## 📁 Project Structure

```
my-first-blog/
├── blog/                   # Main Django app
│   ├── models.py          # LMS data models
│   ├── views.py           # Course and auth views
│   ├── admin.py           # Enhanced admin interface
│   ├── urls.py            # URL routing
│   ├── templates/blog/    # Terminal-themed templates
│   └── static/css/        # Terminal styling
├── mysite/                # Django project settings
│   ├── settings.py        # Configuration
│   ├── urls.py           # Root URL config
│   └── wsgi.py           # WSGI deployment
├── static/                # Collected static files
├── requirements.txt       # Python dependencies
├── manage.py             # Django management
└── db.sqlite3           # SQLite database (auto-created)
```

## 🎓 Features Overview

### User Roles & Permissions
- **Students**: Enroll in courses, access lessons, track progress
- **Instructors**: Create courses, manage content, view enrollments
- **Admins**: Full system access, user management, system configuration

### Course Management
- Course catalog with descriptions and metadata
- Lesson organization with sequential ordering
- Enrollment tracking and capacity limits
- Progress monitoring and completion status

### 📅 Calendar & Events System ⭐ **NEW!**
- **Event Management**: Admin-only event creation, editing, and management
- **Calendar Views**: Monthly calendar grid with event display and navigation
- **Event Types**: General, Deadlines, Exams, Holidays, Maintenance, Meetings, Workshops, Announcements
- **Priority Levels**: Urgent, High, Normal, Low with color-coded display
- **File Attachments**: Upload event posters (images) and materials (documents)
- **Homepage Integration**: Today's events and featured events displayed on homepage sidebar
- **Event Details**: Full event information with course linking and metadata
- **Responsive Design**: Mobile-friendly calendar and event displays

### Authentication System
- Frontend registration for students
- Role-based login redirects
- Secure session management
- Password validation and security

### Terminal Theme Design
- Dark background with amber/green text
- Ubuntu Mono font family
- Retro terminal aesthetics
- Mobile-responsive design
- Bootstrap 3.2 integration

## 🧪 Testing

### Comprehensive Test Suite
The project includes **26 comprehensive Django tests** covering all major functionality:

**Quick Test Commands:**
```bash
# Run all tests (Windows)
.\test.ps1

# Run all tests (Linux/Mac)  
./test.sh

# Run specific test suite
.\test.ps1 blog.tests              # Event/calendar tests (11 tests)
.\test.ps1 tests.test_enhanced_markdown  # Markdown tests (15 tests)
```

### Test Coverage Breakdown
- ✅ **Event/Calendar System** (11 tests)
  - Event model creation and validation (4 tests)
  - Calendar views and navigation (4 tests)  
  - Course-event integration (2 tests)
  - Accessibility compliance (1 test)

- ✅ **Markdown Processing** (15 tests)
  - Enhanced markdown features (14 tests)
  - Content rendering integration (1 test)

### Latest Test Results
```
Found 26 test(s)
Ran 26 tests in 31.634s
OK
```

**Features Validated:**
- Responsive layout fixes (mobile, tablet, desktop)
- Font size improvements (20-30% increase)
- Poster display with thumbnails and hover effects
- Authentication and authorization flows
- Event creation, properties, and file attachments
- Calendar navigation and month switching
- Course-event integration
- Markdown processing (wiki links, callouts, code blocks)
- Security escaping and content validation
- Accessibility guidelines compliance

### Manual Testing
For comprehensive testing instructions and test data, see [`TESTING.md`](TESTING.md).

## 🔧 Development

### Database Models
- **UserProfile**: Extended user data with roles
- **Course**: Course information and metadata
- **Enrollment**: Student-course relationships
- **Lesson**: Course content organization
- **Progress**: Learning progress tracking
- **Event**: Calendar events with file attachments ⭐ **NEW!**

### Adding New Features
1. Create models in `blog/models.py`
2. Add views in `blog/views.py`
3. Create templates in `blog/templates/blog/`
4. Update URLs in `blog/urls.py`
5. Run migrations: `python manage.py makemigrations && python manage.py migrate`

### Customization
- **Colors**: Edit `blog/static/css/blog.css`
- **Layout**: Modify `blog/templates/blog/base.html`
- **Models**: Extend models in `blog/models.py`
- **Settings**: Configure in `mysite/settings.py`

## 🚀 Deployment

### Production Considerations
1. **Security**: Change `SECRET_KEY` and set `DEBUG = False`
2. **Database**: Consider PostgreSQL for production
3. **Static Files**: Use WhiteNoise or CDN
4. **Web Server**: Deploy with Gunicorn + Nginx
5. **Environment**: Use environment variables for sensitive settings

### Docker Deployment (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "mysite.wsgi:application"]
```

## 🗺️ Roadmap

### Phase 2: Content Management (Planned)
- [ ] File upload system for course materials
- [ ] Rich text editor for lesson content
- [ ] Video lesson support
- [ ] Assignment submission system

### Phase 3: Assessment (Future)
- [ ] Quiz and test creation
- [ ] Automated grading
- [ ] Certificate generation
- [ ] Progress analytics

### Phase 4: Communication (Future)
- [ ] Discussion forums
- [ ] Direct messaging
- [ ] Course announcements
- [ ] Email notifications

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Development Guidelines
- Follow Django best practices
- Maintain the terminal theme aesthetic
- Write clear, documented code
- Test with the provided test accounts
- Update documentation for new features

## 📝 Documentation

- **Security Audit**: See `SECURITY_AUDIT.md`
- **Test Users**: See `TEST_USERS.md`
- **Student Login Guide**: See `STUDENT_LOGIN_GUIDE.md`
- **Development Progress**: See `NEXT.md`

## 🐛 Troubleshooting

### Common Issues
- **Migration Errors**: Delete `db.sqlite3` and run `python manage.py migrate`
- **Static Files**: Run `python manage.py collectstatic`
- **Permission Issues**: Check user roles in admin panel
- **Theme Issues**: Clear browser cache and check CSS files

### Getting Help
- Check the documentation files in the repository
- Review the Django official documentation
- Open an issue on GitHub for bugs or questions

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

### What this means:
- ✅ **Commercial use** allowed
- ✅ **Modification** allowed
- ✅ **Distribution** allowed
- ✅ **Private use** allowed
- ❗ **License and copyright notice** required
- ❗ **State changes** required
- ❗ **Disclose source** required
- ❌ **Liability** - No warranty
- ❌ **Warranty** - No warranty

## 🙏 Acknowledgments

- **Django Framework** - The web framework for perfectionists with deadlines
- **Bootstrap** - Frontend component library for responsive design
- **Ubuntu Fonts** - Beautiful monospace typography
- **Pillow** - Python imaging library for poster uploads
- **Font Awesome** - Icons for calendar and file management
- **Educational Community** - For inspiring simple, effective learning tools

## 📊 Project Stats

- **Language**: Python (Django 5.2+)
- **Database**: SQLite (development), PostgreSQL ready
- **Frontend**: HTML5, CSS3, Bootstrap 3.2
- **Theme**: Terminal-inspired dark theme with 5 color schemes
- **Features**: Complete LMS + Calendar + File Management
- **Test Coverage**: 26 comprehensive Django tests (event/calendar + markdown processing)
- **Documentation**: Comprehensive guides and roadmap included
- **File Uploads**: Event posters, materials, and course content support

## 🔗 Links

- **Repository**: https://github.com/andrejli/my-first-blog
- **Django Docs**: https://docs.djangoproject.com/
- **Bootstrap**: https://getbootstrap.com/docs/3.4/
- **License**: https://www.gnu.org/licenses/gpl-3.0.en.html

---

**Built with ❤️ for education and learning**

*Terminal LMS - Where learning meets the command line aesthetic* ⚡📚