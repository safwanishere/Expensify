# Expensify
#### Video Demo:  https://youtu.be/LURBgujFOQw
#### Description:

Expensify is a personal finance tracking web application made using the following tech stack:

Frontend - HTML, CSS, JavaScript, Chart.js
Backend - Python, Flask, Jinja, sqlite3
Database - SQL
Design - Figma

##### User Flow 

Expensify allows users to register and create an account and then login using their credentials, it handles all edge cases and invalid user input to show error messages.

Once logged in, users are greeted with an interface that has a header and a side navigation bar to view different pages including a dashboard, accounts page, transactions page, categories page and a settings page.

In the accounts page, users can add a new account by inputing the account name, available balance and select an icon for the account. The already added accounts of the user will be visible on the page as well.
The categories page allows users to create categories to classify their transactions, this is also done through a form and then the categories are displayed using a table.
The transactions page shows all of users transactions from all accounts and under all categories, they can also add new transactions from the same page inputting the account through which the transaction happened, the type of transaction, the amount and the category in which the transaction falls. The time and date is inputted to the database automatically by the application.
The settings page enables users to change their username and also the currency. They can also add an email to their account.

##### Design Choices

The design of the website is very modern. For the landing, login and registration pages I used a gradient background with vibrant color choices in the elements such as buttons. The font I decided to go with was "Onest" which fits right in with the theme of the whole project.
The dashboard pages after logging in all have a bento box style design thats very popular in dashboards generally, the rounded corners and subtle color difference from the background makes the design pop out. Again the colors are minimal but vibrant. The table elements too have rounded borders to maintain consistency.

The project employs the Flask python web framework to handle the backend. The frontend is done using HTML, CSS, JavaScript and Chart.js. The database is stored in a .db file and queried using the sqlite3 module of python.

##### Structure of the project

```
/static
    dashboard.css
    landing.css
/templates
    accounts.html
    apology.html
    categories.html
    dashApology.html
    dashboard.html
    dashLayout.html
    index.html
    layout.html
    login.html
    register.html
    settings.html
    transactions.html
app.py
database.db
helpers.py
README.md
requirements.txt
```

app.py has the following routes :
/
/login
/register
/dashboard
/transactions
/accounts
/categories
/settings

The latter 5 require the user to be logged in which is checked by the user_id stored in the session.

##### Database Design

The database has the following schema

```
CREATE TABLE sqlite_sequence(name,seq);

CREATE TABLE users(user_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, password TEXT NOT NULL, email TEXT, currency TEXT DEFAULT 'INR');

CREATE TABLE accounts (account_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, balance REAL DEFAULT 0, icon TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(user_id));

CREATE TABLE categories (c_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, type TEXT NOT NULL, icon TEXT NOT NULL, user_id INTEGER NOT NULL);

CREATE TABLE transactions (t_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, account_id INTEGER NOT NULL, type TEXT NOT NULL, amount REAL NOT NULL, category TEXT NOT NULL, date TEXT DEFAULT current_date, time TEXT DEFAULT current_time, FOREIGN KEY(user_id) REFERENCES users(user_id), FOREIGN KEY(account_id) REFERENCES accounts(account_id), FOREIGN KEY(category) REFERENCES categories(category));
```

The database is queried for data whenever a route is reached. When a user submits a form through POST, the values are accoringly inserted into the corresponding tables in the database. When a route is reached via GET, data is retrieved using SELECT queries and WHERE clauses to specify conditions and also ORDER BY and GROUP BY conditions as and when required.

To display the charts and graphs in the dashboard page, I used Chart.js, a free open source JavaScript library used for data visualization using line, bar, scatter, pie charts etc. The dashboard displays 4 charts:
income line chart
expense line chart
income by category pie chart
expense by category pie chart

That was my final project for CS50x 2024.