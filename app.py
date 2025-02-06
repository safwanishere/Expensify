from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from helpers import login_required, apology, dashApology
import sqlite3

# configure flask application
app = Flask(__name__)

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure sqlite database



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response



@app.route("/")
def index():
    return render_template("index.html")




@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form.get("username")

            # if user does not enter username
            if username == "":
                return apology("Enter username")

            password = request.form.get("password")
            confirmedPassword = request.form.get("confirmedPassword")

            # if user does not enter password or confirmation
            if password == "" or confirmedPassword == "":
                return apology("Enter password and confirm it")

            # if password and confirmation are not the same
            if password != confirmedPassword:
                return apology("Your passwords do not match")

            # insert user into the users table in finance.db database
            dbcon = sqlite3.connect("database.db")
            cursor = dbcon.cursor()
            cursor.execute(f"INSERT INTO users (username, password) values ('{username}','{generate_password_hash(password)}');")
            cursor.close()
            dbcon.commit()

            # redirect user to login page
            return render_template("login.html")

        except ValueError:
            return apology("Username already exists")

    # User reached route via GET
    else:
        return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        dbcon = sqlite3.connect("database.db")
        cursor = dbcon.cursor()

        cursor.execute(
            f"SELECT * FROM users WHERE username = '{request.form.get('username')}';", 
        )
        rows = cursor.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0][2], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        cursor.close()
        dbcon.close()

        # Redirect user to home page
        return redirect("/dashboard")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
    

@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")



@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():

    user_id = session["user_id"]
    dbcon = sqlite3.connect("database.db")
    cursor = dbcon.cursor()

    cursor.execute(f"SELECT username FROM users WHERE user_id = {user_id};")
    username = cursor.fetchall()[0][0]

    cursor.execute(f"SELECT SUM(amount), date FROM transactions WHERE date(date) <= date('now') AND  date(date) >= date('now', '-1 month') AND type = 'income' AND user_id = {user_id} GROUP BY date ORDER BY date;")
    incomeRows = cursor.fetchall()
    incomeData = [row[0] for row in incomeRows]
    incomeLabels = [(row[1][8:] + "-" + row[1][5:7]) for row in incomeRows]

    cursor.execute(f"SELECT SUM(amount), date FROM transactions WHERE date(date) <= date('now') AND  date(date) >= date('now', '-1 month') AND type = 'expense' AND user_id = {user_id} GROUP BY date ORDER BY date;")
    expenseRows = cursor.fetchall()
    expenseData = [row[0] for row in expenseRows]
    expenseLabels = [(row[1][8:] + "-" + row[1][5:7]) for row in expenseRows]

    cursor.execute(f"SELECT SUM(amount), category FROM transactions WHERE date(date) <= date('now') AND date(date) >= date('now', '-1 month') AND type = 'expense' AND user_id = {user_id} GROUP BY category;")
    categoryRows = cursor.fetchall()
    categoryAmount = [row[0] for row in categoryRows]
    category = [row[1] for row in categoryRows]

    cursor.execute(f"SELECT SUM(amount), category FROM transactions WHERE date(date) <= date('now') AND date(date) >= date('now', '-1 month') AND type = 'income' AND user_id = {user_id} GROUP BY category;")
    incomeCategoryRows = cursor.fetchall()
    incomeCategoryAmount = [row[0] for row in incomeCategoryRows]
    incomeCategory = [row[1] for row in incomeCategoryRows]

    cursor.execute(f"SELECT category, COUNT(category) FROM transactions WHERE user_id = {user_id} GROUP BY category ORDER BY COUNT(category) DESC LIMIT 1;")
    try:
        mostUsedCategory = cursor.fetchall()[0][0]
    except IndexError:
        mostUsedCategory = "None"

    cursor.execute(f"SELECT count(*) FROM transactions WHERE user_id = {user_id};")
    totalTransactions = cursor.fetchall()[0][0]

    cursor.execute(f"SELECT account_id, COUNT(account_id) FROM transactions WHERE user_id = {user_id} GROUP BY account_id ORDER BY COUNT(account_id) DESC LIMIT 1;")
    try:
        accountId = cursor.fetchall()[0][0]
        cursor.execute(f"SELECT name FROM accounts WHERE account_id = {accountId} AND user_id = {user_id};")
        mostUsedAccount = cursor.fetchall()[0][0]
    except IndexError:
        mostUsedAccount = "None"

    cursor.close()
    dbcon.close()

    return render_template("dashboard.html", 
                           username=username, 
                           incomeLabels=incomeLabels, 
                           incomeData=incomeData, 
                           expenseData=expenseData,
                           expenseLabels=expenseLabels,
                           categoryAmount=categoryAmount,
                           category=category,
                           incomeCategoryAmount=incomeCategoryAmount,
                           incomeCategory=incomeCategory,
                           mostUsedCategory=mostUsedCategory,
                           totalTransactions=totalTransactions,
                           mostUsedAccount=mostUsedAccount)



@app.route("/transactions", methods=["GET", "POST"])
@login_required
def transactions():

    # user reached route via post
    if request.method == "POST":
        user_id = session["user_id"]

        account = request.form.get("account")
        if account == "" or not account:
            return dashApology("select an account")
        
        dbcon = sqlite3.connect("database.db")
        cursor = dbcon.cursor()
        cursor.execute(f"SELECT account_id FROM accounts WHERE name = '{account}' AND user_id = {user_id};")
        account_id = cursor.fetchall()[0][0]

        type = request.form.get("type")
        amount = request.form.get("amount")
        category = request.form.get("category")
        if not type or not amount or not category or amount == "":
            return dashApology("enter all values")
        
        try:
            if not isinstance(float(amount), float):
                return dashApology("enter valid amount")
            if float(amount) <= 0:
                return dashApology("enter positive amount")
        except ValueError:
            return dashApology("enter valid amount")

        cursor.execute(f"INSERT INTO transactions (user_id, account_id, type, amount, category) VALUES({user_id}, {account_id}, '{type}', {amount}, '{category}');")

        if type == "expense":
            cursor.execute(f"UPDATE accounts SET balance = balance - {amount} WHERE user_id = {user_id} AND name = '{account}';")
        elif type == "income":
            cursor.execute(f"UPDATE accounts SET balance = balance + {amount} WHERE user_id = {user_id} AND name = '{account}';")

        cursor.close()
        dbcon.commit()
        dbcon.close()

        return redirect("/transactions")

    else:
        user_id = session["user_id"]
        dbcon = sqlite3.connect("database.db")
        cursor = dbcon.cursor()

        cursor.execute(f"SELECT username FROM users WHERE user_id = {user_id};")
        username = cursor.fetchall()[0][0]

        cursor.execute(f"SELECT name, icon FROM accounts WHERE user_id = {user_id};")
        accounts = cursor.fetchall()

        cursor.execute(f"SELECT category, icon FROM categories WHERE user_id = {user_id};")
        categories = cursor.fetchall()

        cursor.execute(f"SELECT name, type, amount, category, date, time FROM transactions JOIN accounts ON transactions.account_id = accounts.account_id WHERE transactions.user_id = {user_id};")
        rows = cursor.fetchall()

        cursor.close()
        dbcon.close()

        return render_template("transactions.html", username=username, accounts=accounts, categories=categories, rows=rows)



@app.route("/accounts", methods=["GET", "POST"])
@login_required
def accounts():

    # user reached route via post
    if request.method == "POST":

        # handle name input field
        name = request.form.get("name")
        if name == "":
            return dashApology("enter account name")
        
        # handle balance input field
        balance = request.form.get("balance")
        if balance == "":
            return dashApology("enter balance")
        try:
            if not isinstance(float(balance), float):
                return dashApology("enter valid balance")
            if float(balance) <= 0:
                return dashApology("enter positive balance")
        except ValueError:
            return dashApology("enter valid balance")
        
        icon = request.form.get("icon")

        user_id = session["user_id"]
        
        dbcon = sqlite3.connect("database.db")
        cursor = dbcon.cursor()
        cursor.execute(f"INSERT INTO accounts (user_id, name, balance, icon) values ({user_id}, '{name}', {balance}, '{icon}');")
        cursor.close()
        dbcon.commit()
        dbcon.close()

        return redirect("/accounts")

    # user reached route via get or redirect
    else:
        user_id = session["user_id"]
        dbcon = sqlite3.connect("database.db")
        cursor = dbcon.cursor()

        cursor.execute(f"SELECT username, currency FROM users WHERE user_id = {user_id};")
        result = cursor.fetchall()[0]
        username = result[0]
        currency = result[1]

        cursor.execute(f"SELECT * FROM accounts WHERE user_id = {user_id};")
        rows = cursor.fetchall()

        cursor.close()
        dbcon.close()

        return render_template("accounts.html", username=username, currency=currency, rows=rows)



@app.route("/categories", methods=["GET", "POST"])
@login_required
def categories():

    # user reached route via post
    if request.method == "POST":

        # validate category field
        category = request.form.get("category")
        if category == "":
            return dashApology("enter category")

        # validate type field
        type = request.form.get("type")
        if not type:
            return dashApology("select type")
        
        # validate icon field
        icon = request.form.get("icon")
        if not icon:
            return dashApology("select icon")
        
        user_id = session["user_id"]
        
        dbcon = sqlite3.connect("database.db")
        cursor = dbcon.cursor()
        cursor.execute(f"INSERT INTO categories (category, type, icon, user_id) VALUES ('{category}', '{type}', '{icon}', '{user_id}');")
        cursor.close()    
        dbcon.commit()

        return redirect("/categories")

    # user reached route via get or redirect
    else:

        user_id = session["user_id"]

        dbcon = sqlite3.connect("database.db")
        cursor = dbcon.cursor()

        cursor.execute(f"SELECT username FROM users WHERE user_id = {user_id};")
        username = cursor.fetchall()[0][0]

        cursor.execute(f"SELECT * FROM categories WHERE user_id = {user_id};")
        rows = cursor.fetchall()

        cursor.close()    
        dbcon.close()

        return render_template("categories.html", username=username, rows=rows)



@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():

    # user reached route via post
    if request.method == "POST":

        email = request.form.get("email")
        currency = request.form.get("currency")
        username = request.form.get("username")
        user_id = session["user_id"]
        
        dbcon = sqlite3.connect("database.db")
        cursor = dbcon.cursor()
        if email and email != "":
            cursor.execute(f"UPDATE users SET email = '{email}' WHERE user_id = {user_id};")
        if currency and currency != "":
            cursor.execute(f"UPDATE users SET currency = '{currency}' WHERE user_id = {user_id};")
        if username and username != "":
            cursor.execute(f"UPDATE users SET username = '{username}' WHERE user_id = {user_id};")
        cursor.close()
        dbcon.commit()
        dbcon.close()

        if (not email or email == "") and (not currency or currency == "") and (not username or username == ""):
            return dashApology("enter details to change")

        return redirect("/dashboard")


    # user reached route via get or redirect
    else:
        user_id = session["user_id"]

        dbcon = sqlite3.connect("database.db")
        cursor = dbcon.cursor()

        cursor.execute(f"SELECT username FROM users WHERE user_id = {user_id};")
        username = cursor.fetchall()[0][0]

        cursor.close()    
        dbcon.close()

        currencies = (	("AFN", "Afghani"),
            ("DZD", "Algerian Dinar"),
            ("ARS", "Argentine Peso"),
            ("AMD", "Armenian Dram"),
            ("AWG", "Aruban Guilder"),
            ("AUD", "Australian Dollar"),
            ("AZN", "Azerbaijanian Manat"),
            ("BSD", "Bahamian Dollar"),
            ("BHD", "Bahraini Dinar"),
            ("THB", "Baht"),
            ("PAB", "Balboa"),
            ("BBD", "Barbados Dollar"),
            ("BYR", "Belarussian Ruble"),
            ("BZD", "Belize Dollar"),
            ("BMD", "Bermudian Dollar"),
            ("VEF", "Bolivar Fuerte"),
            ("BOB", "Boliviano"),
            ("BRL", "Brazilian Real"),
            ("BND", "Brunei Dollar"),
            ("BGN", "Bulgarian Lev"),
            ("BIF", "Burundi Franc"),
            ("CAD", "Canadian Dollar"),
            ("CVE", "Cape Verde Escudo"),
            ("KYD", "Cayman Islands Dollar"),
            ("GHS", "Cedi"),
            ("CLP", "Chilean Peso"),
            ("COP", "Colombian Peso"),
            ("KMF", "Comoro Franc"),
            ("CDF", "Congolese Franc"),
            ("BAM", "Convertible Mark"),
            ("NIO", "Cordoba Oro"),
            ("CRC", "Costa Rican Colon"),
            ("HRK", "Croatian Kuna"),
            ("CUP", "Cuban Peso"),
            ("CZK", "Czech Koruna"),
            ("GMD", "Dalasi"),
            ("DKK", "Danish Krone"),
            ("MKD", "Denar"),
            ("DJF", "Djibouti Franc"),
            ("STD", "Dobra"),
            ("DOP", "Dominican Peso"),
            ("VND", "Dong"),
            ("XCD", "East Caribbean Dollar"),
            ("EGP", "Egyptian Pound"),
            ("SVC", "El Salvador Colon"),
            ("ETB", "Ethiopian Birr"),
            ("EUR", "Euro"),
            ("FKP", "Falkland Islands Pound"),
            ("FJD", "Fiji Dollar"),
            ("HUF", "Forint"),
            ("GIP", "Gibraltar Pound"),
            ("XAU", "Gold"),
            ("HTG", "Gourde"),
            ("PYG", "Guarani"),
            ("GNF", "Guinea Franc"),
            ("GYD", "Guyana Dollar"),
            ("HKD", "Hong Kong Dollar"),
            ("UAH", "Hryvnia"),
            ("ISK", "Iceland Krona"),
            ("INR", "Indian Rupee"),
            ("IRR", "Iranian Rial"),
            ("IQD", "Iraqi Dinar"),
            ("JMD", "Jamaican Dollar"),
            ("JOD", "Jordanian Dinar"),
            ("KES", "Kenyan Shilling"),
            ("PGK", "Kina"),
            ("LAK", "Kip"),
            ("KWD", "Kuwaiti Dinar"),
            ("MWK", "Kwacha"),
            ("AOA", "Kwanza"),
            ("MMK", "Kyat"),
            ("GEL", "Lari"),
            ("LVL", "Latvian Lats"),
            ("LBP", "Lebanese Pound"),
            ("ALL", "Lek"),
            ("HNL", "Lempira"),
            ("SLL", "Leone"),
            ("RON", "Leu"),
            ("LRD", "Liberian Dollar"),
            ("LYD", "Libyan Dinar"),
            ("SZL", "Lilangeni"),
            ("LTL", "Lithuanian Litas"),
            ("LSL", "Loti"),
            ("MGA", "Malagasy Ariary"),
            ("MYR", "Malaysian Ringgit"),
            ("MUR", "Mauritius Rupee"),
            ("MZN", "Metical"),
            ("MXN", "Mexican Peso"),
            ("MDL", "Moldovan Leu"),
            ("MAD", "Moroccan Dirham"),
            ("BOV", "Mvdol"),
            ("NGN", "Naira"),
            ("ERN", "Nakfa"),
            ("NAD", "Namibia Dollar"),
            ("NPR", "Nepalese Rupee"),
            ("ANG", "Netherlands Antillean Guilder"),
            ("ILS", "New Israeli Sheqel"),
            ("TMT", "New Manat"),
            ("TWD", "New Taiwan Dollar"),
            ("NZD", "New Zealand Dollar"),
            ("BTN", "Ngultrum"),
            ("KPW", "North Korean Won"),
            ("NOK", "Norwegian Krone"),
            ("PEN", "Nuevo Sol"),
            ("MRO", "Ouguiya"),
            ("PKR", "Pakistan Rupee"),
            ("XPD", "Palladium"),
            ("MOP", "Pataca"),
            ("TOP", "Pa’anga"),
            ("CUC", "Peso Convertible"),
            ("UYU", "Peso Uruguayo"),
            ("PHP", "Philippine Peso"),
            ("XPT", "Platinum"),
            ("GBP", "Pound Sterling"),
            ("BWP", "Pula"),
            ("QAR", "Qatari Rial"),
            ("GTQ", "Quetzal"),
            ("ZAR", "Rand"),
            ("OMR", "Rial Omani"),
            ("KHR", "Riel"),
            ("MVR", "Rufiyaa"),
            ("IDR", "Rupiah"),
            ("RUB", "Russian Ruble"),
            ("RWF", "Rwanda Franc"),
            ("SHP", "Saint Helena Pound"),
            ("SAR", "Saudi Riyal"),
            ("RSD", "Serbian Dinar"),
            ("SCR", "Seychelles Rupee"),
            ("XAG", "Silver"),
            ("SGD", "Singapore Dollar"),
            ("SBD", "Solomon Islands Dollar"),
            ("KGS", "Som"),
            ("SOS", "Somali Shilling"),
            ("TJS", "Somoni"),
            ("ZAR", "South African Rand"),
            ("LKR", "Sri Lanka Rupee"),
            ("XSU", "Sucre"),
            ("SDG", "Sudanese Pound"),
            ("SRD", "Surinam Dollar"),
            ("SEK", "Swedish Krona"),
            ("CHF", "Swiss Franc"),
            ("SYP", "Syrian Pound"),
            ("BDT", "Taka"),
            ("WST", "Tala"),
            ("TZS", "Tanzanian Shilling"),
            ("KZT", "Tenge"),
            ("TTD", "Trinidad and Tobago Dollar"),
            ("MNT", "Tugrik"),
            ("TND", "Tunisian Dinar"),
            ("TRY", "Turkish Lira"),
            ("AED", "UAE Dirham"),
            ("USD", "US Dollar"),
            ("UGX", "Uganda Shilling"),
            ("COU", "Unidad de Valor Real"),
            ("CLF", "Unidades de fomento"),
            ("UYI", "Uruguay Peso en Unidades Indexadas (URUIURUI)"),
            ("UZS", "Uzbekistan Sum"),
            ("VUV", "Vatu"),
            ("KRW", "Won"),
            ("YER", "Yemeni Rial"),
            ("JPY", "Yen"),
            ("CNY", "Yuan Renminbi"),
            ("ZMK", "Zambian Kwacha"),
            ("ZWL", "Zimbabwe Dollar"),
            ("PLN", "Zloty"),
        )

        return render_template("settings.html", username=username, currencies=currencies)