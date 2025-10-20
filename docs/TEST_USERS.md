# Test Users and Login Credentials

## User Summary
- **Total Users**: 9
- **Admins**: 1
- **Instructors**: 3  
- **Students**: 5

## Login Credentials

### Admin Access
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: admin@testlms.local
- **Role**: System Administrator
- **Access**: Full admin panel access
- **URL**: http://127.0.0.1:8000/admin/

### Instructors (Password: `instructor123`)

#### Prof. John Smith
- **Username**: `prof_smith`
- **Email**: john.smith@university.edu
- **Name**: John Smith
- **Bio**: Computer Science Professor with 15 years of experience in software development and web technologies.
- **Access**: Staff access, can create and manage courses

#### Dr. Sarah Johnson
- **Username**: `dr_johnson`
- **Email**: sarah.johnson@university.edu
- **Name**: Sarah Johnson
- **Bio**: Data Science and Machine Learning expert. PhD in Mathematics with focus on statistical modeling.
- **Access**: Staff access, can create and manage courses

#### Prof. Michael Davis
- **Username**: `prof_davis`
- **Email**: michael.davis@university.edu
- **Name**: Michael Davis
- **Bio**: Web Development and Frontend Design specialist. Former industry developer turned educator.
- **Access**: Staff access, can create and manage courses

### Students (Password: `student123`)

#### Alice Wonder
- **Username**: `alice_wonder`
- **Email**: alice.wonder@student.edu
- **Name**: Alice Wonder
- **Bio**: Computer Science major interested in web development and AI.

#### Bob Builder
- **Username**: `bob_builder`
- **Email**: bob.builder@student.edu
- **Name**: Bob Builder
- **Bio**: Engineering student exploring data science and machine learning applications.

#### Charlie Coder
- **Username**: `charlie_coder`
- **Email**: charlie.coder@student.edu
- **Name**: Charlie Coder
- **Bio**: Self-taught programmer looking to formalize knowledge through structured courses.

#### Diana Developer
- **Username**: `diana_dev`
- **Email**: diana.dev@student.edu
- **Name**: Diana Developer
- **Bio**: Frontend enthusiast with a passion for creating beautiful user interfaces.

#### Evan Explorer
- **Username**: `evan_explorer`
- **Email**: evan.explorer@student.edu
- **Name**: Evan Explorer
- **Bio**: Career changer from marketing to technology. Eager to learn programming fundamentals.

## Sample Course Created
**Introduction to Web Development (WEB101)**
- **Instructor**: Prof. John Smith
- **Duration**: 8 weeks
- **Max Students**: 25
- **Status**: Published
- **Lessons**: 4 (HTML, CSS, JavaScript, Responsive Design)
- **Direct Link**: http://127.0.0.1:8000/course/2/

## Quick Access URLs
- **Course Catalog**: http://127.0.0.1:8000/
- **Student Login**: http://127.0.0.1:8000/login/
- **Student Registration**: http://127.0.0.1:8000/register/
- **Sample Course**: http://127.0.0.1:8000/course/2/
- **Admin Panel**: http://127.0.0.1:8000/admin/

## Testing Instructions

### 1. Test Student Registration & Login
1. Go to http://127.0.0.1:8000/register/
2. Create a new student account
3. Verify automatic login and redirect to student dashboard
4. Test logout and login again at http://127.0.0.1:8000/login/

### 2. Test Existing Student Login
1. Go to http://127.0.0.1:8000/login/
2. Login as alice_wonder / student123
3. Verify redirect to student dashboard
4. Browse course catalog and enroll in web development course

### 3. Test Student Enrollment
1. Login as any student (password: student123)
2. Browse course catalog at http://127.0.0.1:8000/
3. Click on "Introduction to Web Development" course
4. Click "Enroll in Course" button
5. Verify enrollment and access to lessons

### 4. Test Lesson Navigation
1. As an enrolled student, access course lessons
2. Navigate through the 4 lessons (HTML → CSS → JavaScript → Responsive Design)
3. Mark lessons as complete
4. Check progress tracking functionality

### 5. Test Instructor Features
1. Go to http://127.0.0.1:8000/login/
2. Login as any instructor (password: instructor123)
3. Verify redirect to instructor dashboard
4. Access admin panel to create new courses and lessons

### 6. Test Admin Features
1. Go to http://127.0.0.1:8000/login/
2. Login as admin (password: admin123)
3. Verify redirect to Django admin panel
4. Manage all users, courses, and enrollments

## Database Status
- ✅ Fresh database with clean test data
- ✅ All user roles properly configured
- ✅ Signal handlers working for profile creation
- ✅ Terminal theme styling applied
- ✅ Ready for Phase 1.4: User registration

---
*Test users created on: October 1, 2025*
*Database ready for LMS testing and development*