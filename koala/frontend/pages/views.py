

from flask import render_template

from koala.frontend.app import app


# The Home page is accessible to anyone
@app.route('/')
def home_page():
    return render_template('pages/home_page.html')
