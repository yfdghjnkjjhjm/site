
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret-key'
DB_PATH = 'archive.db'

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            email TEXT,
            document_type TEXT,
            purpose TEXT,
            comment TEXT,
            status TEXT,
            date_created TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS admin(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT)''')
        if not conn.execute('SELECT * FROM admin').fetchone():
            conn.execute('INSERT INTO admin(username,password) VALUES(?,?)',('admin','12345'))
        if not conn.execute('SELECT * FROM requests').fetchone():
            data = [
                ('Иванов Иван Иванович','ivanov@mail.ru','Справка о рождении','Получение копии','Нужно срочно','новое','2025-10-19 22:18'),
                ('Петров Пётр Петрович','petrov@mail.ru','Справка о прописке','Подтверждение адреса','Для суда','в обработке','2025-10-19 22:18'),
                ('Сидорова Анна Сергеевна','sidorova@mail.ru','Выписка из домовой книги','Оформление наследства',' ','выполнено','2025-10-19 22:18')
            ]
            conn.executemany('INSERT INTO requests(full_name,email,document_type,purpose,comment,status,date_created) VALUES(?,?,?,?,?,?,?)', data)

@app.route('/')
def index():
    return render_template('index.html', title='Главная')

@app.route('/request', methods=['GET','POST'])
def request_form():
    if request.method=='POST':
        f=request.form
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''INSERT INTO requests(full_name,email,document_type,purpose,comment,status,date_created)
                            VALUES(?,?,?,?,?,'новое',?)''',
                            (f['full_name'],f['email'],f['document_type'],f['purpose'],f['comment'],datetime.now().strftime('%Y-%m-%d %H:%M')))
        return render_template('success.html', title='Отправлено')
    return render_template('request.html', title='Подать обращение')

@app.route('/admin', methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        u,p=request.form['username'],request.form['password']
        with sqlite3.connect(DB_PATH) as conn:
            user=conn.execute('SELECT * FROM admin WHERE username=? AND password=?',(u,p)).fetchone()
        if user:
            session['admin']=True
            return redirect(url_for('admin_panel'))
    return render_template('admin_login.html', title='Вход администратора')

@app.route('/admin/panel')
def admin_panel():
    if not session.get('admin'): return redirect(url_for('admin_login'))
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory=sqlite3.Row
        rows=conn.execute('SELECT * FROM requests ORDER BY id DESC').fetchall()
    return render_template('admin_panel.html', title='Панель администратора', requests=rows, query='')

@app.route('/admin/search', methods=['POST'])
def admin_search():
    if not session.get('admin'): return redirect(url_for('admin_login'))
    query=request.form.get('query','').strip()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory=sqlite3.Row
        if query:
            sql='''SELECT * FROM requests WHERE full_name LIKE ? OR email LIKE ? ORDER BY id DESC'''
            rows=conn.execute(sql,(f'%{query}%',f'%{query}%')).fetchall()
        else:
            rows=conn.execute('SELECT * FROM requests ORDER BY id DESC').fetchall()
    return render_template('admin_panel.html', title='Панель администратора', requests=rows, query=query)

@app.route('/update_status/<int:req_id>/<status>')
def update_status(req_id,status):
    if not session.get('admin'): return redirect(url_for('admin_login'))
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('UPDATE requests SET status=? WHERE id=?',(status,req_id))
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__=='__main__':
    init_db()
    app.run(debug=True)
