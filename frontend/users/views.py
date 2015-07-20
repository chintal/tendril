
from flask import redirect, render_template
from flask import request, url_for
from flask_user import current_user, login_required
from flask_user.forms import ChangePasswordForm
from flask_user.forms import ChangeUsernameForm

from frontend.app import app, db
from frontend.users.forms import UserProfileForm


@app.route('/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile_page():
    # Initialize form
    form = UserProfileForm(request.form, current_user)
    change_username_form = ChangeUsernameForm()
    change_password_form = ChangePasswordForm()
    # Process valid POST
    if request.method == 'POST' and form.validate():

        # Copy form fields to user_profile fields
        form.populate_obj(current_user)

        # Save user_profile
        db.session.commit()

        # Redirect to home page
        return redirect(url_for('home_page'))

    # Process GET or invalid POST
    return render_template('users/user_profile_page.html',
                           form=form,
                           change_username_form=change_username_form,
                           change_password_form=change_password_form,
                           current_user=current_user,
                           pagetitle="User Profile"
                           )
