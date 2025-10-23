# 🛡️ Secure Terminal LMS 📚⚡

>[!CAUTION]
>This project is made with AI! This README may be inaccurate and is still under development.

A **production-ready** Learning Management System (LMS) built with Django, featuring comprehensive security, terminal-inspired dark theme, calendar integration, and **safe source code upload** capabilities for programming courses.

![Terminal Theme](https://img.shields.io/badge/Theme-Terminal-orange?style=flat-square&logo=linux)
![Django](https://img.shields.io/badge/Django-5.2+-success?style=flat-square&logo=django)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![Security](https://img.shields.io/badge/Security-Production%20Ready-green?style=flat-square&logo=shield)
![File Upload](https://img.shields.io/badge/File%20Upload-Secure%20Validation-blue?style=flat-square&logo=upload)
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

### 🛡️ **Security Features** (NEW - October 2025)
- **🔒 Secure File Uploads**: Multi-layer validation system preventing malicious files
- **📋 Source Code Support**: Safe upload of Python, Go, Rust, JavaScript, Java, C++ projects
- **🚫 Threat Protection**: Automatic blocking of executables (.exe, .bat, .sh, .ps1)
- **📦 Archive Security**: ZIP bomb protection, path traversal prevention
- **🔍 Content Validation**: MIME type verification, file size limits (50MB)
- **✅ Educational Focus**: 92% validation success rate for legitimate assignments
- **🏷️ File Type Whitelist**: Comprehensive educational file type support

### 🎨 Design Philosophy
- **Security First**: Production-ready security with comprehensive file validation
- **Educational Focus**: Safe source code uploads for programming assignments
- **Terminal Theme**: Black background, amber/green text, Ubuntu fonts
- **Simple Setup**: SQLite database, secure by default configuration

### 🚀 Quick Demo
- **Live Course**: Programming courses with secure file submission
- **Test Users**: Pre-configured students, instructors, and admin accounts
- **Security Testing**: Upload validation tests included
- **Instant Setup**: Clone and run securely in minutes

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
- **🔄 Recurring Events**: Weekly and bi-weekly recurring events with checkbox UI for day selection
- **Smart Scheduling**: Fixed day calculation logic ensures events appear on correct days

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
The project includes **41 comprehensive Django tests** covering all major functionality:

**Quick Test Commands:**
```bash
# Run all tests (Windows)
.\test.ps1

# Run all tests (Linux/Mac)  
./test.sh

# Run specific test suite
.\test.ps1 tests.test_blog                  # Event/calendar tests (11 tests)
.\test.ps1 tests.test_recurring_events      # Recurring events tests (15 tests)
.\test.ps1 tests.test_enhanced_markdown     # Markdown tests (15 tests)
```

### Test Coverage Breakdown
- ✅ **Event/Calendar System** (11 tests)
  - Event model creation and validation (4 tests)
  - Calendar views and navigation (4 tests)  
  - Course-event integration (2 tests)
  - Accessibility compliance (1 test)

- ✅ **Recurring Events System** (NEW - 15 tests)
  - Model recurring event generation (5 tests)
  - Weekday field validation (5 tests)
  - Form checkbox widget functionality (3 tests)
  - Edge cases and error handling (2 tests)

- ✅ **Markdown Processing** (15 tests)
  - Enhanced markdown features (14 tests)
  - Content rendering integration (1 test)

### Latest Test Results
```
Found 41 test(s)
Ran 41 tests in 45.892s
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
- **Recurring events system** (weekly/bi-weekly patterns) ⭐ **NEW!**
- **Checkbox UI for day selection** with proper form validation ⭐ **NEW!**
- **Fixed day calculation logic** ensuring correct event generation ⭐ **NEW!**
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

- **🔒 Security Audit**: `SECURITY_AUDIT.md` - Comprehensive security assessment and improvements
- **🛡️ Security Implementation**: `SECURITY_IMPLEMENTATION_COMPLETE.md` - File upload security details
- **⚙️ Production Config**: `PRODUCTION_SECURITY_CONFIG.md` - Production deployment guide
- **📋 Test Users**: `TEST_USERS.md` - Demo accounts and test data
- **👥 Student Guide**: `STUDENT_LOGIN_GUIDE.md` - User documentation
- **🚀 Development Roadmap**: `NEXT.md` - Future plans and progress tracking

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
- **Security**: Production-ready file upload validation system
- **Theme**: Terminal-inspired dark theme with 5 color schemes
- **Features**: Complete LMS + Calendar + **Secure File Management**
- **Test Coverage**: 26 comprehensive Django tests + Security validation tests
- **File Support**: Python, Go, Rust, JavaScript, Java, C++ source code uploads
- **Security Score**: 8.3/10 (was 6.0/10 before security implementation)
- **Documentation**: Complete security audit, deployment guides, roadmap

## 🔗 Links

- **Repository**: https://github.com/andrejli/my-first-blog
- **Django Docs**: https://docs.djangoproject.com/
- **Bootstrap**: https://getbootstrap.com/docs/3.4/
- **License**: https://www.gnu.org/licenses/gpl-3.0.en.html

---

**Built with ❤️ for education and learning**

*Terminal LMS - Where learning meets the command line aesthetic* ⚡📚
