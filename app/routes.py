# Define las rutas (endpoints) de la aplicación.
import urllib.parse
from datetime import date
import os
from functools import wraps

from flask import render_template, redirect, url_for, flash, current_app, request, send_from_directory, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename

from app.forms import *
from app.models import *
from flask import Blueprint

# Crear un objeto Blueprint
bp = Blueprint('renovate', __name__)


def rol_requerido(nombre_rol):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Necesitas iniciar sesión para acceder a esta página.', 'error')
                return redirect(url_for('renovate.login'))
            if current_user.rol_usuario.nombre_rol != nombre_rol:
                flash('No tienes permiso para acceder a esta página.', 'error')
                return redirect(url_for('renovate.categorias'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def roles_permitidos(*nombres_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Necesitas iniciar sesión para acceder a esta página.', 'error')
                return redirect(url_for('renovate.login'))
            if current_user.rol_usuario.nombre_rol not in nombres_roles:
                flash('No tienes permiso para acceder a esta página.', 'error')
                return redirect(url_for('renovate.categorias'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@bp.route('/')
def index():
    return redirect(url_for('renovate.categorias'))


@bp.route('/crear_rol', methods=['GET', 'POST'])
@login_required
@roles_permitidos('Administrador')
def crear_rol():
    form = RolUsuarioForm()
    if form.validate_on_submit():
        nombre_rol = form.nombre_rol.data

        # Verificar si el rol ya existe
        rol_existente = RolUsuario.query.filter_by(nombre_rol=nombre_rol).first()
        if rol_existente:
            flash('El rol ya existe.', 'error')
        else:
            # Crear el nuevo rol
            nuevo_rol = RolUsuario(nombre_rol=nombre_rol)
            db.session.add(nuevo_rol)
            db.session.commit()
            flash('Rol creado exitosamente.', 'success')
            return redirect(url_for('renovate.categorias'))  # Cambia a la ruta que desees

    return render_template('crear_rol.html', form=form)


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

    # Populate provincias and localidades
    provincias = Provincia.query.all()
    localidades = []

    if request.method == 'POST' and form.validate_on_submit():
        nombre = form.nombre.data
        apellido = form.apellido_usuario.data
        nombre_usuario = form.nombre_usuario.data
        contrasena_usuario = generate_password_hash(form.contrasena_usuario.data)
        email = form.email_usuario.data
        fecha_nacimiento = form.fecha_nacimiento_usuario.data
        calle = form.calle_direccion.data
        numero = form.numero_direccion.data
        cod_provincia = request.form.get('provincia')
        cod_localidad = request.form.get('localidad')

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

        usuario = Usuario(
            nombre_usuario=nombre_usuario,
            nombre=nombre,
            apellido_usuario=apellido,
            contrasena_usuario=contrasena_usuario,
            email_usuario=email,
            fecha_nacimiento_usuario=fecha_nacimiento,
            foto_usuario=foto_filename,
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
@login_required
@roles_permitidos('Administrador')
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
@login_required
@roles_permitidos('Administrador')
def listar_provincias():
    provincias = Provincia.query.filter_by(fecha_baja_provincia=None).all()  # Excluye las provincias con fecha de baja
    return render_template('listar_provincias.html', provincias=provincias)


@bp.route('/provincias/eliminar/<int:cod_provincia>', methods=['POST'])
@login_required
@roles_permitidos('Administrador')
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
@login_required
@roles_permitidos('Administrador')
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
@login_required
@roles_permitidos('Administrador')
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
@login_required
@roles_permitidos('Administrador')
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
@login_required
@roles_permitidos('Administrador')
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
@login_required
@roles_permitidos('Administrador')
def dar_baja_localidad(cod_localidad):
    localidad = Localidad.query.get_or_404(cod_localidad)
    localidad.fecha_baja_localidad = datetime.now().date()
    db.session.commit()
    flash('Localidad dada de baja con éxito', 'success')
    return redirect(url_for('renovate.listar_localidades', cod_provincia=localidad.cod_provincia))


@bp.route('/perfil/')
@login_required
@roles_permitidos('Normal')
def mi_perfil():
    return render_template('mi_perfil.html')


# Define una ruta estática para las fotos de perfil
@bp.route('/fotos_perfil/<filename>')
def fotos_perfil(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@bp.route('/fotos_publicacion/<filename>')
def fotos_publicacion(filename):
    return send_from_directory(current_app.config['FOTOS_PUBLICACION'], filename)


@bp.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
@roles_permitidos('Normal')
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


@bp.route('/crear_categoria', methods=['GET', 'POST'])
@login_required
@roles_permitidos('Administrador')
def crear_categoria():
    form = CategoriaForm()
    if form.validate_on_submit():
        nueva_categoria = Categoria(nombre_categoria=form.nombre_categoria.data)
        db.session.add(nueva_categoria)
        db.session.commit()
        flash('Categoría creada con éxito!')
        return redirect(url_for('renovate.listar_categorias'))
    return render_template('crear_categoria.html', form=form)


@bp.route('/admin/categorias', methods=['GET'])
@login_required
@roles_permitidos('Administrador')
def listar_categorias():
    categorias = Categoria.query.filter(Categoria.fecha_baja_categoria.is_(None)).all()
    return render_template('listar_categorias.html', categorias=categorias)


@bp.route('/admin/categorias/modificar/<int:cod_categoria>', methods=['GET', 'POST'])
@login_required
@roles_permitidos('Administrador')
def modificar_categoria(cod_categoria):
    categoria = Categoria.query.get_or_404(cod_categoria)
    if request.method == 'POST':
        nombre_categoria = request.form['nombre_categoria']
        if nombre_categoria:
            categoria.nombre_categoria = nombre_categoria
            db.session.commit()
            flash('Categoría actualizada correctamente', 'success')
            return redirect(url_for('listar_categorias'))
        else:
            flash('El nombre de la categoría no puede estar vacío', 'danger')
    return render_template('modificar_categoria.html', categoria=categoria)


@bp.route('/admin/categorias/eliminar/<int:cod_categoria>', methods=['POST'])
@login_required
@roles_permitidos('Administrador')
def eliminar_categoria(cod_categoria):
    categoria = Categoria.query.get_or_404(cod_categoria)
    categoria.fecha_baja_categoria = db.func.current_date()
    db.session.commit()
    flash('Categoría eliminada correctamente', 'success')
    return redirect(url_for('listar_categorias'))


@bp.route('/admin/categorias/<int:cod_categoria>/subcategorias', methods=['GET'])
@login_required
@roles_permitidos('Administrador')
def listar_subcategorias_categorias(cod_categoria):
    categoria = Categoria.query.get_or_404(cod_categoria)
    subcategorias = Subcategoria.query.filter_by(cod_categoria=cod_categoria).all()
    return render_template('listar_subcategorias_categoria.html', categoria=categoria, subcategorias=subcategorias)


@bp.route('/admin/subcategorias/agregar', methods=['GET', 'POST'])
@login_required
@roles_permitidos('Administrador')
def agregar_subcategoria():
    form = SubcategoriaForm()
    if form.validate_on_submit():
        nombre_subcategoria = form.nombre_subcategoria.data
        categorias = form.categorias.data

        for cod_categoria in categorias:
            categoria = Categoria.query.get(cod_categoria)
            if not categoria:
                flash(f'La categoría con ID {cod_categoria} no existe.', 'danger')
                continue

            nueva_subcategoria = Subcategoria(
                nombre_subcategoria=nombre_subcategoria,
                cod_categoria=cod_categoria
            )
            db.session.add(nueva_subcategoria)

        db.session.commit()
        flash('Subcategoría agregada correctamente a las categorías seleccionadas.', 'success')
        return redirect(url_for('renovate.listar_categorias'))

    return render_template('agregar_subcategoria.html', form=form)


@bp.route('/admin/subcategorias')
def listar_subcategorias():
    subcategorias = Subcategoria.query.filter(Subcategoria.fecha_baja_subcategoria.is_(None)).all()
    return render_template('listar_subcategorias.html', subcategorias=subcategorias)


@bp.route('/admin/modificar_subcategoria/<int:cod_subcategoria>', methods=['GET', 'POST'])
@login_required
@roles_permitidos('Administrador')
def modificar_subcategoria(cod_subcategoria):
    subcategoria = Subcategoria.query.get_or_404(cod_subcategoria)
    form = ModificarSubcategoriaForm(obj=subcategoria)
    form.categorias.choices = [(c.cod_categoria, c.nombre_categoria) for c in Categoria.query.all()]

    if form.validate_on_submit():
        subcategoria.nombre_subcategoria = form.nombre_subcategoria.data
        subcategoria.cod_categoria = form.categorias.data
        db.session.commit()
        flash('Subcategoría actualizada exitosamente', 'success')
        return redirect(url_for('renovate.listar_subcategorias'))

    return render_template('modificar_subcategoria.html', form=form, subcategoria=subcategoria)


@bp.route('/admin/eliminar_subcategoria/<int:cod_subcategoria>', methods=['POST'])
@login_required
@roles_permitidos('Administrador')
def eliminar_subcategoria(cod_subcategoria):
    subcategoria = Subcategoria.query.get_or_404(cod_subcategoria)
    subcategoria.fecha_baja_subcategoria = date.today()
    db.session.commit()
    flash('Subcategoría eliminada (fecha de baja asignada) exitosamente', 'success')
    return redirect(url_for('listar_subcategorias'))


@bp.route('/crear_publicacion', methods=['GET', 'POST'])
@login_required
@roles_permitidos('Normal')
def crear_publicacion():
    form = PublicacionForm()
    categorias = Categoria.query.filter_by(fecha_baja_categoria=None).all()

    if form.validate_on_submit():
        # Manejar la subida de la foto
        foto = form.foto_publicacion.data
        foto_filename = secure_filename(foto.filename)
        foto_path = os.path.join(current_app.config['FOTOS_PUBLICACION'], foto_filename)
        foto.save(foto_path)

        # Obtener la categoría seleccionada
        cod_categoria = request.form.get('cod_categoria')
        # Obtener la subcategoría seleccionada
        cod_subcategoria = request.form.get('cod_subcategoria')

        publicacion = Publicacion(
            nombre_publicacion=form.nombre_publicacion.data,
            descripcion_publicacion=form.descripcion_publicacion.data,
            precio_publicacion=form.precio_publicacion.data,
            talle_publicaion=form.talle_publicacion.data,
            color_publicacion=form.color_publicacion.data,
            foto_publicacion=foto_filename,
            cod_subcategoria=cod_subcategoria,
            cod_categoria=cod_categoria,
            cod_usuario=current_user.cod_usuario,
            cod_direccion=current_user.direccion.cod_direccion
        )
        db.session.add(publicacion)
        db.session.commit()
        flash('Publicación creada exitosamente.', 'success')
        return redirect(url_for('renovate.mis_publicaciones'))

    return render_template('publicar.html', form=form, categorias=categorias)


@bp.route('/subcategorias/<int:cod_categoria>', methods=['GET'])
def get_subcategorias(cod_categoria):
    subcategorias = Subcategoria.query.filter_by(cod_categoria=cod_categoria, fecha_baja_subcategoria=None).all()
    subcategorias_list = [{"cod_subcategoria": sub.cod_subcategoria, "nombre_subcategoria": sub.nombre_subcategoria} for sub in subcategorias]
    return jsonify(subcategorias_list)


@bp.route('/mis_publicaciones')
@login_required
@roles_permitidos('Normal')
def mis_publicaciones():
    publicaciones = Publicacion.query.filter_by(cod_usuario=current_user.cod_usuario).all()
    return render_template('mis_publicaciones.html', publicaciones=publicaciones)


@bp.route('/ver_publicacion/<int:id>')
@login_required
@roles_permitidos('Normal')
def ver_publicacion(id):
    publicacion = Publicacion.query.get_or_404(id)
    receptor = Usuario.query.get_or_404(publicacion.usuario.cod_usuario)  # El receptor es el dueño de la publicación
    form = MensajeForm()  # Inicializa tu formulario aquí

    return render_template('ver_publicacion.html', publicacion=publicacion, receptor=receptor, form=form)


@bp.route('/enviar_mensaje/<int:publicacion_id>', methods=['POST'])
@login_required
@roles_permitidos('Normal')
def enviar_mensaje(publicacion_id):
    try:
        contenido_mensaje = request.form.get('contenido_mensaje')

        if not contenido_mensaje:
            flash('El contenido del mensaje no puede estar vacío', 'error')
            return redirect(url_for('renovate.ver_publicacion', id=publicacion_id))

        # Obtener la publicación y el receptor del mensaje
        publicacion = Publicacion.query.get_or_404(publicacion_id)
        receptor = Usuario.query.get_or_404(publicacion.cod_usuario)

        # Crear el objeto Mensaje y guardarlo en la base de datos
        mensaje = Mensaje(
            contenido=contenido_mensaje,
            emisor_id=current_user.cod_usuario,
            receptor_id=receptor.cod_usuario,
            publicacion_id=publicacion_id
        )
        db.session.add(mensaje)
        db.session.commit()

        # Preparar los datos para el correo
        emisor_email = current_user.email_usuario
        receptor_email = receptor.email_usuario
        subject = f"Nuevo mensaje de {current_user.nombre} sobre tu publicación {publicacion.nombre_publicacion}"
        body = f"""
        Hola {receptor.nombre},

        Has recibido un nuevo mensaje de {current_user.nombre} sobre tu publicación "{publicacion.nombre_publicacion}".

        Mensaje:
        {contenido_mensaje}

        Puedes responder a este correo o iniciar sesión en la plataforma para responder el mensaje.

        Saludos,
        El equipo de Renovate
        """

        # Codificar el enlace mailto
        mailto_link = f"mailto:{receptor_email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

        # Redirigir al enlace mailto
        return redirect(mailto_link)

    except Exception as e:
        print(f'Error in enviar_mensaje route: {e}')
        flash('Ocurrió un error inesperado.', 'error')
        return redirect(url_for('renovate.ver_publicacion', id=publicacion_id))


@bp.route('/editar_publicacion/<int:publicacion_id>', methods=['GET', 'POST'])
@login_required
@roles_permitidos('Normal')
def editar_publicacion(publicacion_id):
    publicacion = Publicacion.query.get_or_404(publicacion_id)
    form = PublicacionForm(obj=publicacion)

    if form.validate_on_submit():
        form.populate_obj(publicacion)

        if form.foto_publicacion.data:
            # Guardar la nueva foto
            filename = secure_filename(form.foto_publicacion.data.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            form.foto_publicacion.data.save(filepath)
            publicacion.foto_publicacion = filename

        db.session.commit()
        flash('Publicación actualizada con éxito', 'success')
        return redirect(url_for('renovate.ver_publicacion', publicacion_id=publicacion.cod_publicacion))

    categorias = Categoria.query.all()
    subcategorias = Subcategoria.query.filter_by(cod_categoria=publicacion.cod_categoria).all()

    return render_template('editar_publicacion.html', form=form, publicacion=publicacion, categorias=categorias, subcategorias=subcategorias)


@bp.route('/categorias')
@login_required
@roles_permitidos('Normal')
def categorias():
    categorias = Categoria.query.all()
    return render_template('buscador_categorias.html', categorias=categorias)


@bp.route('/categorias/<int:cod_categoria>/subcategorias')
@login_required
@roles_permitidos('Normal')
def subcategorias(cod_categoria):
    subcategorias = Subcategoria.query.filter_by(cod_categoria=cod_categoria).all()
    categoria = Categoria.query.get_or_404(cod_categoria)
    return render_template('buscador_subcategorias.html', subcategorias=subcategorias, categoria=categoria)


@bp.route('/publicaciones/subcategoria/<int:cod_subcategoria>')
@login_required
@roles_permitidos('Normal')
def publicaciones_por_subcategoria(cod_subcategoria):
    subcategoria = Subcategoria.query.get_or_404(cod_subcategoria)
    publicaciones = Publicacion.query.filter_by(cod_subcategoria=cod_subcategoria).all()
    return render_template('publicaciones_subcategoria.html', subcategoria=subcategoria, publicaciones=publicaciones)


@bp.route('/buscar_publicaciones', methods=['GET', 'POST'])
@login_required
@roles_permitidos('Normal')
def buscar_publicaciones():
    if request.method == 'POST':
        termino_busqueda = request.form.get('termino_busqueda')
        if termino_busqueda:
            publicaciones = Publicacion.query.filter(Publicacion.nombre_publicacion.ilike(f'%{termino_busqueda}%')).all()
            return render_template('resultados_busqueda.html', publicaciones=publicaciones, termino_busqueda=termino_busqueda)
    return redirect(url_for('categorias'))


@bp.route('/notificaciones', methods=['GET'])
@login_required
@roles_permitidos('Normal')
def notificaciones():
    # Obtener todas las publicaciones del usuario actual
    publicaciones_usuario = Publicacion.query.filter_by(cod_usuario=current_user.cod_usuario).all()

    # Obtener todos los mensajes relacionados con las publicaciones del usuario
    mensajes = []
    for publicacion in publicaciones_usuario:
        mensajes.extend(Mensaje.query.filter_by(cod_publicacion=publicacion.cod_publicacion).all())

    return render_template('notificaciones.html', mensajes=mensajes)
