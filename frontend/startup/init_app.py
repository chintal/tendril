

import logging
from logging.handlers import SMTPHandler
from flask_mail import Mail
from flask_user import UserManager, SQLAlchemyAdapter


def init_app(app, db):
    """
    Initialize Flask applicaton
    """
    # Initialize app config settings
    app.config.from_object('frontend.startup.settings')
    if app.testing:
        app.config['WTF_CSRF_ENABLED'] = False              # Disable CSRF checks while testing

    # Initialize Assets
    from frontend.startup import assets

    # Setup Flask-Mail
    mail = Mail(app)

    # Setup an error-logger to send emails to app.config.ADMINS
    init_error_logger_with_email_handler(app)

    # Setup Flask-User to handle user account related forms
    from frontend.users.models import UserAuth, User
    from frontend.users.forms import MyRegisterForm
    from frontend.users.views import user_profile_page
    db_adapter = SQLAlchemyAdapter(db, User,
                                   UserAuthClass=UserAuth)
    user_manager = UserManager(db_adapter, app,
                               register_form=MyRegisterForm,
                               user_profile_view_function=user_profile_page,
                               )

    # Load all models.py files to register db.Models with SQLAlchemy
    from frontend.users import models

    # Load all views.py files to register @app.routes() with Flask
    from frontend.pages import views
    from frontend.users import views

    # Register blueprints
    from frontend.blueprints.doc import doc
    app.register_blueprint(doc, url_prefix='/doc')

    return app


def init_error_logger_with_email_handler(app):
    """
    Initialize a logger to send emails on error-level messages.
    Unhandled exceptions will now send an email message to app.config.ADMINS.
    """
    if app.debug: return                        # Do not send error emails while developing

    # Retrieve email settings from app.config
    host      = app.config['MAIL_SERVER']
    port      = app.config['MAIL_PORT']
    from_addr = app.config['MAIL_DEFAULT_SENDER']
    username  = app.config['MAIL_USERNAME']
    password  = app.config['MAIL_PASSWORD']
    secure = () if app.config.get('MAIL_USE_TLS') else None

    # Retrieve app settings from app.config
    to_addr_list = app.config['ADMINS']
    subject = app.config.get('APP_SYSTEM_ERROR_SUBJECT_LINE', 'System Error')

    # Setup an SMTP mail handler for error-level messages
    mail_handler = SMTPHandler(
        mailhost=(host, port),                  # Mail host and port
        fromaddr=from_addr,                     # From address
        toaddrs=to_addr_list,                   # To address
        subject=subject,                        # Subject line
        credentials=(username, password),       # Credentials
        secure=secure,
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

    # Log errors using: app.logger.error('Some error message')
