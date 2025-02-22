from flask import Flask, redirect, request, url_for, render_template
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient, rfc6749
import requests
import json
import os
from flask_pymongo import PyMongo
import ssl

app = Flask('HK Guide')
app.config['MONGO_URI'] = 'mongodb+srv://admin:andrewwong2012@partikle.eeys6xn.mongodb.net/HK_Guide_Project?retryWrites=true&w=majority&appName=Partikle&tls=true&tlsAllowInvalidCertificates=true'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app.config['SECRET_KEY'] = 'thisisasecretkey'
login_manager = LoginManager()
login_manager.init_app(app)

# Initialize PyMongo
mongo = PyMongo(app)

from db import get_db
from user import User, Pinpoint  # Import the User class

with open('creds/creds.json', 'r') as f:
    creds = json.load(f)
    GOOGLE_CLIENT_ID = creds['client_id']
    GOOGLE_CLIENT_SECRET = creds['client_secret']
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    
    def get_google_provider_cfg():
        return requests.get(GOOGLE_DISCOVERY_URL).json()

client = WebApplicationClient(GOOGLE_CLIENT_ID)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
def index():
    pinpoints = Pinpoint.getall()
    return render_template('index.html', authenticated=current_user.is_authenticated, user=current_user, pinpoints=pinpoints)

@app.route('/about')
def about():
    return render_template('about.html', authenticated=current_user.is_authenticated, user=current_user)

@app.route('/howto')
def howto():
    return render_template('howto.html', authenticated=current_user.is_authenticated, user=current_user)

@app.route('/test')
def testlogin():
    if current_user.is_authenticated:
            return (
                "<p>Hello, {}! You're logged in! Email: {}</p>"
                "<div><p>Google Profile Picture:</p>"
                '<img src="{}" alt="Google profile pic"></img></div>'
                '<a class="button" href="/logout">Logout</a>'.format(
                    current_user.name, current_user.email, current_user.profile_pic
                )
            )
    else:
        return '<a class="button" href="/login">Google Login</a>'

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    try:
        client.parse_request_body_response(json.dumps(token_response.json()))
    except rfc6749.errors.InvalidGrantError:
        return "Invalid grant error", 400
    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400
    # Create a user in your db with the information provided
    # by Google
    print(unique_id)
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)
    # Send user back to homepage
    return redirect(url_for("index"))

@app.route("/pinpoint/<id>")
def pinpoint(id):
    pinpoint = Pinpoint.get(id)
    if (id == "tai-o"):
        return render_template('Page 1.html', authenticated=current_user.is_authenticated, user=current_user)
    elif (id == "dragons-back"):
        return render_template('Page 2.html', authenticated=current_user.is_authenticated, user=current_user)
    elif (id == "history-museum"):
        return render_template('Page 3.html', authenticated=current_user.is_authenticated, user=current_user)
    elif (id == "tian-tan"):
            return render_template('Page 4.html', authenticated=current_user.is_authenticated, user=current_user)
    elif (id == "wong-tai-sin"):
            return render_template('Page 5.html', authenticated=current_user.is_authenticated, user=current_user)
    elif (id == "preface-hq"):
            return render_template('Page 6.html', authenticated=current_user.is_authenticated, user=current_user)

    return render_template('pinpoint.html', authenticated=current_user.is_authenticated, user=current_user, pinpoint=pinpoint)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

if __name__ == '__main__':
    app.run(debug=True, port=2000)
    