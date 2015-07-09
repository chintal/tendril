

import os

APP_NAME = "Koala"

# Flask settings
from utils.config import SECRET_KEY

# SQLAlchemy settings
from utils.config import INSTANCE_ROOT
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(INSTANCE_ROOT, 'db', 'auth.db')

# Flask-Mail settings
from utils.config import MAIL_DEFAULT_SENDER
from utils.config import MAIL_PASSWORD
from utils.config import MAIL_PORT
from utils.config import MAIL_SERVER
from utils.config import MAIL_USE_SSL
from utils.config import MAIL_USE_TLS
from utils.config import MAIL_USERNAME

# Disable E-mail
USER_ENABLE_EMAIL                 = True
USER_ENABLE_LOGIN_WITHOUT_CONFIRM = True
USER_ENABLE_CONFIRM_EMAIL        = False
USER_SEND_USERNAME_CHANGED_EMAIL = False
USER_SEND_PASSWORD_CHANGED_EMAIL = False
USER_SEND_REGISTERED_EMAIL       = False
USER_ENABLE_FORGOT_PASSWORD      = False
USER_ENABLE_MULTIPLE_EMAILS      = False
USER_REQUIRE_INVITATION          = False

from utils.config import ADMIN_EMAIL
ADMINS = [ADMIN_EMAIL]

# Application settings
APP_SYSTEM_ERROR_SUBJECT_LINE = APP_NAME + " system error"

# Flask settings
CSRF_ENABLED = True

# Flask-User settings
USER_APP_NAME                           = APP_NAME
USER_LOGIN_TEMPLATE                     = 'flask_user/login_or_register.html'
USER_REGISTER_TEMPLATE                  = 'flask_user/login_or_register.html'
USER_AFTER_CHANGE_PASSWORD_ENDPOINT     = 'user.profile'
USER_AFTER_CHANGE_USERNAME_ENDPOINT     = 'user.profile'
