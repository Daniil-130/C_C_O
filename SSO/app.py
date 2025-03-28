from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)


# Модели базы данных
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# Главная страница
@app.route('/')
def home():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)


# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Пользователь с таким email уже существует!', 'danger')
            return redirect(url_for('register'))

        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация успешна! Войдите в систему.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Проверяем пользователя в базе данных
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin  # Сохраняем статус администратора в сессии
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('user_room'))  # Перенаправление в личную комнату
        else:
            flash('Неверный email или пароль. Попробуйте снова.', 'danger')

    return render_template('login.html')  # Возвращает HTML-шаблон для страницы входа


# Личная комната
@app.route('/user_room', methods=['GET', 'POST'])
def user_room():
    if 'user_id' in session:
        user_id = session['user_id']
        user_posts = Post.query.filter_by(user_id=user_id).all()

        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            new_post = Post(title=title, content=content, user_id=user_id)
            db.session.add(new_post)
            db.session.commit()
            flash('Пост успешно опубликован!', 'success')
            return redirect(url_for('user_room'))

        return render_template('user_room.html', posts=user_posts)

    flash('Войдите в систему, чтобы получить доступ к личной комнате.', 'warning')
    return redirect(url_for('login'))


# Панель администратора
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('is_admin'):  # Проверяем, является ли пользователь администратором
        flash('Доступ запрещён!', 'danger')
        return redirect(url_for('home'))

    users = User.query.all()  # Получаем всех пользователей
    posts = Post.query.all()  # Получаем все посты

    if request.method == 'POST':
        # Получение данных из формы
        user_id = request.form.get('user_id')
        action = request.form.get('action')

        if action == 'update_user':  # Обновление данных пользователя
            new_email = request.form.get('new_email')
            new_password = request.form.get('new_password')
            make_admin = request.form.get('make_admin')

            user = User.query.get(user_id)
            if user:
                if new_email:
                    user.email = new_email
                if new_password:
                    user.password = new_password
                if make_admin == 'true':  # Назначение админом
                    user.is_admin = True
                db.session.commit()
                flash('Информация пользователя обновлена.', 'success')

        elif action == 'delete_user':  # Удаление пользователя
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
                flash('Пользователь удалён.', 'success')

        elif action == 'edit_post':  # Редактирование поста
            post_id = request.form.get('post_id')
            new_title = request.form.get('new_title')
            new_content = request.form.get('new_content')

            post = Post.query.get(post_id)
            if post:
                if new_title:
                    post.title = new_title
                if new_content:
                    post.content = new_content
                db.session.commit()
                flash('Пост обновлён.', 'success')

        elif action == 'delete_post':  # Удаление поста
            post_id = request.form.get('post_id')
            post = Post.query.get(post_id)
            if post:
                db.session.delete(post)
                db.session.commit()
                flash('Пост удалён.', 'success')

    return render_template('admin_panel.html', users=users, posts=posts)


# Выход из системы
@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаём таблицы в базе данных
    app.run(debug=True)
