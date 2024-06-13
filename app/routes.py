# Define las rutas (endpoints) de la aplicación.
from datetime import date
import os

from flask import render_template, redirect, url_for, flash, current_app, request, send_from_directory, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename

from app.forms import *
from app.models import *
from flask import Blueprint

# Crear un objeto Blueprint
bp = Blueprint('renovate', __name__)


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
            return redirect(url_for('renovate.index'))
        else:
            flash('Usuario o contraseña incorrectos')

    return render_template('login.html', form=form)


@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('renovate.index'))

    form = RegisterForm()
    provincias = Provincia.query.all()
    localidades = Localidad.query.all()

    if form.validate_on_submit():
        nombre = form.nombre.data
        apellido = form.apellido_usuario.data
        nombre_usuario = form.nombre_usuario.data
        contrasena_usuario = generate_password_hash(form.contrasena_usuario.data)
        email = form.email_usuario.data
        fecha_nacimiento = form.fecha_nacimiento_usuario.data
        calle = form.calle_direccion.data
        numero = form.numero_direccion.data
        cod_provincia = form.provincia.data
        cod_localidad = form.cod_localidad.data

        # Verificar si el nombre de usuario ya existe
        if Usuario.query.filter_by(nombre_usuario=nombre_usuario).first():
            flash('El nombre de usuario ya está en uso.', 'danger')
            return render_template('registro.html', form=form, provincias=provincias, localidades=localidades)

        # Verificar si el correo electrónico ya existe
        if Usuario.query.filter_by(email_usuario=email).first():
            flash('El correo electrónico ya está en uso.', 'danger')
            return render_template('registro.html', form=form, provincias=provincias, localidades=localidades)

        # Validar que el usuario tiene al menos 18 años
        hoy = date.today()
        edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
        if edad < 18:
            flash('Debes tener al menos 18 años para registrarte.', 'danger')
            return render_template('registro.html', form=form, provincias=provincias, localidades=localidades)

        foto = request.files.get('foto_usuario')
        if foto and foto.filename != '':
            foto_filename = secure_filename(foto.filename)
            foto_path = os.path.join(current_app.config['UPLOAD_FOLDER'], foto_filename)
            foto.save(foto_path)
        else:
            foto_filename = None

        direccion = Direccion(
            calle_direccion=calle,
            numero_direccion=numero,
            cod_localidad=cod_localidad
        )

        # Crear el objeto Usuario con la imagen de perfil (si existe)
        usuario = Usuario(
            nombre_usuario=nombre_usuario,
            nombre=nombre,
            apellido_usuario=apellido,
            contrasena_usuario=contrasena_usuario,
            email_usuario=email,
            fecha_nacimiento_usuario=fecha_nacimiento,
            foto_usuario=foto_filename,  # Ruta de la imagen guardada
            cod_rol=1,
            direccion=direccion
        )

        try:
            db.session.add(direccion)
            db.session.add(usuario)
            db.session.commit()
            login_user(usuario)
            return redirect(url_for('renovate.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {e}', 'danger')

    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')

    return render_template('registro.html', form=form, provincias=provincias, localidades=localidades)


# Define la ruta para cerrar sesión
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('renovate.index'))


# rutas administrador
@bp.route('/provincias/nueva', methods=['GET', 'POST'])
def nueva_provincia():
    form = ProvinciaForm()
    if form.validate_on_submit():
        nombre_provincia = form.nombre_provincia.data
        provincia = Provincia(nombre_provincia=nombre_provincia)

        # Verificar si el nombre de la provincia ya existe
        if Provincia.query.filter_by(nombre_provincia=nombre_provincia).first():
            flash('El nombre de la provincia ya está en uso.', 'danger')
            return render_template('nueva_provincia.html', form=form)

        try:
            db.session.add(provincia)
            db.session.commit()
            return redirect(url_for('renovate.listar_provincias'))  # Ajusta esto según tu vista de redirección
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la provincia: {e}', 'danger')

    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Error en {getattr(form, field).label.text}: {error}", 'danger')

    return render_template('nueva_provincia.html', form=form)


@bp.route('/provincias')
def listar_provincias():
    provincias = Provincia.query.filter_by(fecha_baja_provincia=None).all()  # Excluye las provincias con fecha de baja
    return render_template('listar_provincias.html', provincias=provincias)


@bp.route('/provincias/eliminar/<int:cod_provincia>', methods=['POST'])
def baja_provincia(cod_provincia):
    provincia = Provincia.query.get_or_404(cod_provincia)
    try:
        provincia.fecha_baja_provincia = date.today()  # Asigna la fecha actual como fecha de baja

        # Dar de baja las localidades relacionadas
        localidades = Localidad.query.filter_by(cod_provincia=cod_provincia, fecha_baja_localidad=None).all()
        for localidad in localidades:
            localidad.fecha_baja_localidad = date.today()

        db.session.commit()
        flash('Provincia marcada como dada de baja exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al dar de baja la provincia: {e}', 'danger')
    return redirect(url_for('renovate.listar_provincias'))


@bp.route('/provincias/modificar/<int:cod_provincia>', methods=['GET', 'POST'])
def modificar_provincia(cod_provincia):
    provincia = Provincia.query.get_or_404(cod_provincia)
    form = ProvinciaForm(obj=provincia)

    if form.validate_on_submit():
        provincia.nombre_provincia = form.nombre_provincia.data
        try:
            db.session.commit()
            return redirect(url_for('renovate.listar_provincias'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al modificar la provincia: {e}', 'danger')

    return render_template('modificar_provincia.html', form=form, provincia=provincia)


@bp.route('/provincias/<int:cod_provincia>/localidades', methods=['GET', 'POST'])
def listar_localidades(cod_provincia):
    provincia = Provincia.query.get_or_404(cod_provincia)
    localidades = Localidad.query.filter_by(cod_provincia=cod_provincia, fecha_baja_localidad=None).all()

    form = LocalidadForm()
    if form.validate_on_submit():
        nombre_localidad = form.nombre_localidad.data
        nueva_localidad = Localidad(nombre_localidad=nombre_localidad, cod_provincia=cod_provincia)

        try:
            db.session.add(nueva_localidad)
            db.session.commit()
            return redirect(url_for('listar_localidades', cod_provincia=cod_provincia))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar la localidad: {e}', 'danger')

    return render_template('listar_localidades.html', provincia=provincia, localidades=localidades, form=form)


@bp.route('/provincias/<int:cod_provincia>/localidades/nueva', methods=['GET', 'POST'])
def agregar_localidad(cod_provincia):
    form = LocalidadForm()
    if form.validate_on_submit():
        nombre_localidad = form.nombre_localidad.data
        nueva_localidad = Localidad(nombre_localidad=nombre_localidad, cod_provincia=cod_provincia)

        try:
            db.session.add(nueva_localidad)
            db.session.commit()
            return redirect(url_for('renovate.listar_localidades', cod_provincia=cod_provincia))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar la localidad: {e}', 'danger')

    return render_template('nueva_localidad.html', form=form, cod_provincia=cod_provincia)


@bp.route('/provincias/<int:cod_provincia>/localidades/modificar/<int:cod_localidad>', methods=['GET', 'POST'])
def modificar_localidad(cod_provincia, cod_localidad):
    localidad = Localidad.query.get_or_404(cod_localidad)
    form = LocalidadForm(obj=localidad)

    if form.validate_on_submit():
        localidad.nombre_localidad = form.nombre_localidad.data
        try:
            db.session.commit()
            return redirect(url_for('renovate.listar_localidades', cod_provincia=cod_provincia))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al modificar la localidad: {e}', 'danger')

    return render_template('modificar_localidad.html', form=form, localidad=localidad)


@bp.route('/localidades/baja/<int:cod_localidad>', methods=['POST'])
def dar_baja_localidad(cod_localidad):
    localidad = Localidad.query.get_or_404(cod_localidad)
    localidad.fecha_baja_localidad = datetime.now().date()
    db.session.commit()
    flash('Localidad dada de baja con éxito', 'success')
    return redirect(url_for('renovate.listar_localidades', cod_provincia=localidad.cod_provincia))


@bp.route('/perfil/')
@login_required
def mi_perfil():
    return render_template('mi_perfil.html')


# Define una ruta estática para las fotos de perfil
@bp.route('/fotos_perfil/<filename>')
def fotos_perfil(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@bp.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    form = UpdateUserForm()
    provincias = Provincia.query.all()
    localidades = Localidad.query.all()

    if form.validate_on_submit():
        updated = False

        email = form.email.data
        password = form.password.data
        foto = form.foto_usuario.data
        calle = form.calle.data
        numero = form.numero.data
        cod_provincia = form.provincia.data
        cod_localidad = form.localidad.data

        if email and email != current_user.email_usuario:
            current_user.email_usuario = email
            updated = True

        if password:
            current_user.contrasena_usuario = generate_password_hash(password)
            updated = True

        if foto:
            foto_filename = secure_filename(foto.filename)
            foto_path = os.path.join(current_app.config['UPLOAD_FOLDER'], foto_filename)
            foto.save(foto_path)
            current_user.foto_usuario = foto_filename
            updated = True

        if current_user.direccion is None:
            direccion = Direccion(
                calle_direccion=calle,
                numero_direccion=numero,
                cod_localidad=cod_localidad
            )
            db.session.add(direccion)
            current_user.direccion = direccion
            updated = True
        else:
            if current_user.direccion.calle_direccion != calle or \
               current_user.direccion.numero_direccion != numero or \
               current_user.direccion.cod_localidad != cod_localidad:
                current_user.direccion.calle_direccion = calle
                current_user.direccion.numero_direccion = numero
                current_user.direccion.cod_localidad = cod_localidad
                updated = True

        if updated:
            try:
                db.session.commit()
                flash('Your profile has been updated.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating your profile: {e}', 'danger')
        else:
            flash('No changes detected.', 'info')

        return redirect(url_for('renovate.mi_perfil'))

    # Pre-fill the form fields with current user data
    form.email.data = current_user.email_usuario
    if current_user.direccion:
        form.calle.data = current_user.direccion.calle_direccion
        form.numero.data = current_user.direccion.numero_direccion
        form.provincia.data = current_user.direccion.localidad.provincia.cod_provincia
        form.localidad.data = current_user.direccion.cod_localidad

    return render_template('editar_perfil.html', form=form, provincias=provincias, localidades=localidades)


@bp.route('/localidades/<int:cod_provincia>')
def get_localidades(cod_provincia):
    localidades = Localidad.query.filter_by(cod_provincia=cod_provincia).all()
    localidades_list = [{"cod_localidad": loc.cod_localidad, "nombre_localidad": loc.nombre_localidad} for loc in localidades]
    return jsonify(localidades_list)
