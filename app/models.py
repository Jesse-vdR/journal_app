from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login
import os

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    storage_used = db.Column(db.BigInteger, default=0)  # Storage used in bytes
    storage_limit = db.Column(db.BigInteger, default=104857600)  # Default 100MB in bytes
    home_directory = db.Column(db.String(256), unique=True, name='_user_home_directory_uc')
    files = db.relationship('FileMetadata', backref='owner', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        if len(password) < 3:
            raise ValueError("Password must be at least 3 characters long")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

    def get_storage_used_mb(self):
        """Get storage used in MB"""
        return round(self.storage_used / (1024 * 1024), 2)

    def get_storage_limit_mb(self):
        """Get storage limit in MB"""
        return round(self.storage_limit / (1024 * 1024), 2)

    def get_storage_remaining_mb(self):
        """Get remaining storage in MB"""
        return round((self.storage_limit - self.storage_used) / (1024 * 1024), 2)

    def has_storage_space(self, size_bytes):
        """Check if user has enough storage space for a file of given size"""
        return (self.storage_used + size_bytes) <= self.storage_limit

    def get_home_directory(self):
        if not self.home_directory:
            # Create a unique home directory path if not set
            base_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
            self.home_directory = os.path.join(base_path, f'user_{self.id}')
            db.session.commit()
            # Ensure the directory exists
            os.makedirs(self.home_directory, exist_ok=True)
        return self.home_directory

class FileMetadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    filetype = db.Column(db.String(64))
    filesize = db.Column(db.Integer)  # Size in bytes
    is_directory = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('filepath', 'owner_id', name='uix_filepath_owner'),
    )

    def __repr__(self):
        return f'<FileMetadata {self.filename}>'

    @property
    def file_type_icon(self):
        """Return appropriate Bootstrap icon class based on file type"""
        if self.is_directory:
            return 'bi-folder'
        
        ext = self.filename.rsplit('.', 1)[-1].lower() if '.' in self.filename else ''
        icon_map = {
            'txt': 'bi-file-text',
            'pdf': 'bi-file-pdf',
            'png': 'bi-file-image',
            'jpg': 'bi-file-image',
            'jpeg': 'bi-file-image',
            'gif': 'bi-file-image',
            'py': 'bi-file-code',
            'html': 'bi-file-code',
            'css': 'bi-file-code',
            'js': 'bi-file-code'
        }
        return icon_map.get(ext, 'bi-file')

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'filepath': self.filepath,
            'filetype': self.filetype,
            'filesize': self.filesize,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'owner_id': self.owner_id
        }

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
