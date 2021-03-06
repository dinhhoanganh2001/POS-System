from flask import Flask,render_template, url_for, redirect, request, flash, abort
import sqlite3
from flask_login._compat import unicode
import datetime
from forms import RegisterForm, LoginForm
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, UserMixin, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash




app = Flask(__name__) 
app.secret_key = ['832790179812']
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please login to access this page!'
login_manager.login_message_category = "warning"
db = sqlite3.connect('test.db',check_same_thread=False)
db.close()




class User(UserMixin):
    def __init__(self, user_id, username, email, password):
        self.user_id = unicode(user_id)
        self.email = email
        self.username = username
        self.password = generate_password_hash(password)
        self.authenticated = False

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    def is_active(self):
        return self.is_active()

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return self.authenticated

    def get_id(self):
        return self.user_id


@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('test.db')
    curs = conn.cursor()
    curs.execute("SELECT * from user where user_id= (?)", (user_id,))
    lu = curs.fetchone()
    if lu is None:
        return None
    else:
        return User(int(lu[0]), lu[1], lu[2], lu[3])


@app.route('/', methods = ["POST", "GET"])
def index():

    if request.method == "POST":
        number = request.form["quantity"]
        id = request.form["id"]


        return redirect(url_for("choose", number = number, id = id))

    else:
        conn = sqlite3.connect('test.db')
        curs = conn.cursor()
        curs = conn.execute("SELECT * FROM FOOD")
        food = curs.fetchall()

        curs = conn.execute("select * from CART where ID = (?)", (current_user.get_id(), ))
        bill = curs.fetchall()

        curs = conn.execute("select count(*) from CART where ID = (?)", (current_user.get_id(), ))
        number = curs.fetchone()

        total = 0
        for item in bill:
            total += item[2] * item[5]

        conn.close()
        return render_template("index.html", food = food, bill = bill, number = number, total = total)

@app.route('/choose/<number>/<id>/')
def choose(number, id):
    conn = sqlite3.connect('test.db')
    curs = conn.cursor()

    curs = conn.execute("select * from FOOD where ID = (?)", (id,))
    food = curs.fetchone()


    curs = conn.execute("select * from CART where ID = (?) and food_name = (?)", (current_user.get_id(), food[0]))
    data = curs.fetchone()
    if not data:
        curs = conn.execute("insert into CART(ID,food_name,amount,path,food_id,price)values(?,?,?,?,?,?)", (current_user.get_id(), food[0], number, food[3], food[5], food[1]))
        conn.commit()
        conn.close()
    else:
        curs = conn.execute("update CART set amount = (?) where ID = (?) and food_name = (?)", (data[2] + int(number), current_user.get_id(), food[0]))
        conn.commit()
        conn.close()
    return redirect("/")

@app.route('/remove/<id>', methods = ["GET", "POST"])
def remove(id):
    conn = sqlite3.connect('test.db')
    conn.execute("delete from CART where food_id = (?)", (id,))
    conn.commit()
    return redirect("/")

@app.route('/updatehistory/', methods = ["POST", "GET"])
@login_required
def updatehistory():
    id = current_user.get_id()
    con = sqlite3.connect("test.db")
    cur = con.cursor()
    cur.execute("select * from CART where id = (?)", (id,))
    data = cur.fetchall()

    total = 0
    for item in data:
        total += item[2] * item[5]

    cur.execute("insert into history(id_user, time, total)values(?,?,?)", (id, datetime.date.today() ,total))
    con.commit()

    cur.execute("select MAX(id) from history")
    max_his = cur.fetchone()

    for item in data:
        cur.execute("insert into history_detail(id,food,amount,id_user)values(?,?,?,?)",
                        (max_his[0], item[1], item[2], current_user.get_id()))
        con.commit()
    
    cur.execute("delete from CART where id = (?)", (id,))
    con.commit()
    con.close()
    return redirect('/')

@app.route('/history/', methods = ["POST", "GET"])
@login_required
def history():
    con = sqlite3.connect("test.db")
    cur = con.cursor()
    cur.execute("select * from history where id_user = (?)", (current_user.get_id(),))
    his = list(cur.fetchall())

    
    cur.execute("select * from history_detail where id_user = (?)", (current_user.get_id(), ))
    his_detail = list(cur.fetchall())
    return render_template("history.html", his = his, his_detail = his_detail)
    
    
    

@app.route('/removeall/')
def removeall():
    conn = sqlite3.connect('test.db')
    conn.execute("delete from CART")
    conn.commit()
    return redirect("/")

@app.route('/profile', methods = ["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        id = current_user.get_id()
        name = request.form["NAME"]
        age = request.form["AGE"]
        con = sqlite3.connect("test.db")
        cur = con.cursor()
        cur.execute("insert into PROFILE(id, name, age)values(?,?,?)",
                    (id, name, age))
        con.commit()
        con.close()
        return redirect(url_for('profile'))
    else:
        con = sqlite3.connect("test.db")
        cur = con.cursor()
        cur.execute("select * from PROFILE where id=?", (current_user.get_id(),))
        data = cur.fetchone()
        return render_template('profile.html',data=data)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = request.form['username']
        email = request.form['email_address']
        password = request.form['password1']
        con = sqlite3.connect("test.db")
        cur = con.cursor()
        cur.execute("select username from user where username=?", (username,))
        data1 = cur.fetchone()
        if data1:
            flash("Username are already exists", "danger")
            return redirect(url_for('register'))
        cur.execute("select email from user where email=?", (email,))
        data2 = cur.fetchone()
        if data2:
            flash("Email are already exists", "danger")
            return redirect(url_for('register'))
        else:
            cur.execute("insert into user(username,email,password)values(?,?,?)",
                        (username, email, password))
        con.commit()
        con.close()
        return redirect(url_for('login'))
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(f'{err_msg}', category='danger')
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        con = sqlite3.connect("test.db")
        cur = con.cursor()
        cur.execute("select * from user where username=?",
                    [form.username.data])
        data = cur.fetchall()
        if data:
            user = load_user(data[0][0])
            if form.username.data == user.username and user.verify_password(form.password.data):
                login_user(user)
                return redirect('/')
            else:
                flash(f'Username or Password mismatch. Please try again!', category='danger')
        else: 
            flash(f'Username or Password mismatch. Please try again!', category='danger')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("index"))
    

@app.route('/rice/', methods = ["GET", "POST"])
def rice():
    
    params = ["Rice"]
    conn = sqlite3.connect('test.db')
    curs = conn.cursor()
    curs = conn.execute("SELECT * FROM FOOD WHERE Type = (?)", params)
    food = curs.fetchall()
    curs = conn.execute("select * from CART where ID = (?)", (current_user.get_id(), ))
    bill = curs.fetchall()

    curs = conn.execute("select count(*) from CART where ID = (?)", (current_user.get_id(), ))
    number = curs.fetchone()
    conn.close()
    total = 0
    for item in bill:
        total += item[2] * item[5]
    return render_template("index.html", total = total,food = food, bill = bill, number = number)

@app.route('/chicken/', methods = ["GET", "POST"])
def chicken():
    
    params = ["Chicken"]
    conn = sqlite3.connect('test.db')
    curs = conn.cursor()
    curs = conn.execute("SELECT * FROM FOOD WHERE Type = (?)", params)
    food = curs.fetchall()
    curs = conn.execute("select * from CART where ID = (?)", (current_user.get_id(), ))
    bill = curs.fetchall()

    curs = conn.execute("select count(*) from CART where ID = (?)", (current_user.get_id(), ))
    number = curs.fetchone()
    conn.close()

    total = 0
    for item in bill:
        total += item[2] * item[5]    
    return render_template("index.html", total = total, food = food, bill = bill, number = number)

@app.route('/snack/', methods = ["GET", "POST"])
def snack():
    
    params = ["Snack"]
    conn = sqlite3.connect('test.db')
    curs = conn.cursor()
    curs = conn.execute("SELECT * FROM FOOD WHERE Type = (?)", params)
    food = curs.fetchall()

    curs = conn.execute("select * from CART where ID = (?)", (current_user.get_id(), ))
    bill = curs.fetchall()

    curs = conn.execute("select count(*) from CART where ID = (?)", (current_user.get_id(), ))
    number = curs.fetchone()
    conn.close()
    total = 0
    for item in bill:
        total += item[2] * item[5]
    return render_template("index.html", total = total, food = food, bill = bill, number = number)

@app.route('/drink/', methods = ["GET", "POST"])
def drink():
    
    params = ["Drink"]
    conn = sqlite3.connect('test.db')
    curs = conn.cursor()
    curs = conn.execute("SELECT * FROM FOOD WHERE Type = (?)", params)
    food = curs.fetchall()
    curs = conn.execute("select * from CART where ID = (?)", (current_user.get_id(), ))
    bill = curs.fetchall()

    curs = conn.execute("select count(*) from CART where ID = (?)", (current_user.get_id(), ))
    number = curs.fetchone()

    conn.close()
    total = 0
    for item in bill:
        total += item[2] * item[5]
    return render_template("index.html", total = total, food = food, bill = bill, number = number)



if __name__ == '__main__':
   app.run(debug = True)


#Set-ExecutionPolicy Unrestricted -Scope Process
#env\Scripts\activate