# Define las rutas (endpoints) de la aplicación.
from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from app.forms import *

# Importa la clase Usuario desde el archivo models.py
from app.models import *
from flask import Blueprint

# Crear un objeto Blueprint
bp = Blueprint('renovate', __name__)


# Define tus rutas dentro de este archivo

# Define la ruta para la página de inicio
@bp.route('/')
@login_required
def index():
    return render_template('index.html')


# Define la ruta para el inicio de sesión
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('renovate.index'))

    form = LoginForm()
    if form.validate_on_submit():
        nombre_usuario = form.nombre_usuario.data
        contrasena = form.contrasena.data

        usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()
        if usuario is not None and usuario.check_password(contrasena):
            login_user(usuario)
            flash('Inicio de sesión exitoso para el usuario {}'.format(usuario.nombre_usuario))
            return redirect(url_for('renovate.index'))
        else:
            flash('Usuario o contraseña incorrectos')

    return render_template('login.html', form=form)


@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('renovate.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        nombre = form.nombre.data
        apellido = form.apellido_usuario.data
        nombre_usuario = form.nombre_usuario.data
        contrasena_usuario = generate_password_hash(form.contrasena_usuario.data)
        email = form.email_usuario.data
        fecha_nacimiento = form.fecha_nacimiento_usuario.data

        usuario = Usuario(nombre_usuario, nombre, apellido, contrasena_usuario, email, fecha_nacimiento, cod_rol=1)
        try:
            db.session.add(usuario)
            db.session.commit()
            flash('Your account has been created! You are now able to log in', 'success')
            login_user(usuario)
            return redirect(url_for('renovate.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {e}', 'danger')

    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')

    return render_template('registro.html', form=form)


# Define la ruta para cerrar sesión
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('renovate.index'))
