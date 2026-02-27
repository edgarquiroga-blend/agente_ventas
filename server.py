from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, sys, glob

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)
from agent import run_agent
from database import initialize_database

initialize_database()
print("🔄 Inicializando agente...")
print("✅ Agente listo!")

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'interfaz.html')

@app.route('/css/<path:path>')
def css_files(path):
    return send_from_directory(os.path.join(BASE_DIR, 'css'), path)

@app.route('/js/<path:path>')
def js_files(path):
    return send_from_directory(os.path.join(BASE_DIR, 'js'), path)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        pregunta = data.get('pregunta', '')
        if not pregunta:
            return jsonify({'error': 'Pregunta vacía'}), 400
        respuesta = run_agent(pregunta, provider="groq")
        archivos = sorted(
            glob.glob(os.path.join(BASE_DIR, 'outputs', '*.png')) +
            glob.glob(os.path.join(BASE_DIR, 'outputs', '*.csv')) +
            glob.glob(os.path.join(BASE_DIR, 'outputs', '*.xlsx')),
            key=os.path.getmtime, reverse=True
        )
        archivo_reciente = os.path.basename(archivos[0]) if archivos else None
        return jsonify({'respuesta': respuesta, 'archivo': archivo_reciente})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/archivo/<filename>')
def get_archivo(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'outputs'), filename)

@app.route('/api/estadisticas')
def estadisticas():
    import sqlite3, pandas as pd
    try:
        conn = sqlite3.connect(os.path.join(BASE_DIR, 'ventas.db'))
        df = pd.read_sql("SELECT * FROM ventas", conn)
        conn.close()
        return jsonify({
            'total_registros': len(df),
            'productos_unicos': int(df['producto'].nunique()),
            'vendedores_unicos': int(df['vendedor'].nunique())
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
