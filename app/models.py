# Define los modelos de datos utilizando SQLAlchemy u otro ORM.
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager
from datetime import datetime

from app.enums import Talle


class RolUsuario(db.Model):
    cod_rol = db.Column(db.Integer, primary_key=True)
    nombre_rol = db.Column(db.String(14), index=True, unique=True)
    fecha_baja_RU = db.Column(db.Date, default=None)
    usuarios = db.relationship('Usuario', backref='rol_usuario', lazy='dynamic')

    def dar_de_baja(self):
        self.fecha_baja_RU = datetime.utcnow().date()


class Usuario(db.Model):
    cod_usuario = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(14), index=True, unique=True)
    nombre = db.Column(db.String(14))
    apellido_usuario = db.Column(db.String(14))
    contrasena_usuario = db.Column(db.String(20))
    email_usuario = db.Column(db.String(100), index=True, unique=True)
    foto_usuario = db.Column(db.String(300), default=None)
    fecha_nacimiento_usuario = db.Column(db.Date)
    cod_rol = db.Column(db.Integer, db.ForeignKey('rol_usuario.cod_rol'))
    mensajes_enviados = db.relationship('Mensaje', foreign_keys='Mensaje.cod_emisor', backref='emisor', lazy='dynamic')
    mensajes_recibidos = db.relationship('Mensaje', foreign_keys='Mensaje.cod_receptor', backref='receptor',
                                         lazy='dynamic')
    publicaciones = db.relationship('Publicacion', backref='usuario', lazy='dynamic')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    direccion = db.relationship('Direccion', uselist=False, back_populates='usuario')


    def is_authenticated(self):
        return True

    def get_id(self):
        return str(self.cod_usuario)

    def set_password(self, password):
        self.contrasena_usuario = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.contrasena_usuario, password)

    def __repr__(self):
        return f'<Usuario {self.nombre_usuario}>'


@login_manager.user_loader
def cargar_usuario(cod_usuario):
    return Usuario.query.get(int(cod_usuario))


class Direccion(db.Model):
    cod_direccion = db.Column(db.Integer, primary_key=True)
    calle_direccion = db.Column(db.String(100), index=True)
    numero_direccion = db.Column(db.Integer)
    cod_localidad = db.Column(db.Integer, db.ForeignKey('localidad.cod_localidad'))
    cod_usuario = db.Column(db.Integer, db.ForeignKey('usuario.cod_usuario'))
    usuario = db.relationship('Usuario', back_populates='direccion')
    publicaciones = db.relationship('Publicacion', backref='direccion', lazy='dynamic')


class Localidad(db.Model):
    cod_localidad = db.Column(db.Integer, primary_key=True)
    nombre_localidad = db.Column(db.String(100), index=True)
    fecha_baja_localidad = db.Column(db.Date, default=None)
    direcciones = db.relationship('Direccion', backref='localidad', lazy='dynamic')
    cod_provincia = db.Column(db.Integer, db.ForeignKey('provincia.cod_provincia'))

    def dar_de_baja(self):
        self.fecha_baja_localidad = datetime.utcnow().date()


class Provincia(db.Model):
    cod_provincia = db.Column(db.Integer, primary_key=True)
    nombre_provincia = db.Column(db.String(100), index=True, unique=True)
    fecha_baja_provincia = db.Column(db.Date, default=None)
    localidades = db.relationship('Localidad', backref='provincia', lazy='dynamic')

    def dar_de_baja(self):
        self.fecha_baja_provincia = datetime.utcnow().date()


class Categoria(db.Model):
    cod_categoria = db.Column(db.Integer, primary_key=True)
    nombre_categoria = db.Column(db.String(100), index=True, unique=True)
    fecha_baja_categoria = db.Column(db.Date, default=None)
    subcategorias = db.relationship('Subcategoria', backref='categoria_relacionada', lazy='dynamic')
    publicaciones = db.relationship('Publicacion', backref='categoria', lazy='dynamic')

    def dar_de_baja(self):
        self.fecha_baja_categoria = datetime.utcnow().date()


class Subcategoria(db.Model):
    cod_subcategoria = db.Column(db.Integer, primary_key=True)
    nombre_subcategoria = db.Column(db.String(100), index=True)
    fecha_baja_subcategoria = db.Column(db.Date, default=None)
    publicaciones = db.relationship('Publicacion', backref='subcategoria', lazy='dynamic')
    cod_categoria = db.Column(db.Integer, db.ForeignKey('categoria.cod_categoria'))

    def dar_de_baja(self):
        self.fecha_baja_subcategoria = datetime.utcnow().date()


class Publicacion(db.Model):
    cod_publicacion = db.Column(db.Integer, primary_key=True)
    nombre_publicacion = db.Column(db.String(100), index=True)
    descripcion_publicacion = db.Column(db.String(300))
    precio_publicacion = db.Column(db.Float, index=True)
    talle_publicaion = db.Column(db.Enum(Talle))
    color_publicacion = db.Column(db.String(20), index=True)
    vendido = db.Column(db.Boolean, default=False)
    foto_publicacion = db.Column(db.String(300))
    cod_categoria = db.Column(db.Integer, db.ForeignKey('categoria.cod_categoria'))
    cod_subcategoria = db.Column(db.Integer, db.ForeignKey('subcategoria.cod_subcategoria'))
    cod_usuario = db.Column(db.Integer, db.ForeignKey('usuario.cod_usuario'))
    mensajes = db.relationship('Mensaje', backref='publicacion', lazy='dynamic')
    cod_direccion = db.Column(db.Integer, db.ForeignKey('direccion.cod_direccion'))


class Mensaje(db.Model):
    cod_mensaje = db.Column(db.Integer, primary_key=True)
    fecha_mensaje = db.Column(db.Date)
    contenido_mensaje = db.Column(db.String(300))
    cod_emisor = db.Column(db.Integer, db.ForeignKey('usuario.cod_usuario'))
    cod_receptor = db.Column(db.Integer, db.ForeignKey('usuario.cod_usuario'))
    cod_publicacion = db.Column(db.Integer, db.ForeignKey('publicacion.cod_publicacion'))
