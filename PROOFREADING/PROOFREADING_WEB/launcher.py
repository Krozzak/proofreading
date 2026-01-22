import os
import sys
import threading
import webbrowser
import time
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import fitz
from PIL import Image
import numpy as np
from skimage.metrics._structural_similarity import structural_similarity as ssim
import io
import base64
import csv
from datetime import datetime
import socket

# Fonction pour trouver un port disponible
def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

# Déterminer le chemin de base (différent en .exe)
if getattr(sys, 'frozen', False):
    # Mode exécutable
    BASE_DIR = sys._MEIPASS
    STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
    TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
else:
    # Mode développement
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
    TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')

# Créer les dossiers nécessaires dans le répertoire de l'utilisateur
UPLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'ProofreadingUploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, 
            static_folder=STATIC_FOLDER,
            template_folder=TEMPLATE_FOLDER)

app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'loreal-proofreading-secret-key'

comparison_results = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'zip'}

def extract_code(filename):
    base_name = os.path.basename(filename)
    return base_name[:8] if len(base_name) >= 8 else base_name

def pdf_to_image(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img
    except Exception as e:
        print(f"Erreur conversion PDF: {e}")
        return None

def image_to_base64(img, max_size=(400, 400)):
    try:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        print(f"Erreur conversion base64: {e}")
        return None

def compare_images(img1, img2):
    try:
        max_size = (800, 800)
        img1 = img1.convert('RGB')
        img2 = img2.convert('RGB')
        
        img1.thumbnail(max_size, Image.Resampling.LANCZOS)
        img2.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        if img1.size != img2.size:
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)
        
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        gray1 = np.mean(arr1, axis=2).astype(np.float32)
        gray2 = np.mean(arr2, axis=2).astype(np.float32)
        
        similarity_index = ssim(gray1, gray2, data_range=gray2.max() - gray2.min())
        score = max(0, min(100, similarity_index * 100))
        
        return round(score, 2)
    except Exception as e:
        print(f"Erreur comparaison: {e}")
        return None

def find_pdfs(folder):
    pdfs = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdfs.append(os.path.join(root, file))
    return pdfs

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    global comparison_results
    comparison_results = []
    
    try:
        # Nettoyer les anciens fichiers
        import shutil
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        original_files = request.files.getlist('original_folder')
        printer_files = request.files.getlist('printer_folder')
        threshold = float(request.form.get('threshold', 95.0))
        
        if not original_files or not printer_files:
            return jsonify({'error': 'Veuillez sélectionner les deux dossiers'}), 400
        
        original_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'original')
        printer_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'printer')
        os.makedirs(original_folder, exist_ok=True)
        os.makedirs(printer_folder, exist_ok=True)
        
        # Sauvegarder les fichiers SANS modifier les noms
        for file in original_files:
            if file and file.filename:
                filepath = os.path.join(original_folder, file.filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)

        for file in printer_files:
            if file and file.filename:
                filepath = os.path.join(printer_folder, file.filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)

        original_pdfs = find_pdfs(original_folder)
        printer_pdfs = find_pdfs(printer_folder)

        if not original_pdfs and not printer_pdfs:
            return jsonify({'error': 'Aucun fichier PDF trouvé'}), 400

        # Créer les paires (comme dans proofreading_v2.py)
        processed_codes = set()

        # D'abord, traiter tous les fichiers originaux
        for original_pdf in original_pdfs:
            code = extract_code(original_pdf)
            processed_codes.add(code)

            matching_printer = None
            for printer_pdf in printer_pdfs:
                if extract_code(printer_pdf) == code:
                    matching_printer = printer_pdf
                    break

            original_img = pdf_to_image(original_pdf)
            printer_img = pdf_to_image(matching_printer) if matching_printer else None

            score = None
            if original_img and printer_img:
                score = compare_images(original_img, printer_img)

            original_b64 = image_to_base64(original_img) if original_img else None
            printer_b64 = image_to_base64(printer_img) if printer_img else None

            result = {
                'litho_code': code,
                'filename': os.path.basename(original_pdf),
                'original_path': original_pdf,
                'printer_path': matching_printer,
                'original_image': original_b64,
                'printer_image': printer_b64,
                'score': score,
                'matching': 'Both' if matching_printer else 'Original only',
                'validation': 'Auto-Approved' if score and score >= threshold else 'Pending',
                'comment': f'Auto-approved (Score: {score}%)' if score and score >= threshold else '',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S') if score and score >= threshold else ''
            }

            comparison_results.append(result)

        # Ensuite, traiter les fichiers printer qui n'ont pas de correspondance dans original
        for printer_pdf in printer_pdfs:
            code = extract_code(printer_pdf)
            if code not in processed_codes:
                printer_img = pdf_to_image(printer_pdf)
                printer_b64 = image_to_base64(printer_img) if printer_img else None

                result = {
                    'litho_code': code,
                    'filename': os.path.basename(printer_pdf),
                    'original_path': None,
                    'printer_path': printer_pdf,
                    'original_image': None,
                    'printer_image': printer_b64,
                    'score': None,
                    'matching': 'Printer only',
                    'validation': 'Pending',
                    'comment': '',
                    'date': ''
                }

                comparison_results.append(result)
        
        return jsonify({
            'success': True,
            'total': len(comparison_results),
            'matched': len([r for r in comparison_results if r['matching'] == 'Both']),
            'auto_approved': len([r for r in comparison_results if r['validation'] == 'Auto-Approved']),
            'threshold': threshold
        })
        
    except Exception as e:
        print(f"Erreur upload: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/results')
def get_results():
    return jsonify(comparison_results)

@app.route('/validate/<int:index>', methods=['POST'])
def validate_item(index):
    global comparison_results
    
    try:
        data = request.json
        approved = data.get('approved', True)
        comment = data.get('comment', '')
        
        if 0 <= index < len(comparison_results):
            comparison_results[index]['validation'] = 'Approved' if approved else 'Rejected'
            comparison_results[index]['comment'] = comment
            comparison_results[index]['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({'success': True})
        
        return jsonify({'error': 'Index invalide'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/csv')
def export_csv():
    try:
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        writer.writerow(['Code Litho', 'Filename', 'Matching', 'Score (%)', 'Validation', 'Comment', 'Date'])
        
        for result in comparison_results:
            writer.writerow([
                result['litho_code'],
                result['filename'],
                result['matching'],
                result['score'] if result['score'] else 'N/A',
                result['validation'],
                result['comment'],
                result['date']
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'proofreading_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auto-approve', methods=['POST'])
def auto_approve():
    global comparison_results
    
    try:
        data = request.json
        threshold = float(data.get('threshold', 95.0))
        
        count = 0
        for result in comparison_results:
            if result['score'] and result['score'] >= threshold and result['validation'] == 'Pending':
                result['validation'] = 'Auto-Approved'
                result['comment'] = f'Auto-approved (Score: {result["score"]}%)'
                result['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                count += 1
        
        return jsonify({'success': True, 'approved_count': count})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def open_browser(port):
    """Ouvre le navigateur après un court délai"""
    time.sleep(1.5)
    webbrowser.open(f'http://127.0.0.1:{port}')

if __name__ == '__main__':
    # Trouver un port disponible
    port = find_free_port()
    
    print("=" * 60)
    print("  L'ORÉAL - PRINTER PROOFREADING")
    print("=" * 60)
    print(f"\n✓ Serveur démarré sur le port {port}")
    print(f"✓ Ouverture automatique du navigateur...")
    print(f"\n📍 URL: http://127.0.0.1:{port}")
    print("\n⚠  Pour arrêter le serveur, fermez cette fenêtre")
    print("=" * 60 + "\n")
    
    # Ouvrir le navigateur dans un thread séparé
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    # Lancer le serveur Flask
    app.run(debug=False, host='127.0.0.1', port=port, use_reloader=False)