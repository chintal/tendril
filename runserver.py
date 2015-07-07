"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""


from frontend.app import app, db
from frontend.startup.init_app import init_app

init_app(app, db)

if __name__ == '__main__':
    app.run(debug=True)
