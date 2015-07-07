from __future__ import print_function
import datetime

from frontend.app import app, db
from frontend.startup.init_app import init_app
from frontend.users.models import User, UserAuth, Role


def reset_db(app, db):
    """
    Delete all tables; Create all tables; Populate roles and users.
    """

    # Drop all tables
    print('Dropping all tables')
    db.drop_all()

    # Create all tables
    print('Creating all tables')
    db.create_all()

    # Adding roles
    print('Adding roles')

    admin_role = Role(name='admin')
    db.session.add(admin_role)

    exec_role = Role(name='exec')
    db.session.add(exec_role)

    internal_role = Role(name='internal')
    db.session.add(internal_role)

    # Add users
    print('Adding users')

    from utils.config import ADMIN_USERNAME
    from utils.config import ADMIN_FULLNAME
    from utils.config import ADMIN_EMAIL
    from utils.config import ADMIN_PASSWORD

    user = add_user(app, db, ADMIN_USERNAME, ADMIN_FULLNAME, ADMIN_EMAIL, ADMIN_PASSWORD)
    user.roles.append(admin_role)
    user.roles.append(exec_role)
    user.roles.append(internal_role)
    db.session.commit()


def add_user(app, db, username, full_name, email, password):
    """
    Create UserAuth and User records.
    """
    user_auth = UserAuth(username=username, password=app.user_manager.hash_password(password))
    user = User(
        active=True,
        full_name=full_name,
        email=email,
        confirmed_at=datetime.datetime.now(),
        user_auth=user_auth
    )
    db.session.add(user_auth)
    db.session.add(user)
    return user


# Initialize the app and reset the database
if __name__ == "__main__":
    init_app(app, db)
    reset_db(app, db)
