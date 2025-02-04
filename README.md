# AI Website Project

## Project Status
Current status: Production-Ready File System Implementation

### Completed Features:
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
11. Comprehensive test suite with 93% coverage
12. File system browser with:
    - Upload/download capabilities
    - Network accessibility
    - Progress tracking
    - Security features
    - User isolation
    - Folder creation
    - File deletion
    - Path normalization
    - Duplicate file handling

### Planned Enhancements:
1. File Browser Improvements:
   - [ ] File sharing between users
   - [ ] File preview functionality
   - [ ] Bulk operations (upload/download/delete)
   - [ ] Drag and drop support
2. User System Enhancements:
   - [ ] User profiles
   - [ ] Password reset
   - [ ] Email verification
3. Security Improvements:
   - [ ] Rate limiting
   - [ ] Enhanced session management
   - [ ] Security headers

## Features

### Authentication System
- User registration with email verification
- Secure password hashing
- Login with remember me option
- Protected routes requiring authentication
- Flash messages for user feedback

### File Browser
- Secure file system navigation
- File upload with progress tracking and duplicate handling
- File download functionality
- Directory creation and management
- File deletion capabilities
- User isolation (each user has their own directory)
- Network accessibility (LAN access)
- Security features:
  - Path traversal protection
  - File type validation
  - Authentication required
  - Configurable root directory
  - User directory isolation
- Responsive UI with:
  - Breadcrumb navigation
  - File/directory listing
  - Size and modification date display
  - Progress tracking for uploads
  - Upload status messages
  - Confirmation dialogs for deletion

### API Endpoints
All API endpoints are prefixed with `/files/api`

#### File Operations
- `GET /files/api/list?path=<path>` - List files in directory
- `POST /files/api/upload` - Upload file (multipart/form-data)
  - Parameters: file, path
- `POST /files/api/delete` - Delete file or directory
  - Parameters: path
- `GET /files/api/download/<path>` - Download file
- `POST /files/api/create_folder` - Create new folder
  - Parameters: path, name

### File Browser Structure
The file browser is organized into two main components:
1. View Routes (`/files/*`):
   - Main file browser interface
   - Directory navigation
   - File listings
   - Breadcrumb navigation
2. API Routes (`/files/api/*`):
   - File operations (upload, download, delete)
   - Directory operations (create, list)
   - JSON responses for AJAX requests

### Frontend Components
- Bootstrap 5 for UI components
- Bootstrap Icons for file type indicators
- AJAX for file operations with progress tracking
- Modal dialogs for user interactions
- Responsive design for all screen sizes

### Testing Coverage
- 93% test coverage across the codebase
- Comprehensive test suite including:
  - User registration tests
  - Login/logout functionality
  - Form validation
  - Protected routes
  - User model methods
  - Database interactions
  - File browser operations
  - Security measures

## Project Conventions

### File System Structure
- User files are stored in: `static/uploads/<user_id>/`
- Each user has an isolated directory
- All paths in the database use forward slashes (/)
- File paths are unique per user

### Database Schema
- FileMetadata table:
  - Unique constraint on (filepath, owner_id)
  - Tracks file size, creation time, and modification time
  - Stores relative paths from user's root directory

### Path Handling
- All paths are normalized to use forward slashes
- Trailing slashes are removed
- Empty paths are handled as root directory
- Parent directory navigation is secure

### Security Measures
- File paths are validated against user's root directory
- Filenames are sanitized using werkzeug.secure_filename
- Database operations use SQLAlchemy for SQL injection protection
- All file operations require authentication

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip (Python package installer)
- SQLite 3

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
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Initialize the database:
   ```bash
   flask db upgrade
   ```
6. Run the development server:
   ```bash
   flask run --host=0.0.0.0
   ```
   Note: The --host flag allows network access

### Running Tests
```bash
python -m pytest
```

## Directory Structure
```
ai_website/
├── app/
│   ├── auth/           # Authentication blueprint
│   ├── files/          # File browser blueprint
│   ├── static/
│   │   └── uploads/    # User file storage
│   └── templates/      # HTML templates
├── migrations/         # Database migrations
├── tests/             # Test suite
├── venv/              # Virtual environment
├── config.py          # Configuration
└── requirements.txt   # Dependencies