from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from functools import wraps
from datetime import date
app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'maintenance_management'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('index'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))    

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min = 1, max = 50)])
    email = StringField('Email', [validators.Length(min = 1, max = 50)])
    department = StringField('Department', [validators.Length(min = 1, max = 80)])
    designation = StringField('Designation', [validators.Length(min = 1, max = 50)])

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/userRegister',methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        department = form.department.data
        designation = form.designation.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO user(email, name, department, designation) VALUES(%s, %s, %s, %s)", (email, name, department, designation))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)  

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        email = request.form['email']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM user WHERE email = %s", [email])

        if result > 0:
            data = cur.fetchone()
            session['logged_in'] = True
            session['name'] = data['name']
            session['email'] = data['email']
            session['department'] = data['department']
            session['designation'] = data['designation']


            flash('You are now logged in', 'success')
            return redirect(url_for('dashboard'))
        else:
            error = 'Email not found'
            return render_template('login.html', error=error)

    return render_template('login.html')
    
# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    #result = cur.execute("SELECT * FROM articles")
    # Show articles only from the user logged in 
    result = cur.execute("SELECT * FROM complaint WHERE email = %s", [session['email']])

    complaints = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', complaints = complaints)
    else:
        msg = 'No Complaints Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection

class ComplaintForm(Form):
    roomno = StringField('Roomno', [validators.Length(min=1, max=200)])
    issue = TextAreaField('Issue', [validators.Length(min=1)])

# Add Complaint
@app.route('/add_complaint', methods=['GET', 'POST'])
@is_logged_in
def add_complaint():
    form = ComplaintForm(request.form)
    if request.method == 'POST' and form.validate():
        roomno = form.roomno.data
        issue = form.issue.data

        cur = mysql.connection.cursor()
        # Create Cursor
        # Execute
        cur.execute("INSERT INTO complaint(email, name,department, designation, roomno, issue, userStatus, mainStatus,date) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",(session['email'], session['name'],session['department'], session['designation'], roomno, issue, False, False,date.today()))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Complaint Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_complaint.html', form=form)


# Edit Article
@app.route('/edit_complaint/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_complaint(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM complaint WHERE id = %s", [id])

    complaint = cur.fetchone()
    cur.close()
    # Get form
    form = ComplaintForm(request.form)

    # Populate article form fields
    form.roomno.data = complaint['roomno']
    form.issue.data = complaint['issue']
    _id = complaint['id']

    if request.method == 'POST' and form.validate():
        roomno = request.form['roomno']
        issue = request.form['issue']

        # Create Cursor
        cur = mysql.connection.cursor()
        #app.logger.info(issue)
        # Execute
        cur.execute ("UPDATE complaint SET roomno=%s, issue=%s WHERE id=%s AND email = %s",(roomno, issue, _id,session['email']))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Complaint Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_complaint.html', form=form)

# Delete Article
@app.route('/delete_complaint/<string:id>', methods=['POST'])
@is_logged_in
def delete_complaint(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM complaint WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Complaint Deleted', 'success')

    return redirect(url_for('dashboard'))


#---------------------------------------------------------------
# Maintenance login
@app.route('/mainLogin', methods=['GET', 'POST'])
def mainLogin():
    if request.method == 'POST':
        # Get Form Fields
        name = request.form['name']
        password = request.form['password']
        # Create cursor

        # Get user by username
        if name == "admin" and password == "admin":
            session['logged_in'] = True
            session['name'] = "admin"
            flash('You are now logged in', 'success')
            return redirect(url_for('mainDashboard'))
        else:
            error = 'Name or password incorrect'
            return render_template('mainLogin.html', error=error)

    return render_template('mainLogin.html')

# Maintenance Dashboard
@app.route('/mainDashboard')
@is_logged_in
def mainDashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    #result = cur.execute("SELECT * FROM articles")
    # Show articles only from the user logged in 
    result = cur.execute("SELECT * FROM complaint")
    complaints = cur.fetchall()

    if result > 0:
        return render_template('mainDashboard.html', complaints = complaints)
    else:
        msg = 'No Complaints Found'
        return render_template('mainDashboard.html', msg=msg)  


@app.route('/checkboxMainToggleTrue/<string:id>',methods=['GET','POST'])
@is_logged_in
def checkboxMainToggleTrue(id):

    cur = mysql.connection.cursor()
    cur.execute ("UPDATE complaint SET mainStatus=%s,userStatus=%s WHERE id=%s",(True, True, id))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('mainDashboard'))

@app.route('/checkboxMainToggleFalse/<string:id>',methods=['GET','POST'])
@is_logged_in
def checkboxMainToggleFalse(id):

    cur = mysql.connection.cursor()
    cur.execute ("UPDATE complaint SET mainStatus=%s, userStatus=%s WHERE id=%s",(False, False, id))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('mainDashboard'))


if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)