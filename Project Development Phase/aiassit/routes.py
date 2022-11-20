from flask import (
    Flask,
    render_template,
    redirect,
    flash,
    url_for,
    session,request,Response
)
from camera import Video
from datetime import timedelta
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.routing import BuildError


from flask_bcrypt import Bcrypt,generate_password_hash, check_password_hash

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

from app import create_app,db,login_manager,bcrypt
from models import User
from mail import send_email
from otpgen import genotp



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app = create_app()

@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)

@app.route("/", methods=("GET", "POST"), strict_slashes=False)
@app.route("/login/", methods=("GET", "POST"), strict_slashes=False)
def login():
    if request.method=='POST':
        uname = request.form.get('username')
        psw = request.form.get('password')

        try:
            user = User.query.filter_by(username=uname).first()
            if check_password_hash(user.pwd, psw):
                if user.confirmed==True:
                    login_user(user)
                    return render_template('home.html',uname=uname)
                else:
                    user = User.query.filter_by(username=uname).first()
                    otp=genotp()
                    send_email(user.email,str(otp))
                    session['res']=str(otp)
                    flash("Verify your Account to login!", "danger")
                    return render_template('enterotp.html')
                    
            else:
                flash("Invalid Username or password!", "danger")
        except Exception as e:
            flash(e, "danger")

    return render_template('login.html')



# Register route
@app.route("/register/", methods=("GET", "POST"), strict_slashes=False)
def signup():
    if request.method=='POST':
        try:
            email = request.form.get('email')
            pwd = request.form.get('password')
            username = request.form.get('username')
            
            user = User.query.filter_by(email=email).first()
            if user is None:
                newuser = User(
                username=username,
                email=email,
                pwd=bcrypt.generate_password_hash(pwd),
                confirmed=False
                )
                db.session.add(newuser)
                db.session.commit()
                flash(f"Account Succesfully created.Please Verify Your Account", "success")
                return render_template('login.html')
            else:
                flash(f"Account already Exists", "Warning")
                return redirect(url_for("signup"))

        except InvalidRequestError:
            db.session.rollback()
            flash(f"Something went wrong!", "danger")
        except IntegrityError:
            db.session.rollback()
            flash(f"User already exists!.", "warning")
        except DataError:
            db.session.rollback()
            flash(f"Invalid Entry", "warning")
        except InterfaceError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except DatabaseError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except BuildError:
            db.session.rollback()
            flash(f"An error occured !", "danger")
    return render_template('signup.html')

@app.route("/home/")
@login_required
def home():
    return render_template('index.html')
    
def gen(camera):
	while True:
		frame = camera.get_frame()
		yield(b'--frame\r\n'
			b'Content-Type: image/jpeg\r\n\r\n' + frame +
			b'\r\n\r\n')

@app.route("/verifyotp/",methods=("GET", "POST"), strict_slashes=False)
def confirmaccount():
    if request.method=='POST':
        email = request.form.get('email')
        otp=request.form.get('otp')
        if 'res' in session:
            r = session['res']
            session.pop('res',None)
            if r == otp:
                user = User.query.filter_by(email=email).first()
                #print(user.confirmed)
                user.confirmed = 1
                #print(user.confirmed)
                db.session.add(user)
                db.session.commit()
                flash(f"Your Account has verified Successfully! You can login now", "success")
                return redirect(url_for('login'))


@app.route('/video_feed')
@login_required
def video_feed():
	video = Video()
	return Response(gen(video), mimetype='multipart/x-mixed-replace; boundary = frame')



@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)
