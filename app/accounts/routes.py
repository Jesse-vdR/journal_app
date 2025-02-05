from flask import render_template
from flask_login import login_required, current_user
from app.accounts import bp

@bp.route('/')
@login_required
def index():
    # Get user's storage info
    storage_used_mb = round(current_user.storage_used / (1024 * 1024), 2)
    storage_limit_mb = round(current_user.storage_limit / (1024 * 1024), 2)
    storage_percent = round((current_user.storage_used / current_user.storage_limit) * 100, 1) if current_user.storage_limit > 0 else 0
    
    return render_template('accounts/index.html',
                         user=current_user,
                         storage_used_mb=storage_used_mb,
                         storage_limit_mb=storage_limit_mb,
                         storage_percent=storage_percent)
