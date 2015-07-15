

from flask import render_template
from flask_user import login_required, roles_required

from frontend.app import app


# The Home page is accessible to anyone
@app.route('/')
def home_page():
    return render_template('pages/home_page.html')


# The Member page is accessible to authenticated users (users that have logged in)
@app.route('/member')
@login_required             # Limits access to authenticated users
def member_page():
    return render_template('pages/member_page.html')


# The Admin page is accessible to users with the 'admin' role
@app.route('/admin')
@roles_required('admin')    # Limits access to users with the 'admin' role
def admin_page():
    return render_template('pages/admin_page.html')
