from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_proy_aula'

# ============================================
# CONFIGURACIÓN DE BASE DE DATOS (RAILWAY)
# ============================================
def get_db():
    return mysql.connector.connect(
        host=os.environ.get('MYSQLHOST', 'localhost'),
        user=os.environ.get('MYSQLUSER', 'root'),
        password=os.environ.get('MYSQLPASSWORD', 'hola'),
        database=os.environ.get('MYSQLDATABASE', 'control_estudiantil'),
        port=int(os.environ.get('MYSQLPORT', 3306))
    )

# ============================================
# RUTAS PRINCIPALES
# ============================================

@app.route('/')
def home():
    if 'usuario_logueado' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    datos = request.get_json()
    correo = datos.get('correo')
    contrasena = datos.get('contrasena')
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE correo = %s AND contrasena = %s", (correo, contrasena))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if usuario:
            session['usuario_logueado'] = usuario['correo']
            session['nombre'] = usuario.get('nombre', 'Estudiante')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False})
    except Exception as e:
        return jsonify({'success': False, 'mensaje': str(e)})

# ============================================
# INDEX - PÁGINA PRINCIPAL
# ============================================

@app.route('/index')
def index():
    if 'usuario_logueado' not in session:
        return redirect(url_for('home'))
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT contenido FROM consejos ORDER BY id DESC LIMIT 7")
        consejos = cursor.fetchall()
        
        cursor.execute("SELECT contenido FROM efemerides ORDER BY id DESC LIMIT 7")
        efemerides = cursor.fetchall()
        
        cursor.execute("SELECT titulo, contenido FROM noticias ORDER BY id DESC LIMIT 7")
        noticias = cursor.fetchall()
        
        cursor.execute("SELECT contenido FROM comentarios ORDER BY id DESC")
        comentarios = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        ruta_music = os.path.join(app.root_path, 'static', 'music')
        ruta_podcast = os.path.join(app.root_path, 'static', 'podcast')
        
        musicas = os.listdir(ruta_music) if os.path.exists(ruta_music) else []
        podcasts = os.listdir(ruta_podcast) if os.path.exists(ruta_podcast) else []
        
        return render_template('index.html', 
                               nombre=session.get('nombre'),
                               noticias=noticias,
                               consejos=consejos,
                               efemerides=efemerides,
                               comentarios=comentarios,
                               musicas=musicas, 
                               podcasts=podcasts)
    except Exception as e:
        return f"Error en la base de datos: {e}"

# ============================================
# API PARA ACTUALIZACIÓN AUTOMÁTICA
# ============================================

@app.route('/api/datos')
def api_datos():
    if 'usuario_logueado' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT titulo, contenido FROM noticias ORDER BY id DESC LIMIT 7")
        noticias = cursor.fetchall()
        
        cursor.execute("SELECT contenido FROM consejos ORDER BY id DESC LIMIT 7")
        consejos = cursor.fetchall()
        
        cursor.execute("SELECT contenido FROM efemerides ORDER BY id DESC LIMIT 7")
        efemerides = cursor.fetchall()
        
        cursor.execute("SELECT contenido FROM comentarios ORDER BY id DESC")
        comentarios = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        ruta_music = os.path.join(app.root_path, 'static', 'music')
        ruta_podcast = os.path.join(app.root_path, 'static', 'podcast')
        
        musicas = os.listdir(ruta_music) if os.path.exists(ruta_music) else []
        podcasts = os.listdir(ruta_podcast) if os.path.exists(ruta_podcast) else []
        
        return jsonify({
            'noticias': noticias,
            'consejos': consejos,
            'efemerides': efemerides,
            'comentarios': comentarios,
            'musicas': musicas,
            'podcasts': podcasts
        })
    except Exception as e:
        return jsonify({'error': str(e)})

# ============================================
# SERVIR ARCHIVOS ESTÁTICOS
# ============================================

@app.route('/static/music/<filename>')
def serve_music(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'music'), filename)

@app.route('/static/podcast/<filename>')
def serve_podcast(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'podcast'), filename)

# ============================================
# COMENTARIOS
# ============================================

@app.route('/comentar', methods=['POST'])
def comentar():
    datos = request.get_json()
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO comentarios (contenido) VALUES (%s)", (datos['contenido'],))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============================================
# LOGOUT
# ============================================

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ============================================
# INICIAR SERVIDOR (RAILWAY)
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)