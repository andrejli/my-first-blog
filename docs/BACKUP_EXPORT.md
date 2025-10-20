# Course Backup and Export/Import System Guide

## 📚 **Terminal LMS Course Import/Export Manual**

*Comprehensive guide for backing up, exporting, and importing courses in the Terminal LMS*

---

## 🎯 **Table of Contents**

1. [Overview](#overview)
2. [Course Export System](#course-export-system)
3. [Course Import System](#course-import-system)
4. [Backup Strategies](#backup-strategies)
5. [Data Migration](#data-migration)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)
8. [Technical Specifications](#technical-specifications)

---

## 🔍 **Overview**

The Terminal LMS Course Import/Export system provides comprehensive tools for backing up, sharing, and migrating course content. This system enables instructors and administrators to:

- **Create complete course backups** with all content and settings
- **Share course templates** between instructors and institutions
- **Migrate courses** between LMS instances
- **Restore courses** from backup files
- **Create course templates** for reuse

### **Key Features:**
- ✅ **Complete Course Data**: All lessons, assignments, quizzes, materials, and announcements
- ✅ **File Preservation**: Course materials and attachments included in exports
- ✅ **Flexible Import**: Customizable course codes and instructor assignment
- ✅ **Privacy Controls**: Optional student data inclusion
- ✅ **Conflict Resolution**: Handles duplicate course codes and content
- ✅ **Version Compatibility**: Forward and backward compatibility support

---

## 📤 **Course Export System**

### **Accessing Course Export**

**For Instructors:**
1. Navigate to your **Instructor Dashboard**
2. Select the course you want to export
3. Click **"Backup & Import" → "Export Course"**
4. Configure export options and download

**Direct URL:** `/instructor/course/{course_id}/export/`

### **Export Options**

#### **Standard Export (Recommended)**
- **Includes**: Course structure, lessons, assignments, quizzes, materials, announcements
- **Excludes**: Student enrollments, progress data, submissions
- **Use Case**: Course templates, sharing, general backups

#### **Full Export with Student Data**
- **Includes**: Everything in Standard Export + student enrollments, progress, submissions
- **Use Case**: Complete course migration, institutional transfers
- **Privacy Note**: Contains personal student information

### **Export Process**

#### **Step 1: Select Export Type**
```
[ ] Include Student Data
    ├── Student enrollments and grades
    ├── Lesson completion progress  
    ├── Assignment submissions
    └── Quiz attempts and scores
```

#### **Step 2: Review Export Summary**
The system displays:
- Course information and metadata
- Content counts (lessons, assignments, quizzes, materials)
- File size estimates
- Privacy warnings (if student data included)

#### **Step 3: Download Export File**
- **Format**: ZIP archive
- **Filename**: `{COURSE_CODE}_{TIMESTAMP}.zip`
- **Contents**: 
  - `course_data.json` (structured course data)
  - `materials/` (course files and attachments)
  - `assignments/` (assignment files)

### **Export File Structure**

```
COURSE_EXPORT.zip
├── course_data.json          # Main course data
├── materials/                # Course materials
│   ├── document1.pdf
│   ├── presentation.pptx
│   └── image.jpg
└── assignments/              # Assignment files
    ├── assignment1.pdf
    └── project_template.docx
```

### **JSON Data Structure**

```json
{
  "export_info": {
    "exported_at": "2025-10-15T14:30:00Z",
    "lms_version": "1.0",
    "export_format_version": "1.0",
    "include_user_data": false
  },
  "course": {
    "title": "Course Title",
    "course_code": "CS101",
    "description": "Course description...",
    "instructor_username": "instructor",
    "duration_weeks": 12,
    "max_students": 30,
    "prerequisites": "Basic programming knowledge"
  },
  "lessons": [
    {
      "title": "Introduction to Programming",
      "content": "Lesson content in enhanced markdown...",
      "order": 1,
      "video_url": "https://youtube.com/watch?v=example",
      "is_published": true
    }
  ],
  "assignments": [...],
  "quizzes": [...],
  "materials": [...],
  "announcements": [...]
}
```

---

## 📥 **Course Import System**

### **Accessing Course Import**

**For Instructors:**
1. Go to **Instructor Dashboard**
2. Click **"Import Course"** in Quick Actions
3. Upload course export file
4. Configure import settings
5. Confirm import

**Direct URL:** `/instructor/course/import/`

### **Import Process**

#### **Step 1: Upload Course File**
- **Supported Formats**: ZIP files from Terminal LMS exports
- **File Size Limit**: 100MB
- **Validation**: Automatic validation of file structure and content

#### **Step 2: Preview and Configure**
After upload, the system displays:

**Course Preview:**
- Original course information
- Content summary (lessons, assignments, quizzes, materials)
- Export metadata and version information
- File list and included materials

**Import Configuration:**
- **New Course Code**: Must be unique in your LMS
- **Instructor Assignment**: Option to assign to yourself
- **Import Notes**: Warnings and important information

#### **Step 3: Confirm Import**
- Review all settings and warnings
- Confirm the import operation
- Monitor import progress

### **Import Behavior**

#### **Course Creation:**
- **Status**: Always imported as "Draft" for review
- **Instructor**: Assigned to importing user (unless specified otherwise)
- **Code**: Must be unique (no duplicates allowed)

#### **Content Import:**
- **Lessons**: Imported as unpublished for review
- **Assignments**: Imported as unpublished with original due dates
- **Quizzes**: Imported as unpublished with all questions and answers
- **Materials**: Files copied to new course structure
- **Announcements**: Imported as unpublished for review

#### **Post-Import Tasks:**
1. **Review Content**: Check all imported lessons and assignments
2. **Update Dates**: Adjust assignment due dates and quiz availability
3. **Publish Content**: Selectively publish lessons and assignments
4. **Configure Course**: Update course status from Draft to Published
5. **Test Functionality**: Verify quizzes, assignments, and materials work correctly

---

## 💾 **Backup Strategies**

### **Regular Backup Schedule**

#### **Weekly Backups (Recommended)**
- Export courses without student data
- Store in secure location
- Rotate old backups (keep last 4 weeks)

#### **End-of-Term Backups**
- Export with full student data
- Archive for institutional records
- Include grade reports and analytics

#### **Pre-Major Changes**
- Export before significant course modifications
- Create restore point for rollback capability
- Document changes for version control

### **Backup Storage Options**

#### **Local Storage**
- Download to instructor's computer
- Store on institutional file servers
- Use cloud storage (Google Drive, OneDrive, etc.)

#### **Institutional Backup**
- IT department managed backups
- Automated backup scripts
- Centralized storage systems

### **Backup Verification**

#### **Test Restore Process**
1. Periodically test import process
2. Verify file integrity
3. Check content completeness
4. Validate quiz and assignment functionality

#### **Backup Documentation**
- Maintain backup logs
- Document backup locations
- Record restore procedures
- Update emergency contacts

---

## 🔄 **Data Migration**

### **Between LMS Instances**

#### **Same Institution Migration**
- Export from source LMS
- Import to destination LMS
- Verify instructor accounts exist
- Update course references and links

#### **Cross-Institution Transfer**
- Export course templates (without student data)
- Coordinate with receiving institution
- Map instructor accounts
- Adapt content for new environment

### **LMS Upgrade Migration**

#### **Version Compatibility**
- Export from older LMS version
- Import to newer version
- Check format compatibility
- Update deprecated features

#### **Bulk Migration**
- Plan migration sequence
- Test with sample courses
- Execute in phases
- Verify all content

### **Migration Checklist**

#### **Pre-Migration**
- [ ] Inventory all courses to migrate
- [ ] Verify instructor accounts in destination
- [ ] Test migration with sample course
- [ ] Plan migration timeline
- [ ] Notify affected users

#### **During Migration**
- [ ] Export courses in batches
- [ ] Verify file integrity
- [ ] Import with new course codes
- [ ] Test functionality
- [ ] Document any issues

#### **Post-Migration**
- [ ] Verify all content imported correctly
- [ ] Update course links and references
- [ ] Republish course content
- [ ] Train instructors on changes
- [ ] Monitor for issues

---

## 🔧 **Troubleshooting**

### **Common Export Issues**

#### **Export Fails to Complete**
**Symptoms**: Export process stops or times out
**Causes**: 
- Large course materials
- Network connectivity issues
- Server resource limitations

**Solutions**:
1. Try exporting without student data first
2. Remove large materials temporarily
3. Export during low-traffic hours
4. Contact system administrator for resource limits

#### **Missing Files in Export**
**Symptoms**: Materials or attachments not included
**Causes**:
- File permissions issues
- Missing file references
- Corrupted files

**Solutions**:
1. Check file permissions
2. Re-upload missing materials
3. Verify file paths are correct
4. Export course materials separately

#### **Export File Too Large**
**Symptoms**: Download fails or file won't upload elsewhere
**Causes**:
- Many large course materials
- High-resolution images/videos
- Multiple assignment attachments

**Solutions**:
1. Compress large images/documents
2. Remove or replace large video files with links
3. Use file hosting for large materials
4. Export in multiple smaller chunks

### **Common Import Issues**

#### **Course Code Conflicts**
**Symptoms**: "Course code already exists" error
**Solutions**:
1. Use modified course code (CS101-2025, CS101-IMPORT, etc.)
2. Check for archived courses with same code
3. Contact administrator to resolve conflicts

#### **Import Validation Errors**
**Symptoms**: "Invalid course file" or "Missing required data"
**Causes**:
- Corrupted ZIP file
- Incompatible export format
- Missing course_data.json

**Solutions**:
1. Re-download the export file
2. Verify file integrity
3. Check export format version
4. Try exporting course again

#### **Incomplete Content Import**
**Symptoms**: Some lessons, assignments, or quizzes missing
**Causes**:
- Import timeout
- File permission issues
- Database constraints

**Solutions**:
1. Check import logs for errors
2. Verify all content in original export
3. Try importing again
4. Contact technical support

#### **File Upload Failures**
**Symptoms**: Materials not importing properly
**Causes**:
- File size limits
- File type restrictions
- Storage space limitations

**Solutions**:
1. Check file size limits (default 10MB)
2. Verify allowed file types
3. Ensure adequate storage space
4. Upload large files separately

### **Performance Issues**

#### **Slow Export/Import**
**Causes**:
- Large course materials
- High server load
- Network congestion

**Solutions**:
1. Schedule during off-peak hours
2. Compress materials before export
3. Use wired network connection
4. Close unnecessary applications

#### **Memory or Timeout Errors**
**Causes**:
- Insufficient server resources
- Very large courses
- Complex quiz structures

**Solutions**:
1. Contact system administrator
2. Split large courses into modules
3. Reduce quiz complexity temporarily
4. Increase server timeout limits

### **Data Integrity Issues**

#### **Missing Quiz Questions/Answers**
**Symptoms**: Quizzes import but questions are missing
**Causes**:
- Complex question types
- Malformed answer data
- Export corruption

**Solutions**:
1. Verify original quiz structure
2. Re-create problematic questions
3. Check answer format consistency
4. Use simpler question types

#### **Broken File Links**
**Symptoms**: Materials show as missing or inaccessible
**Causes**:
- File path changes
- Permission issues
- Missing file references

**Solutions**:
1. Re-upload affected materials
2. Update file references
3. Check file permissions
4. Verify file storage location

---

## 💡 **Best Practices**

### **Export Best Practices**

#### **Regular Backup Schedule**
- **Weekly**: Export active courses without student data
- **Monthly**: Full backup with student data
- **Semester End**: Complete archive with all data

#### **File Organization**
- Use consistent naming conventions
- Include date and version in filenames
- Store exports in organized folder structure
- Document export purposes and contents

#### **Version Control**
- Keep multiple versions of course exports
- Document major changes between versions
- Use meaningful export descriptions
- Maintain changelog for significant updates

### **Import Best Practices**

#### **Pre-Import Preparation**
1. **Plan Course Code**: Choose unique, meaningful code
2. **Review Content**: Check original course before import
3. **Prepare Materials**: Ensure all files are accessible
4. **Schedule Time**: Allow adequate time for review post-import

#### **Post-Import Review**
1. **Content Verification**: Check all lessons and materials
2. **Date Updates**: Adjust assignment due dates and quiz availability
3. **Publishing Workflow**: Gradually publish content after review
4. **Testing**: Verify all functionality works correctly

#### **Security Considerations**
- **Student Data**: Only include when necessary
- **File Access**: Verify proper permissions on imported materials
- **Content Review**: Check for sensitive information
- **Privacy Compliance**: Follow institutional privacy policies

### **Backup Management**

#### **Storage Strategy**
- **3-2-1 Rule**: 3 copies, 2 different media, 1 offsite
- **Multiple Locations**: Local, cloud, and institutional storage
- **Access Control**: Limit access to authorized personnel
- **Encryption**: Encrypt backups containing student data

#### **Retention Policies**
- **Active Courses**: Weekly backups for 1 semester
- **Completed Courses**: Monthly backups for 2 years
- **Archived Courses**: Yearly backups for 7 years
- **Legal Requirements**: Follow institutional retention policies

### **Migration Planning**

#### **Testing Strategy**
1. **Pilot Migration**: Test with sample courses first
2. **User Acceptance**: Get instructor approval before migration
3. **Rollback Plan**: Maintain ability to revert changes
4. **Communication**: Keep users informed throughout process

#### **Change Management**
- **Training**: Provide training on new features/changes
- **Documentation**: Update user guides and help materials
- **Support**: Increase support capacity during migration
- **Feedback**: Collect and address user feedback

---

## 🔧 **Technical Specifications**

### **File Format Specifications**

#### **Export Archive Structure**
```
{COURSE_CODE}_{TIMESTAMP}.zip
├── course_data.json          # Required: Main course data
├── materials/               # Optional: Course materials
│   ├── {file1}
│   └── {file2}
└── assignments/            # Optional: Assignment files
    ├── {assignment_file1}
    └── {assignment_file2}
```

#### **JSON Schema Version 1.0**

**Export Information:**
```json
{
  "export_info": {
    "exported_at": "ISO 8601 timestamp",
    "exported_by": "username or system",
    "lms_version": "string",
    "export_format_version": "string",
    "include_user_data": boolean
  }
}
```

**Course Data:**
```json
{
  "course": {
    "title": "string (max 200 chars)",
    "course_code": "string (max 20 chars)",
    "description": "text",
    "instructor_username": "string",
    "instructor_email": "string",
    "instructor_first_name": "string",
    "instructor_last_name": "string",
    "created_date": "ISO 8601 timestamp",
    "published_date": "ISO 8601 timestamp or null",
    "status": "draft|published|archived",
    "duration_weeks": integer,
    "max_students": integer,
    "prerequisites": "text"
  }
}
```

**Lesson Data:**
```json
{
  "lessons": [
    {
      "title": "string (max 200 chars)",
      "content": "text (enhanced markdown)",
      "order": integer,
      "video_url": "URL or empty string",
      "created_date": "ISO 8601 timestamp",
      "is_published": boolean
    }
  ]
}
```

**Assignment Data:**
```json
{
  "assignments": [
    {
      "title": "string (max 200 chars)",
      "description": "text",
      "instructions": "text",
      "due_date": "ISO 8601 timestamp",
      "max_points": integer,
      "allow_file_submission": boolean,
      "allow_text_submission": boolean,
      "created_date": "ISO 8601 timestamp",
      "is_published": boolean,
      "file_name": "string or null",
      "file_path": "string or null"
    }
  ]
}
```

**Quiz Data:**
```json
{
  "quizzes": [
    {
      "title": "string (max 200 chars)",
      "description": "text",
      "quiz_type": "practice|graded|exam",
      "time_limit": "integer minutes or null",
      "max_attempts": integer,
      "available_from": "ISO 8601 timestamp or null",
      "available_until": "ISO 8601 timestamp or null",
      "shuffle_questions": boolean,
      "show_correct_answers": boolean,
      "immediate_feedback": boolean,
      "points": number,
      "passing_score": "number or null",
      "is_published": boolean,
      "created_date": "ISO 8601 timestamp",
      "questions": [
        {
          "question_text": "text",
          "question_type": "multiple_choice|true_false|short_answer",
          "points": number,
          "order": integer,
          "explanation": "text",
          "created_date": "ISO 8601 timestamp",
          "answers": [
            {
              "answer_text": "string (max 500 chars)",
              "is_correct": boolean,
              "order": integer
            }
          ]
        }
      ]
    }
  ]
}
```

### **System Requirements**

#### **Server Requirements**
- **PHP Memory**: Minimum 256MB, Recommended 512MB
- **Upload Limit**: Minimum 100MB
- **Execution Time**: Minimum 300 seconds for large exports
- **Storage**: Adequate space for temporary files during processing

#### **Client Requirements**
- **Browser**: Modern browser with JavaScript enabled
- **Connection**: Stable internet connection for file uploads
- **Storage**: Local storage space for downloaded export files

### **API Endpoints**

#### **Export Course**
```
POST /instructor/course/{id}/export/
Content-Type: application/x-www-form-urlencoded

Parameters:
- include_user_data: boolean (optional)

Response:
Content-Type: application/zip
Content-Disposition: attachment; filename="{course_code}_{timestamp}.zip"
```

#### **Import Course Upload**
```
POST /instructor/course/import/
Content-Type: multipart/form-data

Parameters:
- course_file: file (ZIP format)

Response:
- Success: Import preview page
- Error: Import form with error messages
```

#### **Confirm Import**
```
POST /instructor/course/import/confirm/
Content-Type: application/x-www-form-urlencoded

Parameters:
- course_code: string (required)
- assign_to_me: boolean (optional)

Response:
- Success: Redirect to course detail page
- Error: Import form with error messages
```

### **File Size Limits**

#### **Default Limits**
- **Course Materials**: 10MB per file
- **Assignment Attachments**: 10MB per file
- **Total Export Size**: 500MB recommended maximum
- **Import File Size**: 100MB default limit

#### **Configuring Limits**
Administrators can adjust limits in Django settings:
```python
# File upload limits
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB

# Course export limits
COURSE_EXPORT_MAX_SIZE = 500 * 1024 * 1024  # 500MB
COURSE_IMPORT_TIMEOUT = 300  # 5 minutes
```

### **Security Considerations**

#### **File Validation**
- ZIP file structure validation
- JSON schema validation
- File type checking for materials
- Virus scanning (if available)

#### **Access Control**
- Instructor-only access to export/import
- Course ownership verification for exports
- User authentication required
- CSRF protection on all forms

#### **Data Privacy**
- Optional student data inclusion
- Clear warnings about personal information
- Audit logging of export/import operations
- Compliance with privacy regulations

---

## 📞 **Support and Resources**

### **Getting Help**

#### **Technical Support**
- **System Administrators**: For server-related issues
- **LMS Support Team**: For functional questions
- **IT Help Desk**: For general technical assistance

#### **Documentation**
- **User Guides**: Complete LMS user documentation
- **Video Tutorials**: Step-by-step import/export demos
- **FAQ**: Common questions and solutions
- **Best Practices**: Institutional guidelines

#### **Training Resources**
- **Instructor Training**: Comprehensive LMS training program
- **Backup Workshops**: Hands-on backup and restore training
- **Migration Support**: Assistance with large-scale migrations

### **Emergency Procedures**

#### **Data Loss Scenarios**
1. **Contact IT immediately**
2. **Stop using the affected course**
3. **Identify most recent backup**
4. **Coordinate with system administrators for restore**
5. **Verify data integrity after restoration**

#### **Emergency Contacts**
- **LMS Administrator**: [Contact Information]
- **IT Help Desk**: [Contact Information]
- **System Administrator**: [Contact Information]
- **Data Recovery Team**: [Contact Information]

---

## 📋 **Appendices**

### **Appendix A: Export Checklist**

#### **Pre-Export Checklist**
- [ ] Verify course content is complete and current
- [ ] Check all materials are accessible
- [ ] Review privacy requirements for student data
- [ ] Confirm adequate storage space for export file
- [ ] Document export purpose and retention requirements

#### **Export Process Checklist**
- [ ] Select appropriate export options
- [ ] Include/exclude student data as needed
- [ ] Verify export completes successfully
- [ ] Test export file integrity
- [ ] Store export in secure location
- [ ] Document export details and location

### **Appendix B: Import Checklist**

#### **Pre-Import Checklist**
- [ ] Verify export file integrity
- [ ] Choose unique course code
- [ ] Plan post-import review process
- [ ] Ensure adequate time for content review
- [ ] Prepare for date and settings updates

#### **Import Process Checklist**
- [ ] Upload export file successfully
- [ ] Review course preview carefully
- [ ] Configure import settings appropriately
- [ ] Complete import process
- [ ] Verify all content imported correctly
- [ ] Update dates and publish settings

#### **Post-Import Checklist**
- [ ] Review all imported lessons
- [ ] Check assignment settings and due dates
- [ ] Verify quiz questions and answers
- [ ] Test all course materials and links
- [ ] Update course status and publish content
- [ ] Notify students of course availability

### **Appendix C: Troubleshooting Quick Reference**

#### **Export Issues**
| Problem | Quick Solution |
|---------|----------------|
| Export times out | Try without student data |
| File too large | Remove large materials temporarily |
| Missing materials | Check file permissions |
| Process fails | Contact system administrator |

#### **Import Issues**
| Problem | Quick Solution |
|---------|----------------|
| Course code exists | Use modified course code |
| Upload fails | Check file size and format |
| Content missing | Verify original export |
| Import errors | Check error logs and retry |

#### **File Issues**
| Problem | Quick Solution |
|---------|----------------|
| Materials missing | Re-upload files manually |
| Links broken | Update file references |
| Large files fail | Use external file hosting |
| Access denied | Check file permissions |

---

**📅 Last Updated**: October 15, 2025  
**🔧 Version**: 1.0  
**👤 Maintained by**: Terminal LMS Development Team  

*For the most current version of this guide, please check the LMS documentation section or contact your system administrator.*