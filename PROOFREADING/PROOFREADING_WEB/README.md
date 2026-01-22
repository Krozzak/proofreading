📁 STRUCTURE DU PROJET

PROOFREADING_WEB/
├── app.py                      # Serveur Flask
├── requirements.txt            # Dépendances
├── templates/
│   ├── index.html             # Page d'accueil
│   └── results.html           # Page de résultats
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── uploads/               # Fichiers uploadés (temporaire)
└── README.md

🚀 ÉTAPE 1 : Installation
# Créer le dossier du projet
cd "C:\Users\thomas.silliard\OneDrive - L'Oréal\Desktop\SCRIPT_PYTHON"
mkdir PROOFREADING_WEB
cd PROOFREADING_WEB

# Activer l'environnement virtuel
..\.venv\Scripts\Activate.ps1

# Installer Flask et dépendances
pip install flask flask-cors pymupdf pillow scikit-image numpy werkzeug