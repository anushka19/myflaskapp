from flask import Flask
from flask import render_template, flash, redirect, url_for, session, logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from flask import request
from functools import wraps

app = Flask(__name__)  # placeholder for current module

# config Mysql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)


# Articles = Articles()  # here articles is equal to the articles function in data.py

# creating route for home,index etc


@app.route('/')
def index():
    # return 'INDEX'  # we usually return a template not a string
    return render_template('home.html')

# about


@app.route('/about')
def about():
    return render_template('about.html')

# Articles


@app.route('/articles')
def articles():
    # here Articles is the data from above from fuc er getting
    # return render_template('articles.html', articles=Articles)
    # create cursor
    cur = mysql.connection.cursor()

    # get articles
    result = cur.execute("SELECT * from articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)

    # close Connection
    cur.close()


# Single article


@app.route('/article/<string:id>/')
def article(id):
    # create cursor
    cur = mysql.connection.cursor()

    # get articles
    result = cur.execute("SELECT * from articles WHERE id=%s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)

# Register Form class


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Paswswords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# User Register


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute(
            "INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)", (name, email, username, password))  # these variables are the one passed in if statment
        # we are using string replacements so percent s sign where it will get replaced

        # Commit To DB
        mysql.connection.commit()

        # Close Connection
        cur.close()

        # flash message after we register and its a successful message.After that we redirect
        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User Login

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form fields
        # did not used wt forms like registeration
        username = request.form['username']
        password_candidate = request.form['password']

        # create cursor
        cur = mysql.connection.cursor()

        # get user by username
        # username should be equal to the one we pass
        result = cur.execute(
            "SELECT * FROM users WHERE username= %s", [username])

        if result > 0:
            # Get the stored hash
            # if select query is true then it will fetch it and if it has many with same usernamer it will take first one
            data = cur.fetchone()
            password = data['password']  # pass mysql config for dict

            # compare teh password
            if sha256_crypt.verify(password_candidate, password):
                # app.logger.info('PASSWORD MATCHED')  # to log stuff to console
                # Passed
                session['logged_in'] = True
                # its equal to username variable that from form
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)

            # close Conncetion
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


# Check if user is logged in


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, Please Login', 'danger')
            return redirect(url_for('login'))
    return wrap


# Logout


@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# dashboard


@app.route('/dashboard')
@is_logged_in
def dashboard():
    # create cursor
    cur = mysql.connection.cursor()

    # get articles
    result = cur.execute("SELECT * from articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)

    # close Connection
    cur.close()

# Article Form class


class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article


@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # create cursor
        cur = mysql.connection.cursor()

        # execute
        # for in depth - you could get the user from username and put the real name as author
        cur.execute("INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)",
                    (title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        # close connection
        cur.close()

        flash('Article created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

# Edit Article


@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # get the article by the id
    result = cur.execute("SELECT * FROM articles WHERE id=%s", [id])

    article = cur.fetchone()

    # get form
    form = ArticleForm(request.form)

    # populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']  # pass db col name

# after comparing then validating sending the post request
    if request.method == 'POST' and form.validate():
        # Get form fields
        # did not used wt forms like registeration but here similar to user login
        title = request.form['title']
        body = request.form['body']
        #name = form.name.data

        # create cursor
        cur = mysql.connection.cursor()

        # execute
        # for in depth - you could get the user from username and put the real name as author
        cur.execute(
            "UPDATE articles SET title=%s,body=%s WHERE id=%s", (title, body, id))

        # Commit to DB
        mysql.connection.commit()

        # close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


# Delete Article
# here get method should not able to do anything here and post is always in brackets and methods is plural
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create Cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id= %s", [id])

    # Commit to DB
    mysql.connection.commit()

    # close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))


if __name__ == '__main__':  # the script that will be executed is that same
    # As we cannot restart every moment So we keep it in debug mode
    app.secret_key = 'secret123'
    app.run(debug=True)
