# AI Website Project

## Project Status
Current status: File System Browser Implementation Complete

### Completed Steps:
1. Basic project structure setup
2. Virtual environment creation
3. Dependencies installation
4. Flask application factory pattern implementation
5. Basic configuration setup
6. Blueprint structure for authentication and main routes
7. Base template with Bootstrap integration
8. User model implementation
9. Authentication system (login/register)
10. Basic main page template
11. Comprehensive test suite with 98% coverage
12. File system browser with upload/download capabilities

### Next Steps:
- [ ] Python task execution system
- [ ] Security enhancements
- [ ] Deployment configuration

## Features

### Authentication System
- User registration with email verification
- Secure password hashing
- Login with remember me option
- Protected routes requiring authentication
- Flash messages for user feedback

### File Browser
- Secure file system navigation
- File upload with progress tracking
- File download functionality
- Directory browsing
- Security features:
  - Path traversal protection
  - File type validation
  - Authentication required
  - Configurable root directory
- Responsive UI with:
  - Breadcrumb navigation
  - File/directory listing
  - Size and modification date display
  - Progress tracking for uploads

### Testing Coverage
- 98% test coverage across the codebase
- Comprehensive test suite including:
  - User registration tests
  - Login/logout functionality
  - Form validation
  - Protected routes
  - User model methods
  - Database interactions
  - File browser operations
  - Security measures

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip (Python package installer)

### Installation
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows (Command Prompt):
     ```bash
     venv\Scripts\activate
     ```
   - Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   Note: If using PowerShell and encountering execution policy errors, run as administrator:
   ```powershell
   Set-ExecutionPolicy RemoteSigned
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Project Structure
```
ai_website/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── files/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── main/
│   │   ├── __init__.py
│   │   └── routes.py
│   └── templates/
│       ├── base.html
│       ├── auth/
│       │   ├── login.html
│       │   └── register.html
│       ├── files/
│       │   └── browse.html
│       └── main/
│           └── index.html
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_files.py
│   └── test_models.py
├── config.py
├── requirements.txt
└── run.py
```

## Running the Application
To run the application in development mode:
```bash
python run.py
```
The application will be available at `http://localhost:5000`

## Running Tests
To run the test suite with coverage:
```bash
coverage run -m pytest
coverage report
```

## Testing the File Browser

1. Start the application and register a new account or log in
2. Click the "Files" link in the navigation bar
3. Test file browsing:
   - Navigate through directories by clicking on them
   - Use the breadcrumb navigation to go back
   - View file details (size, type, modified date)

4. Test file upload:
   - Click the "Upload Files" button
   - Select one or more files
   - Watch the progress in the upload modal
   - Verify the files appear in the list

5. Test file download:
   - Click the download button next to any file
   - Verify the file downloads correctly

6. Security testing:
   - Verify you can't access files outside the root directory
   - Try uploading invalid file types
   - Attempt to access the file browser without logging in