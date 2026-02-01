"""
Authentication Routes
Login, Register, Logout functionality
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from models.database import db

auth_bp = Blueprint('auth', __name__)

# ============================================================================
# LOGIN ROUTES
# ============================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    # POST - Handle login
    data = request.form
    username_or_email = data.get('username', '').strip()
    password = data.get('password', '')
    remember = data.get('remember', False)
    
    # Validate input
    if not username_or_email or not password:
        flash('Please enter both username/email and password', 'danger')
        return render_template('auth/login.html')
    
    # Authenticate user
    user = User.authenticate(username_or_email, password)
    
    if user:
        login_user(user, remember=remember)
        
        # Get next page or default to dashboard
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
        
        flash(f'Welcome back, {user.full_name or user.username}!', 'success')
        return redirect(next_page)
    else:
        flash('Invalid username/email or password', 'danger')
        return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page and handler"""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    # POST - Handle registration
    data = request.form
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    full_name = data.get('full_name', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    
    # Validate input
    if not username or not email or not password:
        flash('Please fill in all required fields', 'danger')
        return render_template('auth/register.html')
    
    if password != confirm_password:
        flash('Passwords do not match', 'danger')
        return render_template('auth/register.html')
    
    # Create user
    user, error = User.create_user(
        username=username,
        email=email,
        password=password,
        full_name=full_name or username
    )
    
    if error:
        flash(error, 'danger')
        return render_template('auth/register.html')
    
    # Log in the new user
    login_user(user)
    flash(f'Account created successfully! Welcome, {user.full_name}!', 'success')
    return redirect(url_for('index'))


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('auth.login'))


# ============================================================================
# API ENDPOINTS (for AJAX requests)
# ============================================================================

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for login (AJAX)"""
    if current_user.is_authenticated:
        return jsonify({
            'success': True,
            'message': 'Already logged in',
            'redirect': url_for('index')
        })
    
    data = request.get_json()
    username_or_email = data.get('username', '').strip()
    password = data.get('password', '')
    remember = data.get('remember', False)
    
    if not username_or_email or not password:
        return jsonify({
            'success': False,
            'error': 'Please enter both username/email and password'
        }), 400
    
    user = User.authenticate(username_or_email, password)
    
    if user:
        login_user(user, remember=remember)
        next_page = request.args.get('next', url_for('index'))
        
        return jsonify({
            'success': True,
            'message': f'Welcome back, {user.full_name or user.username}!',
            'redirect': next_page,
            'user': user.to_dict_public()
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid username/email or password'
        }), 401


@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    """API endpoint for registration (AJAX)"""
    if current_user.is_authenticated:
        return jsonify({
            'success': True,
            'message': 'Already logged in',
            'redirect': url_for('index')
        })
    
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    full_name = data.get('full_name', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    
    if not username or not email or not password:
        return jsonify({
            'success': False,
            'error': 'Please fill in all required fields'
        }), 400
    
    if password != confirm_password:
        return jsonify({
            'success': False,
            'error': 'Passwords do not match'
        }), 400
    
    user, error = User.create_user(
        username=username,
        email=email,
        password=password,
        full_name=full_name or username
    )
    
    if error:
        return jsonify({
            'success': False,
            'error': error
        }), 400
    
    login_user(user)
    
    return jsonify({
        'success': True,
        'message': f'Account created successfully! Welcome, {user.full_name}!',
        'redirect': url_for('index'),
        'user': user.to_dict_public()
    })


@auth_bp.route('/api/check-username', methods=['POST'])
def check_username():
    """Check if username is available"""
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'available': False, 'message': 'Username required'})
    
    if len(username) < 3:
        return jsonify({'available': False, 'message': 'Too short (min 3 characters)'})
    
    exists = User.query.filter_by(username=username).first()
    
    if exists:
        return jsonify({'available': False, 'message': 'Username already taken'})
    else:
        return jsonify({'available': True, 'message': 'Username available'})


@auth_bp.route('/api/check-email', methods=['POST'])
def check_email():
    """Check if email is available"""
    data = request.get_json()
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({'available': False, 'message': 'Email required'})
    
    if '@' not in email:
        return jsonify({'available': False, 'message': 'Invalid email format'})
    
    exists = User.query.filter_by(email=email).first()
    
    if exists:
        return jsonify({'available': False, 'message': 'Email already registered'})
    else:
        return jsonify({'available': True, 'message': 'Email available'})


# ============================================================================
# PROFILE MANAGEMENT
# ============================================================================

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    data = request.get_json()
    
    # Update allowed fields
    if 'full_name' in data:
        current_user.full_name = data['full_name'].strip()
    
    if 'email' in data:
        new_email = data['email'].strip()
        # Check if email is already taken by another user
        existing = User.query.filter(
            User.email == new_email,
            User.id != current_user.id
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'error': 'Email already in use'
            }), 400
        
        current_user.email = new_email
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/api/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    data = request.get_json()
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    # Validate current password
    if not current_user.check_password(current_password):
        return jsonify({
            'success': False,
            'error': 'Current password is incorrect'
        }), 400
    
    # Validate new password
    if len(new_password) < 6:
        return jsonify({
            'success': False,
            'error': 'New password must be at least 6 characters'
        }), 400
    
    if new_password != confirm_password:
        return jsonify({
            'success': False,
            'error': 'Passwords do not match'
        }), 400
    
    # Update password
    current_user.set_password(new_password)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Password changed successfully'
    })