import os
from flask import Flask, jsonify, render_template, redirect, request, send_file
import shutil
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user,login_required,current_user, logout_user
import random, string
import bcrypt
import contextlib, io
import subprocess

def get_hashed_password(plain_text_password):
    # Hash a password for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    return bcrypt.hashpw(plain_text_password.encode(), bcrypt.gensalt())

def check_password(plain_text_password, hashed_password):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(plain_text_password, hashed_password)

def getRandomString(length):
    return ''.join(random.choices(string.ascii_letters+string.digits,k=length))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///users.db'
app.config["SECRET_KEY"] = "ediwnfiuew"
loginManager = LoginManager(app)

db = SQLAlchemy(app)

class File:
    def __init__(self,filename):
        self.filename = filename
        self.size = os.path.getsize(filename)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30),unique=True)
    email = db.Column(db.String(30),unique=True)
    password = db.Column(db.String(1200))
    state = db.Column(db.String(30))


@app.route("/")
def index():
    return render_template("index.html")

@loginManager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/account')
@login_required
def me():
    files = [File(x) for x in os.listdir()]
    return render_template('dashboard.html',user=current_user,files=files,enumerate=enumerate)

@app.route("/dockerlang.communicate")
def dockerlang():
    user = User.query.filter_by(username=request.headers["username"]).first()
    container_name = request.headers["container"]
    cmd = request.headers["cmd"]
    stdout = io.StringIO()
    if check_password(request.headers["password"].encode(),user.password):
      with contextlib.redirect_stdout(stdout):
        output = subprocess.Popen(["docker" ,"exec", "-it", f"{secure_filename(user.username)}-{container_name}", *cmd.split(" ")).communicate()[0].decode()

      return jsonify({
            "result":output
        })
    else:
        return jsonify({
            "result":"401 Unauthorized, Maybe Password doesn't match?"
        })


@app.route("/dockerlang.up")
def dockerlang_upload():
    user = User.query.filter_by(username=request.headers["username"]).first()
    container_name = request.headers["container"]
    cmd = request.files["main"]
    stdout = io.StringIO()
    if check_password(request.headers["password"],user.password):
        cmd.save(secure_filename(cmd.filename))
        with contextlib.redirect_stdout(stdout):
            os.system(f"docker cp {secure_filename(cmd.filename)} {container_name}:/{cmd.filename} ")
        return jsonify({
            "result":stdout.read()
        })
    else:
        return jsonify({
            "result":"401 Unauthorized, Maybe Password doesn't match?"
        })


@app.route("/dockerlang.init")
def dockerlang_init():
    user = User.query.filter_by(username=request.headers["username"]).first()
    container_image = request.headers["container-img"]
    container_name = request.headers["container-name"]
    container_entry = request.headers["container-entry-cmd"]
    stdout = io.StringIO()
    os.mkdir(secure_filename(user.username))
    with open(f'{secure_filename(user.username)}/Dockerfile',"W") as f:
        f.write(
f"""
FROM {container_image}

RUN {container_entry}

ENTRYPOINT sleep infinity;
"""
        )
    if check_password(request.headers["password"],user.password):
        with contextlib.redirect_stdout(stdout):
            output = subprocess.Popen(["docker" ,"build", "-t", f"{secure_filename(user.username)}-{container_name}", f"{secure_filename(user.username)}"],stdout=subprocess.PIPE).communicate()[0].decode()
            shutil.rmtree(secure_filename(user.username))
        return jsonify({
            "result":output
        })
    else:
        return jsonify({
            "result":"401 Unauthorized, Maybe Password doesn't match?"
        })

@app.route("/dockerlang.down")
def dockerlang_download():
    user = User.query.filter_by(username=request.headers["username"]).first()
    container_name = request.headers["container"]
    cmd = request.headers["filename"]
    stdout = io.StringIO()
    if check_password(request.headers["password"],user.password):
        with contextlib.redirect_stdout(stdout):
            os.system(f"docker cp {container_name}:/{cmd} {secure_filename(cmd)}  ")
        return send_file(secure_filename(cmd))
    else:
        return jsonify({
            "result":"401 Unauthorized, Maybe Password doesn't match?"
        })

@app.route("/register",methods=["GET","POST"])
def regist():
  if request.method == "GET":
    return render_template("register.html")
  else:
    emailad = request.form.get("email")
    username  = request.form.get("username")
    passwd = request.form.get("passwd")
    state = getRandomString(10)
    user = User(username=username, password=get_hashed_password(passwd),state=state)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect("/account")

@app.route('/login',methods=['POST','GET'])
@app.route('/account/login',methods=['POST','GET'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    else:
        user = User.query.filter_by(username=request.form.get('username')).first()
        if check_password(request.form.get('passwd'),user.password):
            login_user(user)
            return redirect('/account')
        else:
            return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)
