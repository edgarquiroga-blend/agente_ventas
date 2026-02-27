from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, sys, glob

app = Flask(__name__)
CORS(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    from flask import send_from_directory
    return send_from_directory(BASE_DIR, 'interfaz.html')

@app.route('/css/<path:path>')
def css_files(path):
    from flask import send_from_directory
    return send_from_directory(os.path.join(BASE_DIR, 'css'), path)
sys.path.insert(0, os.getcwd())
from agent import run_agent
from database import initialize_database

# Inicializar BD y agente
initialize_database()
print("🔄 Inicializando agente...")
print("✅ Agente listo!")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'interfaz.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(BASE_DIR, path)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        pregunta = data.get('pregunta', '')
        if not pregunta:
            return jsonify({'error': 'Pregunta vacía'}), 400
        respuesta = run_agent(pregunta, provider="groq")
        # Buscar archivos recién generados
        archivos = sorted(glob.glob('outputs/*.png') + 
                         glob.glob('outputs/*.csv') + 
                         glob.glob('outputs/*.xlsx'),
                         key=os.path.getmtime, reverse=True)
        archivo_reciente = os.path.basename(archivos[0]) if archivos else None
        return jsonify({
            'respuesta': respuesta,
            'archivo': archivo_reciente
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/archivo/<filename>')
def get_archivo(filename):
    return send_from_directory('outputs', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)