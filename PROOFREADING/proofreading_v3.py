import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk, ImageDraw, ImageFont
import datetime
import fitz  # PyMuPDF
import csv
import io
from skimage.metrics import structural_similarity as ssim  # pip install scikit-image
from skimage.feature import canny  # Pour détection de bords
from scipy import ndimage  # Pour dilatation
import numpy as np

# Version
VERSION = "3.0.0"

class CropDialog(tk.Toplevel):
    """
    Fenêtre permettant de sélectionner manuellement la zone de crop.
    L'utilisateur dessine un rectangle sur l'image.
    """

    def __init__(self, parent, img, title="Sélectionner la zone de contenu"):
        super().__init__(parent)
        self.title(title)
        self.img = img
        self.result = None  # Contiendra (left, top, right, bottom)

        # Variables pour le dessin du rectangle
        self.start_x = None
        self.start_y = None
        self.rect_id = None

        self.setup_ui()

        # Modal
        self.transient(parent)
        self.grab_set()

        # Centrer la fenêtre
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        # Frame principale
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)

        # Instructions
        ttk.Label(
            main_frame,
            text="Dessinez un rectangle autour de la zone à comparer.\n"
                 "Cliquez et glissez pour sélectionner.",
            justify='center',
            font=("Arial", 11)
        ).pack(pady=10)

        # Canvas pour l'image
        self.canvas = tk.Canvas(main_frame, cursor="crosshair", bg='gray')
        self.canvas.pack(fill='both', expand=True)

        # Afficher l'image redimensionnée
        display_size = (700, 700)
        self.display_img = self.img.copy()
        self.display_img.thumbnail(display_size, Image.Resampling.LANCZOS)
        self.scale_x = self.img.width / self.display_img.width
        self.scale_y = self.img.height / self.display_img.height

        self.tk_img = ImageTk.PhotoImage(self.display_img)
        self.canvas.config(width=self.display_img.width, height=self.display_img.height)
        self.canvas.create_image(0, 0, anchor='nw', image=self.tk_img)

        # Événements souris
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Boutons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)

        ttk.Button(btn_frame, text="Valider", command=self.validate).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Annuler", command=self.cancel).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Image entière", command=self.use_full).pack(side='left', padx=10)

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id:
            self.canvas.delete(self.rect_id)

    def on_drag(self, event):
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline='lime', width=3
        )

    def on_release(self, event):
        self.end_x = event.x
        self.end_y = event.y

    def validate(self):
        if self.start_x is None or not hasattr(self, 'end_x'):
            messagebox.showwarning("Attention", "Veuillez sélectionner une zone.")
            return

        # Convertir les coordonnées d'affichage en coordonnées réelles
        left = int(min(self.start_x, self.end_x) * self.scale_x)
        top = int(min(self.start_y, self.end_y) * self.scale_y)
        right = int(max(self.start_x, self.end_x) * self.scale_x)
        bottom = int(max(self.start_y, self.end_y) * self.scale_y)

        # Vérifier que la sélection est valide
        if right - left < 10 or bottom - top < 10:
            messagebox.showwarning("Attention", "La zone sélectionnée est trop petite.")
            return

        self.result = (left, top, right, bottom)
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()

    def use_full(self):
        self.result = (0, 0, self.img.width, self.img.height)
        self.destroy()


class ImageComparator:
    def __init__(self, master):
        self.master = master
        self.master.title(f"PRINTER PROOFREADING v{VERSION}")
        self.master.geometry("1600x1200")

        self.original_folder = ""
        self.printer_folder = ""
        self.image_pairs = []
        self.current_index = 0
        self.show_only_matched = False
        self.similarity_threshold = 0.85  # Seuil par défaut (85%)

        # NOUVEAU V3: Options de détection de contenu
        self.auto_crop_enabled = True
        self.show_crop_overlay = True
        self.similarity_enabled = True  # Option pour désactiver complètement le score
        self.manual_bounds_original = None
        self.manual_bounds_printer = None
        self.last_detection = None

        # Images PIL actuelles (pour le crop manuel)
        self.current_original_img = None
        self.current_printer_img = None

        # NOUVEAU V3: Support multi-pages
        self.current_page = 0  # Page actuelle (0-indexed)
        self.total_pages_original = 1
        self.total_pages_printer = 1
        self.page_validations = {}  # {(pair_index, page_number): 'approved'/'rejected'/None}

        # État de l'interface
        self.startup_mode = True

        self.setup_startup_ui()

    # ==================== NOUVELLES FONCTIONS V3: DÉTECTION DE CONTENU ====================

    def detect_content_bounds(self, img, margin_threshold=250, min_content_ratio=0.05):
        """
        Détecte la zone de contenu en identifiant les pixels non-blancs.
        Retourne: (left, top, right, bottom) ou None si échec
        """
        try:
            gray = np.array(img.convert('L'))

            # Masque: True = contenu (non-blanc)
            mask = gray < margin_threshold

            # Ratio de contenu par ligne/colonne
            row_content = np.sum(mask, axis=1) / mask.shape[1]
            col_content = np.sum(mask, axis=0) / mask.shape[0]

            # Trouver les limites du contenu
            content_rows = np.where(row_content > min_content_ratio)[0]
            content_cols = np.where(col_content > min_content_ratio)[0]

            if len(content_rows) == 0 or len(content_cols) == 0:
                return None

            top, bottom = content_rows[0], content_rows[-1]
            left, right = content_cols[0], content_cols[-1]

            # Ajouter padding de 2%
            h, w = gray.shape
            padding_h, padding_w = int(h * 0.02), int(w * 0.02)

            return (
                max(0, left - padding_w),
                max(0, top - padding_h),
                min(w, right + padding_w),
                min(h, bottom + padding_h)
            )
        except Exception as e:
            print(f"Error in detect_content_bounds: {e}")
            return None

    def detect_content_bounds_edge(self, img, sigma=2.0):
        """
        Utilise la détection de contours Canny pour les designs blancs sur blanc.
        """
        try:
            gray = np.array(img.convert('L')).astype(float) / 255.0

            # Détection de contours
            edges = canny(gray, sigma=sigma, low_threshold=0.1, high_threshold=0.3)

            # Dilater pour connecter les contours proches
            edges = ndimage.binary_dilation(edges, iterations=3)

            # Trouver les coordonnées des pixels de contour
            edge_coords = np.argwhere(edges)

            if len(edge_coords) < 100:
                return None

            top, left = edge_coords.min(axis=0)
            bottom, right = edge_coords.max(axis=0)

            # Padding 5%
            h, w = gray.shape
            padding = int(min(h, w) * 0.05)

            return (
                max(0, left - padding),
                max(0, top - padding),
                min(w, right + padding),
                min(h, bottom + padding)
            )
        except Exception as e:
            print(f"Error in detect_content_bounds_edge: {e}")
            return None

    def detect_content_region(self, img):
        """
        Combine les deux méthodes de détection.
        Retourne: (bounds, confidence, method)

        Si la détection échoue, retourne l'image entière (pas de crop)
        L'utilisateur peut ajuster manuellement si besoin.
        """
        if not self.auto_crop_enabled:
            w, h = img.size
            return (0, 0, w, h), 1.0, 'disabled'

        w, h = img.size

        # Essayer la méthode par seuil
        bounds_threshold = self.detect_content_bounds(img)

        if bounds_threshold:
            left, top, right, bottom = bounds_threshold
            content_ratio = ((right - left) * (bottom - top)) / (w * h)

            # Vérifier que la zone détectée est raisonnable
            # - Entre 15% et 95% de l'image
            # - Pas trop petite (au moins 100px dans chaque dimension)
            width_ok = (right - left) >= 100
            height_ok = (bottom - top) >= 100

            if 0.15 < content_ratio < 0.95 and width_ok and height_ok:
                return bounds_threshold, 0.9, 'threshold'

        # Fallback: détection par bords (pour space savers blancs)
        bounds_edge = self.detect_content_bounds_edge(img)

        if bounds_edge:
            left, top, right, bottom = bounds_edge
            content_ratio = ((right - left) * (bottom - top)) / (w * h)
            width_ok = (right - left) >= 100
            height_ok = (bottom - top) >= 100

            if 0.15 < content_ratio < 0.95 and width_ok and height_ok:
                return bounds_edge, 0.7, 'edge'

        # Détection incertaine: utiliser l'image entière par défaut
        # L'utilisateur peut ajuster manuellement via le bouton "Ajuster zone"
        return (0, 0, w, h), 0.5, 'full'

    def resize_preserve_aspect(self, img, target_size):
        """Redimensionne en conservant le ratio, avec padding blanc si nécessaire"""
        img_copy = img.copy()
        img_copy.thumbnail(target_size, Image.Resampling.LANCZOS)

        # Créer image de fond blanche
        result = Image.new('RGB', target_size, 'white')

        # Centrer l'image redimensionnée
        offset = ((target_size[0] - img_copy.size[0]) // 2,
                  (target_size[1] - img_copy.size[1]) // 2)
        result.paste(img_copy, offset)

        return result

    def draw_detection_overlay(self, img_display, bounds, original_size, confidence):
        """Dessine le rectangle de la zone détectée sur l'image affichée"""
        img_copy = img_display.copy()
        draw = ImageDraw.Draw(img_copy)

        # Calculer l'échelle
        scale_x = img_display.width / original_size[0]
        scale_y = img_display.height / original_size[1]

        # Convertir les coordonnées
        left = int(bounds[0] * scale_x)
        top = int(bounds[1] * scale_y)
        right = int(bounds[2] * scale_x)
        bottom = int(bounds[3] * scale_y)

        # Couleur selon la confiance
        if confidence >= 0.7:
            color = 'lime'  # Vert = bonne détection
        elif confidence >= 0.5:
            color = 'yellow'  # Jaune = détection moyenne
        else:
            color = 'red'  # Rouge = détection faible

        draw.rectangle([left, top, right, bottom], outline=color, width=3)

        # Afficher la confiance
        label = f"{int(confidence*100)}%"
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()

        # Fond pour le texte
        bbox = draw.textbbox((left + 5, top + 5), label, font=font)
        draw.rectangle([bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2], fill='black')
        draw.text((left + 5, top + 5), label, fill=color, font=font)

        return img_copy

    def open_crop_dialog(self, which_image):
        """Ouvre le dialog de crop manuel pour une image"""
        if which_image == 'original':
            img = self.current_original_img
        else:
            img = self.current_printer_img

        if img is None:
            messagebox.showwarning("Attention", f"Aucune image {which_image} chargée.")
            return

        dialog = CropDialog(self.master, img, f"Crop manuel - {which_image.upper()}")
        self.master.wait_window(dialog)

        if dialog.result:
            if which_image == 'original':
                self.manual_bounds_original = dialog.result
            else:
                self.manual_bounds_printer = dialog.result

            # Recalculer la similarité
            self.show_current_images()

    def reset_manual_crops(self):
        """Réinitialise les crops manuels"""
        self.manual_bounds_original = None
        self.manual_bounds_printer = None
        self.show_current_images()
        messagebox.showinfo("Info", "Les zones de crop manuelles ont été réinitialisées.")

    def update_warning_indicator(self):
        """Met à jour l'indicateur visuel de détection (discret, sans pop-up)"""
        if not self.last_detection or not self.similarity_enabled:
            if hasattr(self, 'crop_button'):
                self.crop_button.config(bg='#17a2b8', text="🔲 Ajuster zone...")
            return

        method = self.last_detection.get('methods', ('', ''))[0]

        if hasattr(self, 'crop_button'):
            if method == 'full':
                # Image entière utilisée - couleur neutre (info seulement)
                self.crop_button.config(bg='#6c757d', text="🔲 Ajuster zone...")
            elif method == 'manual':
                # Crop manuel - couleur verte
                self.crop_button.config(bg='#28a745', text="✓ Zone manuelle")
            else:
                # Détection automatique OK
                self.crop_button.config(bg='#17a2b8', text="🔲 Ajuster zone...")

    # ==================== FIN NOUVELLES FONCTIONS V3 ====================

    def create_placeholder_image(self, text, width=400, height=300):
        """Crée une image placeholder avec du texte"""
        img = Image.new('RGB', (width, height), color='lightgray')
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((width - text_width) // 2, (height - text_height) // 2)

        draw.text(position, text, fill='black', font=font)
        return img

    def setup_startup_ui(self):
        """Interface de démarrage avec drag & drop"""
        for widget in self.master.winfo_children():
            widget.destroy()

        self.master.configure(bg='#f0f0f0')

        title_label = tk.Label(self.master, text=f"PRINTER PROOFREADING v{VERSION}",
                              font=("Arial", 24, "bold"), bg='#f0f0f0', fg='#2649B2')
        title_label.pack(pady=30)

        subtitle_label = tk.Label(self.master, text="Sélectionnez les dossiers pour commencer",
                                 font=("Arial", 14), bg='#f0f0f0', fg='#666666')
        subtitle_label.pack(pady=10)

        # Info sur les nouvelles fonctionnalités V3
        info_label = tk.Label(self.master,
                             text="Nouveautés V3: Détection automatique du contenu + Crop manuel",
                             font=("Arial", 10, "italic"), bg='#f0f0f0', fg='#28a745')
        info_label.pack(pady=5)

        main_frame = tk.Frame(self.master, bg='#f0f0f0')
        main_frame.pack(expand=True, fill='both', padx=50, pady=50)

        self.original_frame = self.create_drop_zone(main_frame, "DOSSIER DESIGN (ORIGINAL)", "original")
        self.original_frame.pack(side='left', expand=True, fill='both', padx=20)

        self.printer_frame = self.create_drop_zone(main_frame, "DOSSIER IMPRIMEUR", "printer")
        self.printer_frame.pack(side='right', expand=True, fill='both', padx=20)

        self.continue_button = tk.Button(self.master, text="COMMENCER L'ANALYSE",
                                        command=self.start_analysis,
                                        font=("Arial", 16, "bold"),
                                        bg='#2649B2', fg='white',
                                        state='disabled', pady=15)
        self.continue_button.pack(pady=30)

        self.update_continue_button()

    def create_drop_zone(self, parent, title, zone_type):
        """Crée une zone de drag & drop"""
        frame = tk.Frame(parent, bg='white', relief='solid', bd=2)

        title_label = tk.Label(frame, text=title, font=("Arial", 16, "bold"),
                              bg='white', fg='#2649B2')
        title_label.pack(pady=20)

        drop_container = tk.Frame(frame, bg='white')
        drop_container.pack(expand=True, fill='both', padx=20, pady=20)

        drop_label = tk.Label(drop_container,
                             text="📁\n\nGlissez le dossier ici\nou cliquez pour sélectionner",
                             font=("Arial", 12),
                             bg='#f8f9fa',
                             fg='#666666',
                             relief='ridge',
                             bd=2,
                             height=8,
                             justify='center',
                             cursor='hand2')
        drop_label.pack(expand=True, fill='both')

        path_label = tk.Label(frame, text="Aucun dossier sélectionné",
                             font=("Arial", 10), bg='white', fg='#999999',
                             wraplength=300)
        path_label.pack(pady=10, padx=20)

        drop_label.drop_target_register(DND_FILES)
        drop_label.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, zone_type, path_label, drop_label))
        drop_label.bind("<Button-1>", lambda e: self.on_click(zone_type, path_label, drop_label))

        return frame

    def on_drop(self, event, zone_type, path_label, drop_label):
        """Gère le drop de dossier"""
        files = self.master.tk.splitlist(event.data)
        if files and os.path.isdir(files[0]):
            self.set_folder(files[0], zone_type, path_label, drop_label)

    def on_click(self, zone_type, path_label, drop_label):
        """Gère le clic pour sélectionner un dossier"""
        folder = filedialog.askdirectory(title=f"Sélectionner le dossier {zone_type}")
        if folder:
            self.set_folder(folder, zone_type, path_label, drop_label)

    def set_folder(self, folder_path, zone_type, path_label, drop_label):
        """Définit le dossier sélectionné"""
        if zone_type == "original":
            self.original_folder = folder_path
        else:
            self.printer_folder = folder_path

        path_label.config(text=f"✓ {os.path.basename(folder_path)}", fg='#28a745')
        drop_label.config(bg='#d4edda',
                         text=f"📁\n\n{os.path.basename(folder_path)}\n\nDossier sélectionné ✓",
                         relief='solid',
                         bd=3)

        self.update_continue_button()

    def update_continue_button(self):
        """Met à jour l'état du bouton continuer"""
        if self.original_folder and self.printer_folder:
            self.continue_button.config(state='normal', bg='#28a745')
        else:
            self.continue_button.config(state='disabled', bg='#6c757d')

    def start_analysis(self):
        """Démarre l'analyse et bascule vers l'interface principale"""
        self.startup_mode = False
        self.setup_main_ui()
        self.load_images()

    def setup_main_ui(self):
        """Interface principale de comparaison"""
        for widget in self.master.winfo_children():
            widget.destroy()

        self.master.configure(bg='SystemButtonFace')

        # Configuration de la grille principale
        self.master.rowconfigure(0, weight=0)  # Barre de similarité
        self.master.rowconfigure(1, weight=3)  # Images
        self.master.rowconfigure(2, weight=0)  # Boutons
        self.master.rowconfigure(3, weight=1)  # Liste
        self.master.columnconfigure(0, weight=1)

        # Barre de similarité en haut
        self.create_similarity_bar()

        # Frame principal pour les images (côte à côte)
        self.images_frame = tk.Frame(self.master)
        self.images_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.images_frame.columnconfigure(0, weight=1)
        self.images_frame.columnconfigure(1, weight=1)
        self.images_frame.rowconfigure(0, weight=1)

        # GAUCHE: Dossier Design (Original)
        self.left_frame = tk.Frame(self.images_frame, relief='solid', bd=1)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        self.left_frame.rowconfigure(1, weight=1)
        self.left_frame.columnconfigure(0, weight=1)

        self.original_folder_label = tk.Label(self.left_frame, text="DOSSIER DESIGN (ORIGINAL)",
                                             font=("Arial", 12, "bold"), bg='#4A74F3', fg='white', pady=8)
        self.original_folder_label.grid(row=0, column=0, sticky="ew")

        self.original_image_label = tk.Label(self.left_frame, bg='white')
        self.original_image_label.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.original_filename_label = tk.Label(self.left_frame, text="",
                                               wraplength=self.master.winfo_width()//2-40,
                                               justify="center", font=("Arial", 9))
        self.original_filename_label.grid(row=2, column=0, sticky="ew", pady=2)

        # Indicateur de page pour Original
        self.original_page_label = tk.Label(self.left_frame, text="",
                                           font=("Arial", 9, "bold"), fg="#666666")
        self.original_page_label.grid(row=3, column=0, sticky="ew", pady=2)

        # DROITE: Dossier Imprimeur
        self.right_frame = tk.Frame(self.images_frame, relief='solid', bd=1)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        self.right_frame.rowconfigure(1, weight=1)
        self.right_frame.columnconfigure(0, weight=1)

        self.printer_folder_label = tk.Label(self.right_frame, text="DOSSIER IMPRIMEUR",
                                            font=("Arial", 12, "bold"), bg='#8E7DE3', fg='white', pady=8)
        self.printer_folder_label.grid(row=0, column=0, sticky="ew")

        self.printer_image_label = tk.Label(self.right_frame, bg='white')
        self.printer_image_label.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.printer_filename_label = tk.Label(self.right_frame, text="",
                                              wraplength=self.master.winfo_width()//2-40,
                                              justify="center", font=("Arial", 9))
        self.printer_filename_label.grid(row=2, column=0, sticky="ew", pady=2)

        # Indicateur de page pour Printer
        self.printer_page_label = tk.Label(self.right_frame, text="",
                                          font=("Arial", 9, "bold"), fg="#666666")
        self.printer_page_label.grid(row=3, column=0, sticky="ew", pady=2)

        # Boutons de navigation et validation
        self.bottom_frame = tk.Frame(self.master)
        self.bottom_frame.grid(row=2, column=0, sticky="ew", padx=10)

        # NOUVEAU V3: Frame de navigation entre pages
        page_nav_frame = tk.Frame(self.bottom_frame)
        page_nav_frame.pack(fill=tk.X, pady=(5, 0))

        self.prev_page_button = tk.Button(page_nav_frame, text="◄ Page préc.",
                                         command=self.show_previous_page,
                                         font=("Arial", 10), width=12,
                                         bg='#6c757d', fg='white')
        self.prev_page_button.pack(side=tk.LEFT, padx=5)

        self.page_indicator_label = tk.Label(page_nav_frame, text="Page 1/1",
                                            font=("Arial", 11, "bold"), fg='#2649B2')
        self.page_indicator_label.pack(side=tk.LEFT, expand=True)

        # Indicateur de validation des pages
        self.page_status_label = tk.Label(page_nav_frame, text="",
                                         font=("Arial", 10), fg='#666666')
        self.page_status_label.pack(side=tk.LEFT, expand=True)

        self.next_page_button = tk.Button(page_nav_frame, text="Page suiv. ►",
                                         command=self.show_next_page,
                                         font=("Arial", 10), width=12,
                                         bg='#6c757d', fg='white')
        self.next_page_button.pack(side=tk.RIGHT, padx=5)

        # Frame de navigation entre PDFs
        button_frame = tk.Frame(self.bottom_frame)
        button_frame.pack(expand=True, fill=tk.X, pady=(10, 0))

        self.prev_button = tk.Button(button_frame, text="<< PDF Précédent", command=self.show_previous,
                                     font=("Arial", 12), width=15)
        self.prev_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # NOUVEAU V3: Bouton pour ajuster les zones
        self.crop_button = tk.Button(button_frame, text="🔲 Ajuster zone...",
                                    command=self.show_crop_menu,
                                    font=("Arial", 10), bg='#17a2b8', fg='white')
        self.crop_button.pack(side=tk.LEFT, padx=5)

        self.next_button = tk.Button(button_frame, text="PDF Suivant >>", command=self.show_next,
                                     font=("Arial", 12), width=15)
        self.next_button.pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)

        validate_frame = tk.Frame(self.bottom_frame)
        validate_frame.pack(expand=True, fill=tk.X)

        self.approve_button = tk.Button(validate_frame, text="✔ Approuver",
                                       command=lambda: self.validate_image(True),
                                       bg="lightgreen", font=("Arial", 12), width=15)
        self.approve_button.pack(side=tk.LEFT, padx=5, pady=(0, 10), expand=True, fill=tk.X)

        self.reject_button = tk.Button(validate_frame, text="✖ Rejeter",
                                      command=lambda: self.validate_image(False),
                                      bg="lightcoral", font=("Arial", 12), width=15)
        self.reject_button.pack(side=tk.RIGHT, padx=5, pady=(0, 10), expand=True, fill=tk.X)

        # Frame pour la liste et les boutons d'export
        list_frame = tk.Frame(self.master)
        list_frame.grid(row=3, column=0, pady=10, sticky="nsew", padx=10)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)

        # Boutons d'export et filtre
        export_frame = tk.Frame(list_frame)
        export_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        self.filter_button = tk.Button(export_frame, text="🔍 Fichiers correspondants",
                                      command=self.toggle_filter,
                                      font=("Arial", 10), bg="#9D5CE6", fg="white")
        self.filter_button.pack(side=tk.LEFT, padx=5)

        self.export_csv_button = tk.Button(export_frame, text="📋 Exporter CSV",
                                          command=self.export_to_csv,
                                          font=("Arial", 10), bg="#4A74F3", fg="white")
        self.export_csv_button.pack(side=tk.LEFT, padx=5)

        self.copy_clipboard_button = tk.Button(export_frame, text="📋 Copier dans le presse-papiers",
                                              command=self.copy_to_clipboard,
                                              font=("Arial", 10), bg="#8E7DE3", fg="white")
        self.copy_clipboard_button.pack(side=tk.LEFT, padx=5)

        self.filter_status_label = tk.Label(export_frame, text="", font=("Arial", 9), fg="#666666")
        self.filter_status_label.pack(side=tk.LEFT, padx=10)

        self.back_button = tk.Button(export_frame, text="🔙 Retour à l'accueil",
                                    command=self.back_to_startup,
                                    font=("Arial", 10), bg="#D4D9F0", fg="black")
        self.back_button.pack(side=tk.RIGHT, padx=5)

        # Liste avec colonnes incluant Similarité
        columns = ('Code Litho', 'Filename', 'Matching', 'Similarity', 'Validation', 'Comment', 'Date')
        self.image_listbox = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)

        for col in columns:
            self.image_listbox.heading(col, text=col)
            if col == 'Code Litho':
                self.image_listbox.column(col, width=100)
            elif col == 'Filename':
                self.image_listbox.column(col, width=180)
            elif col in ['Matching', 'Validation', 'Similarity']:
                self.image_listbox.column(col, width=100)
            elif col == 'Comment':
                self.image_listbox.column(col, width=180)
            else:
                self.image_listbox.column(col, width=130)

        self.image_listbox.grid(row=1, column=0, sticky="nsew")
        self.image_listbox.bind('<<TreeviewSelect>>', self.on_listbox_select)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.image_listbox.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.image_listbox.configure(yscrollcommand=scrollbar.set)

        self.setup_menu()

    def show_crop_menu(self):
        """Affiche le menu pour choisir quelle image ajuster"""
        menu = tk.Menu(self.master, tearoff=0)
        menu.add_command(label="Ajuster Original",
                        command=lambda: self.open_crop_dialog('original'))
        menu.add_command(label="Ajuster Imprimeur",
                        command=lambda: self.open_crop_dialog('printer'))
        menu.add_separator()
        menu.add_command(label="Réinitialiser les crops",
                        command=self.reset_manual_crops)

        # Positionner le menu sous le bouton
        menu.tk_popup(self.crop_button.winfo_rootx(),
                     self.crop_button.winfo_rooty() + self.crop_button.winfo_height())

    def create_similarity_bar(self):
        """Crée la barre de similarité compacte en haut (tout sur une ligne si activé)"""
        # Container principal
        self.similarity_container = tk.Frame(self.master, bg='#2649B2', relief='solid', bd=1)
        self.similarity_container.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        # Tout sur une seule ligne
        main_bar = tk.Frame(self.similarity_container, bg='#2649B2')
        main_bar.pack(fill='x', padx=10, pady=8)

        # GAUCHE: Code Litho
        litho_container = tk.Frame(main_bar, bg='#2649B2')
        litho_container.pack(side='left')

        tk.Label(litho_container, text="Code:", font=("Arial", 10, "bold"),
                bg='#2649B2', fg='white').pack(side='left', padx=(0, 5))

        self.litho_code_label = tk.Label(litho_container, text="", font=("Arial", 12, "bold"),
                                        bg='white', fg='#2649B2', relief='solid', bd=1,
                                        cursor='hand2', padx=6, pady=1)
        self.litho_code_label.pack(side='left')
        self.litho_code_label.bind("<Button-1>", self.copy_litho_code)

        # CENTRE: Barre de similarité (si activée)
        self.similarity_bar_frame = tk.Frame(main_bar, bg='#2649B2')
        self.similarity_bar_frame.pack(side='left', expand=True, fill='x', padx=20)

        # Canvas pour la barre de progression compacte
        self.similarity_canvas = tk.Canvas(self.similarity_bar_frame, height=28, bg='#e9ecef',
                                          highlightthickness=1, highlightbackground='#dee2e6')
        self.similarity_canvas.pack(side='left', expand=True, fill='x')

        # Label du score (à droite de la barre)
        self.similarity_score_label = tk.Label(self.similarity_bar_frame, text="--",
                                              font=("Arial", 11, "bold"), bg='#2649B2',
                                              fg='white', width=12)
        self.similarity_score_label.pack(side='left', padx=(10, 0))

        # Indicateur de détection
        self.detection_label = tk.Label(self.similarity_bar_frame, text="", font=("Arial", 9),
                                       bg='#2649B2', fg='#90EE90', width=15)
        self.detection_label.pack(side='left', padx=5)

        # DROITE: Contrôles
        controls_container = tk.Frame(main_bar, bg='#2649B2')
        controls_container.pack(side='right')

        # Seuil
        tk.Label(controls_container, text="Seuil:", font=("Arial", 9),
                bg='#2649B2', fg='white').pack(side='left', padx=(0, 3))

        self.threshold_scale = tk.Scale(controls_container, from_=0, to=100,
                                       orient='horizontal', length=100,
                                       command=self.update_threshold,
                                       bg='#2649B2', fg='white', highlightthickness=0,
                                       troughcolor='white', showvalue=False)
        self.threshold_scale.set(int(self.similarity_threshold * 100))
        self.threshold_scale.pack(side='left')

        self.threshold_label = tk.Label(controls_container,
                                       text=f"{int(self.similarity_threshold * 100)}%",
                                       font=("Arial", 9, "bold"),
                                       bg='#2649B2', fg='white', width=4)
        self.threshold_label.pack(side='left')

        # Mettre à jour la visibilité selon l'état
        self.update_similarity_bar_visibility()

    def update_similarity_bar_visibility(self):
        """Affiche ou masque la barre de similarité selon l'option"""
        if self.similarity_enabled:
            self.similarity_bar_frame.pack(side='left', expand=True, fill='x', padx=20)
        else:
            self.similarity_bar_frame.pack_forget()

    def toggle_similarity(self):
        """Active/désactive le calcul et l'affichage du score de similarité"""
        self.similarity_enabled = self.similarity_var.get()
        self.update_similarity_bar_visibility()
        self.show_current_images()

    def update_threshold(self, value):
        """Met à jour le seuil de similarité"""
        self.similarity_threshold = float(value) / 100
        self.threshold_label.config(text=f"{int(float(value))}%")
        # Redessine la barre avec le nouveau seuil
        if hasattr(self, 'current_similarity_score'):
            self.draw_similarity_bar(self.current_similarity_score)

    def calculate_similarity(self, img1, img2):
        """V3: Calcule la similarité avec détection de contenu"""
        if img1 is None or img2 is None:
            return 0.0

        try:
            # Utiliser les bounds manuels si définis, sinon auto-détection
            if self.manual_bounds_original:
                bounds1 = self.manual_bounds_original
                conf1, method1 = 1.0, 'manual'
            else:
                bounds1, conf1, method1 = self.detect_content_region(img1)

            if self.manual_bounds_printer:
                bounds2 = self.manual_bounds_printer
                conf2, method2 = 1.0, 'manual'
            else:
                bounds2, conf2, method2 = self.detect_content_region(img2)

            # Stocker pour l'affichage et l'avertissement
            self.last_detection = {
                'bounds1': bounds1, 'bounds2': bounds2,
                'confidence': min(conf1, conf2),
                'conf1': conf1, 'conf2': conf2,
                'methods': (method1, method2)
            }

            # Vérifier si avertissement nécessaire (confiance < 50%)
            self.needs_warning = min(conf1, conf2) < 0.5

            # Recadrer les images
            img1_cropped = img1.crop(bounds1)
            img2_cropped = img2.crop(bounds2)

            # Redimensionner à la même taille
            target_size = (800, 800)
            img1_resized = self.resize_preserve_aspect(img1_cropped, target_size)
            img2_resized = self.resize_preserve_aspect(img2_cropped, target_size)

            # Convertir en niveaux de gris et calculer SSIM
            gray1 = np.array(img1_resized.convert('L'))
            gray2 = np.array(img2_resized.convert('L'))

            score = ssim(gray1, gray2)

            return float(max(0.0, min(1.0, score)))

        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return self._calculate_similarity_basic(img1, img2)

    def _calculate_similarity_basic(self, img1, img2):
        """Fallback: calcul basique sans détection de contenu"""
        try:
            size = (800, 800)
            img1_resized = img1.resize(size, Image.Resampling.LANCZOS)
            img2_resized = img2.resize(size, Image.Resampling.LANCZOS)

            img1_array = np.array(img1_resized.convert('L'))
            img2_array = np.array(img2_resized.convert('L'))

            score = ssim(img1_array, img2_array)

            return max(0.0, min(1.0, score))
        except Exception as e:
            print(f"Error in basic similarity: {e}")
            return 0.0

    def draw_similarity_bar(self, similarity_score):
        """Dessine la barre de similarité compacte avec statut intégré"""
        if not self.similarity_enabled:
            return

        self.current_similarity_score = similarity_score

        # Nettoie le canvas
        self.similarity_canvas.delete("all")

        width = self.similarity_canvas.winfo_width()
        if width <= 1:
            width = 400

        height = 28  # Plus compact

        # Couleur en fonction du seuil
        if similarity_score >= self.similarity_threshold:
            bar_color = "#28a745"  # Vert
            status = "✓"
            status_text = "CONFORME"
        else:
            bar_color = "#dc3545"  # Rouge
            status = "✗"
            status_text = "NON CONFORME"

        # Dessine le fond
        self.similarity_canvas.create_rectangle(0, 0, width, height,
                                               fill='#e9ecef', outline='')

        # Dessine la barre de progression
        progress_width = width * similarity_score
        self.similarity_canvas.create_rectangle(0, 0, progress_width, height,
                                               fill=bar_color, outline='')

        # Dessine la ligne du seuil
        threshold_x = width * self.similarity_threshold
        self.similarity_canvas.create_line(threshold_x, 0, threshold_x, height,
                                          fill='#ffc107', width=2)

        # Texte du pourcentage dans la barre
        percentage_text = f"{int(similarity_score * 100)}% {status}"
        self.similarity_canvas.create_text(width/2, height/2,
                                          text=percentage_text,
                                          font=("Arial", 11, "bold"),
                                          fill='white' if similarity_score > 0.25 else '#333')

        # Met à jour le label compact (juste le statut)
        self.similarity_score_label.config(
            text=status_text,
            fg='#90EE90' if similarity_score >= self.similarity_threshold else '#FF6B6B'
        )

        # Met à jour l'indicateur de détection
        if self.last_detection:
            methods = self.last_detection.get('methods', ('', ''))

            if 'manual' in methods:
                detection_text = "Manuel"
                detection_color = 'white'
            elif 'full' in methods:
                detection_text = "Image entière"
                detection_color = '#AAAAAA'  # Gris clair
            elif 'threshold' in methods or 'edge' in methods:
                detection_text = "Auto"
                detection_color = '#90EE90'  # Vert clair
            else:
                detection_text = ""
                detection_color = 'white'

            self.detection_label.config(text=detection_text, fg=detection_color)

    def copy_litho_code(self, event=None):
        """Copie le code litho dans le presse-papiers"""
        if hasattr(self, 'current_litho_code') and self.current_litho_code:
            self.master.clipboard_clear()
            self.master.clipboard_append(self.current_litho_code)
            messagebox.showinfo("Copié", f"Code litho '{self.current_litho_code}' copié dans le presse-papiers!")

    def on_listbox_select(self, event):
        """Appelé quand une ligne est sélectionnée dans la liste"""
        selection = self.image_listbox.selection()
        if selection:
            item_id = selection[0]
            all_items = self.image_listbox.get_children()
            new_index = all_items.index(item_id)

            if new_index != self.current_index:
                self.current_index = new_index
                self.current_page = 0  # Revenir à la première page
                # Réinitialiser les crops manuels pour la nouvelle paire
                self.manual_bounds_original = None
                self.manual_bounds_printer = None
                self.show_current_images()

    def update_listbox_selection(self):
        """Met à jour la sélection dans la liste pour correspondre à l'index actuel"""
        for item in self.image_listbox.selection():
            self.image_listbox.selection_remove(item)

        filtered_pairs = self.get_filtered_pairs()
        if filtered_pairs:
            all_items = self.image_listbox.get_children()
            if self.current_index < len(all_items):
                current_item = all_items[self.current_index]
                self.image_listbox.selection_add(current_item)
                self.image_listbox.see(current_item)

    def setup_menu(self):
        """Configuration du menu"""
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Nouveau projet", command=self.back_to_startup)
        file_menu.add_separator()
        file_menu.add_command(label="Exporter en CSV", command=self.export_to_csv)
        file_menu.add_command(label="Copier dans le presse-papiers", command=self.copy_to_clipboard)

        filter_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Filtre", menu=filter_menu)
        filter_menu.add_command(label="Tous les fichiers", command=lambda: self.set_filter_mode(False))
        filter_menu.add_command(label="Fichiers correspondants uniquement", command=lambda: self.set_filter_mode(True))

        # NOUVEAU V3: Menu Options
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)

        # Option pour activer/désactiver le score de similarité
        self.similarity_var = tk.BooleanVar(value=self.similarity_enabled)
        options_menu.add_checkbutton(
            label="Activer le score de similarité",
            variable=self.similarity_var,
            command=self.toggle_similarity
        )

        options_menu.add_separator()

        self.auto_crop_var = tk.BooleanVar(value=self.auto_crop_enabled)
        options_menu.add_checkbutton(
            label="Détection auto du contenu",
            variable=self.auto_crop_var,
            command=self.toggle_auto_detection
        )

        self.show_overlay_var = tk.BooleanVar(value=self.show_crop_overlay)
        options_menu.add_checkbutton(
            label="Afficher zone détectée",
            variable=self.show_overlay_var,
            command=self.toggle_overlay
        )

        options_menu.add_separator()
        options_menu.add_command(label="Ajuster zone Original...",
                                command=lambda: self.open_crop_dialog('original'))
        options_menu.add_command(label="Ajuster zone Imprimeur...",
                                command=lambda: self.open_crop_dialog('printer'))
        options_menu.add_separator()
        options_menu.add_command(label="Réinitialiser les crops manuels",
                                command=self.reset_manual_crops)

    def toggle_auto_detection(self):
        """Active/désactive la détection automatique"""
        self.auto_crop_enabled = self.auto_crop_var.get()
        self.show_current_images()

    def toggle_overlay(self):
        """Active/désactive l'affichage de l'overlay"""
        self.show_crop_overlay = self.show_overlay_var.get()
        self.show_current_images()

    def toggle_filter(self):
        """Bascule entre tous les fichiers et fichiers correspondants uniquement"""
        self.show_only_matched = not self.show_only_matched

        if self.show_only_matched:
            self.filter_button.config(text="🔍 Tous les fichiers", bg="#B55CE6")
            matched_count = len([pair for pair in self.image_pairs if pair[0] and pair[1]])
            self.filter_status_label.config(text=f"Affichage: {matched_count} fichier(s) correspondant(s)")
        else:
            self.filter_button.config(text="🔍 Fichiers correspondants", bg="#9D5CE6")
            self.filter_status_label.config(text=f"Affichage: {len(self.image_pairs)} fichier(s) total")

        self.current_index = 0
        self.current_page = 0
        self.manual_bounds_original = None
        self.manual_bounds_printer = None
        self.update_image_list()
        if self.get_filtered_pairs():
            self.show_current_images()

    def get_filtered_pairs(self):
        """Retourne les paires filtrées selon le mode actuel"""
        if self.show_only_matched:
            return [(i, pair) for i, pair in enumerate(self.image_pairs) if pair[0] and pair[1]]
        else:
            return [(i, pair) for i, pair in enumerate(self.image_pairs)]

    def set_filter_mode(self, show_matched_only):
        """Définit le mode de filtre"""
        if self.show_only_matched != show_matched_only:
            self.toggle_filter()

    def back_to_startup(self):
        """Retourne à l'interface de démarrage"""
        self.original_folder = ""
        self.printer_folder = ""
        self.image_pairs = []
        self.current_index = 0
        self.current_page = 0
        self.show_only_matched = False
        self.manual_bounds_original = None
        self.manual_bounds_printer = None
        self.page_validations = {}  # Réinitialiser les validations de pages
        self.startup_mode = True
        self.setup_startup_ui()

    def export_to_csv(self):
        """Exporte le tableau en fichier CSV"""
        if not self.image_pairs:
            messagebox.showwarning("Attention", "Aucune donnée à exporter.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Sauvegarder le rapport"
        )

        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile, delimiter=';')
                    writer.writerow(['Code Litho', 'Filename', 'Matching', 'Similarity', 'Validation', 'Comment', 'Date'])

                    for item_id in self.image_listbox.get_children():
                        item = self.image_listbox.item(item_id)
                        writer.writerow(item['values'])

                messagebox.showinfo("Succès", f"Rapport exporté vers :\n{filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'export :\n{e}")

    def copy_to_clipboard(self):
        """Copie le tableau dans le presse-papiers"""
        if not self.image_pairs:
            messagebox.showwarning("Attention", "Aucune donnée à copier.")
            return

        try:
            output = io.StringIO()
            writer = csv.writer(output, delimiter='\t')
            writer.writerow(['Code Litho', 'Filename', 'Matching', 'Similarity', 'Validation', 'Comment', 'Date'])

            for item_id in self.image_listbox.get_children():
                item = self.image_listbox.item(item_id)
                writer.writerow(item['values'])

            content = output.getvalue()
            self.master.clipboard_clear()
            self.master.clipboard_append(content)

            messagebox.showinfo("Succès", "Données copiées dans le presse-papiers !\nVous pouvez les coller dans Excel ou un autre tableur.")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la copie :\n{e}")

    def load_images(self):
        if not self.original_folder or not self.printer_folder:
            messagebox.showerror("Error", "Please select both folders first.")
            return

        self.image_pairs = []
        original_images = self.find_images(self.original_folder)
        printer_images = self.find_images(self.printer_folder)

        progress_window = tk.Toplevel(self.master)
        progress_window.title("Chargement en cours...")
        progress_window.geometry("400x100")
        progress_window.transient(self.master)
        progress_window.grab_set()

        progress_label = tk.Label(progress_window, text="Analyse des fichiers en cours...")
        progress_label.pack(pady=10)

        progress_bar = ttk.Progressbar(progress_window, mode='determinate', maximum=len(original_images))
        progress_bar.pack(fill=tk.X, padx=20, pady=10)

        for i, image in enumerate(original_images):
            code = self.extract_code(image)
            matching_printer_image = next((img for img in printer_images if self.extract_code(img) == code), None)
            self.image_pairs.append((image, matching_printer_image))
            progress_bar['value'] = i + 1
            progress_window.update_idletasks()

        progress_window.destroy()

        self.update_image_list()
        if self.get_filtered_pairs():
            self.show_current_images()

        self.update_filter_status()

    def update_filter_status(self):
        """Met à jour l'affichage du statut du filtre"""
        if hasattr(self, 'filter_status_label'):
            if self.show_only_matched:
                matched_count = len([pair for pair in self.image_pairs if pair[0] and pair[1]])
                self.filter_status_label.config(text=f"Affichage: {matched_count} fichier(s) correspondant(s)")
            else:
                self.filter_status_label.config(text=f"Affichage: {len(self.image_pairs)} fichier(s) total")

    def find_images(self, folder):
        images = []
        for root, _, files in os.walk(folder):
            for file in files:
                if file.lower().endswith('.pdf'):
                    images.append(os.path.join(root, file))
        return images

    def extract_code(self, filename):
        """Extrait les 8 premiers caractères du nom de fichier"""
        base_name = os.path.basename(filename)
        return base_name[:8] if len(base_name) >= 8 else base_name

    def get_current_litho_code(self):
        """Obtient le code litho pour l'image actuelle"""
        filtered_pairs = self.get_filtered_pairs()
        if filtered_pairs and self.current_index < len(filtered_pairs):
            real_index, (original, printer) = filtered_pairs[self.current_index]
            if original:
                return self.extract_code(original)
            elif printer:
                return self.extract_code(printer)
        return ""

    def update_image_list(self):
        """Met à jour la liste selon le filtre actuel"""
        self.image_listbox.delete(*self.image_listbox.get_children())

        filtered_pairs = self.get_filtered_pairs()
        for i, (real_index, (original, printer)) in enumerate(filtered_pairs):
            filename = os.path.basename(original) if original else os.path.basename(printer)

            litho_code = ""
            if original:
                litho_code = self.extract_code(original)
            elif printer:
                litho_code = self.extract_code(printer)

            if original and printer:
                matching_status = "Both files"
            elif original:
                matching_status = "Original only"
            else:
                matching_status = "Printer only"

            validation_status = "Pending"
            comment = ""
            date = ""
            similarity = "N/A"

            self.image_listbox.insert('', 'end',
                                     values=(litho_code, filename, matching_status,
                                            similarity, validation_status, comment, date),
                                     iid=str(i))

    def show_current_images(self):
        """Affiche les images selon le filtre actuel (avec support multi-pages)"""
        filtered_pairs = self.get_filtered_pairs()
        if not filtered_pairs:
            return

        if self.current_index >= len(filtered_pairs):
            self.current_index = 0

        real_index, (original, printer) = filtered_pairs[self.current_index]

        self.current_litho_code = self.get_current_litho_code()
        self.litho_code_label.config(text=self.current_litho_code)

        self.update_listbox_selection()

        self.master.update_idletasks()
        available_width = (self.master.winfo_width() - 60) // 2
        # Ajuster la hauteur selon si le score est activé ou non
        if self.similarity_enabled:
            available_height = self.master.winfo_height() - 500  # Plus d'espace pour la nav de pages
        else:
            available_height = self.master.winfo_height() - 400

        # S'assurer d'une taille minimum
        available_height = max(250, available_height)
        available_width = max(300, available_width)

        original_img_pil = None
        printer_img_pil = None

        try:
            # Charger l'image Original avec le numéro de page actuel
            if original:
                original_img_pil, self.total_pages_original = self.load_pdf_image(original, self.current_page)
                self.current_original_img = original_img_pil

                if original_img_pil:
                    original_img_display = self.resize_image_to_fit(original_img_pil, available_width, available_height)

                    # V3: Dessiner l'overlay de détection
                    if self.show_crop_overlay and self.auto_crop_enabled:
                        if self.manual_bounds_original:
                            bounds = self.manual_bounds_original
                            conf = 1.0
                        else:
                            bounds, conf, _ = self.detect_content_region(original_img_pil)
                        original_img_display = self.draw_detection_overlay(
                            original_img_display, bounds, original_img_pil.size, conf
                        )

                    original_photo = ImageTk.PhotoImage(original_img_display)
                    self.original_image_label.config(image=original_photo, text="")
                    self.original_image_label.image = original_photo
                    self.original_filename_label.config(text=os.path.basename(original))

                    # Afficher l'indicateur de page pour Original
                    if self.total_pages_original > 1:
                        page_text = f"Page {min(self.current_page + 1, self.total_pages_original)}/{self.total_pages_original}"
                        self.original_page_label.config(text=page_text)
                    else:
                        self.original_page_label.config(text="")
                else:
                    self.total_pages_original = 1
                    self.original_image_label.config(image=None, text="Could not load PDF")
                    self.original_filename_label.config(text="Error loading file")
                    self.original_page_label.config(text="")
            else:
                self.current_original_img = None
                self.total_pages_original = 1
                placeholder_img = self.create_placeholder_image("No Original File", available_width, available_height)
                placeholder_photo = ImageTk.PhotoImage(placeholder_img)
                self.original_image_label.config(image=placeholder_photo, text="")
                self.original_image_label.image = placeholder_photo
                self.original_filename_label.config(text="No original file found")
                self.original_page_label.config(text="")

            # Charger l'image Printer avec le numéro de page actuel
            if printer:
                printer_img_pil, self.total_pages_printer = self.load_pdf_image(printer, self.current_page)
                self.current_printer_img = printer_img_pil

                if printer_img_pil:
                    printer_img_display = self.resize_image_to_fit(printer_img_pil, available_width, available_height)

                    # V3: Dessiner l'overlay de détection
                    if self.show_crop_overlay and self.auto_crop_enabled:
                        if self.manual_bounds_printer:
                            bounds = self.manual_bounds_printer
                            conf = 1.0
                        else:
                            bounds, conf, _ = self.detect_content_region(printer_img_pil)
                        printer_img_display = self.draw_detection_overlay(
                            printer_img_display, bounds, printer_img_pil.size, conf
                        )

                    printer_photo = ImageTk.PhotoImage(printer_img_display)
                    self.printer_image_label.config(image=printer_photo, text="")
                    self.printer_image_label.image = printer_photo
                    self.printer_filename_label.config(text=os.path.basename(printer))

                    # Afficher l'indicateur de page pour Printer
                    if self.total_pages_printer > 1:
                        page_text = f"Page {min(self.current_page + 1, self.total_pages_printer)}/{self.total_pages_printer}"
                        self.printer_page_label.config(text=page_text)
                    else:
                        self.printer_page_label.config(text="")
                else:
                    self.total_pages_printer = 1
                    self.printer_image_label.config(image=None, text="Could not load PDF")
                    self.printer_filename_label.config(text="Error loading file")
                    self.printer_page_label.config(text="")
            else:
                self.current_printer_img = None
                self.total_pages_printer = 1
                placeholder_img = self.create_placeholder_image("No Printer File", available_width, available_height)
                placeholder_photo = ImageTk.PhotoImage(placeholder_img)
                self.printer_image_label.config(image=placeholder_photo, text="")
                self.printer_image_label.image = placeholder_photo
                self.printer_filename_label.config(text="No printer file found")
                self.printer_page_label.config(text="")

            # Mettre à jour la navigation des pages
            self.update_page_navigation()

            # Calcule et affiche la similarité
            if original_img_pil and printer_img_pil:
                similarity_score = self.calculate_similarity(original_img_pil, printer_img_pil)
                self.draw_similarity_bar(similarity_score)

                # Met à jour la liste avec le score de similarité (pour la page actuelle)
                current_item = self.image_listbox.get_children()[self.current_index]
                current_values = list(self.image_listbox.item(current_item)['values'])
                # Si multi-pages, indiquer que c'est le score de la page actuelle
                max_pages = self.get_max_pages()
                if max_pages > 1:
                    current_values[3] = f"{int(similarity_score * 100)}% (p.{self.current_page + 1})"
                else:
                    current_values[3] = f"{int(similarity_score * 100)}%"
                self.image_listbox.item(current_item, values=current_values)

                # V3: Mettre à jour l'indicateur visuel (sans pop-up)
                self.update_warning_indicator()
            else:
                self.draw_similarity_bar(0.0)
                self.similarity_score_label.config(text="Similarité: N/A (fichier manquant)")
                self.detection_label.config(text="")

        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {e}")

    def resize_image_to_fit(self, img, max_width, max_height):
        original_width, original_height = img.size
        width_ratio = max_width / original_width
        height_ratio = max_height / original_height
        ratio = min(width_ratio, height_ratio)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def load_pdf_image(self, pdf_path, page_number=0):
        """
        Charge une page spécifique d'un PDF.

        Args:
            pdf_path: Chemin vers le fichier PDF
            page_number: Numéro de la page (0-indexed)

        Returns:
            tuple: (image PIL, nombre total de pages) ou (None, 0) en cas d'erreur
        """
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)

            if page_number >= total_pages:
                page_number = 0

            page = doc.load_page(page_number)
            # V3: Utilise une résolution 2x pour une meilleure qualité
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            return img, total_pages
        except Exception as e:
            print(f"Error loading PDF {pdf_path}: {e}")
            return None, 0

    def get_pdf_page_count(self, pdf_path):
        """Retourne le nombre de pages d'un PDF"""
        try:
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except:
            return 1

    def get_max_pages(self):
        """Retourne le nombre maximum de pages entre les deux PDFs"""
        return max(self.total_pages_original, self.total_pages_printer)

    def show_previous_page(self):
        """Affiche la page précédente du PDF actuel"""
        if self.current_page > 0:
            self.current_page -= 1
            # Réinitialiser les crops manuels pour la nouvelle page
            self.manual_bounds_original = None
            self.manual_bounds_printer = None
            self.show_current_images()

    def show_next_page(self):
        """Affiche la page suivante du PDF actuel"""
        max_pages = self.get_max_pages()
        if self.current_page < max_pages - 1:
            self.current_page += 1
            # Réinitialiser les crops manuels pour la nouvelle page
            self.manual_bounds_original = None
            self.manual_bounds_printer = None
            self.show_current_images()

    def update_page_navigation(self):
        """Met à jour l'état des boutons et indicateurs de navigation de pages"""
        max_pages = self.get_max_pages()

        # Mettre à jour l'indicateur de page
        self.page_indicator_label.config(text=f"Page {self.current_page + 1}/{max_pages}")

        # Mettre à jour l'état des boutons
        self.prev_page_button.config(state='normal' if self.current_page > 0 else 'disabled')
        self.next_page_button.config(state='normal' if self.current_page < max_pages - 1 else 'disabled')

        # Masquer/afficher les contrôles de page selon le nombre de pages
        if max_pages <= 1:
            self.prev_page_button.config(state='disabled')
            self.next_page_button.config(state='disabled')

        # Mettre à jour le statut de validation des pages
        self.update_page_validation_status()

    def update_page_validation_status(self):
        """Met à jour l'indicateur de statut des pages validées"""
        max_pages = self.get_max_pages()
        if max_pages <= 1:
            self.page_status_label.config(text="")
            return

        # Compter les pages validées pour ce PDF
        validated_count = 0
        for page in range(max_pages):
            key = (self.current_index, page)
            if key in self.page_validations and self.page_validations[key] is not None:
                validated_count += 1

        if validated_count == max_pages:
            self.page_status_label.config(text=f"✓ Toutes les pages validées ({validated_count}/{max_pages})",
                                         fg='#28a745')
        elif validated_count > 0:
            self.page_status_label.config(text=f"⚠ {validated_count}/{max_pages} pages validées",
                                         fg='#ffc107')
        else:
            self.page_status_label.config(text=f"○ 0/{max_pages} pages validées",
                                         fg='#6c757d')

    def show_previous(self):
        """Navigation vers le PDF précédent"""
        if self.current_index > 0:
            self.current_index -= 1
            self.current_page = 0  # Revenir à la première page
            # Réinitialiser les crops manuels pour la nouvelle paire
            self.manual_bounds_original = None
            self.manual_bounds_printer = None
            self.show_current_images()

    def show_next(self):
        """Navigation vers le PDF suivant"""
        filtered_pairs = self.get_filtered_pairs()
        if self.current_index < len(filtered_pairs) - 1:
            self.current_index += 1
            self.current_page = 0  # Revenir à la première page
            # Réinitialiser les crops manuels pour la nouvelle paire
            self.manual_bounds_original = None
            self.manual_bounds_printer = None
            self.show_current_images()

    def validate_image(self, approved):
        """Validation de la page actuelle (support multi-pages)"""
        filtered_pairs = self.get_filtered_pairs()
        if not filtered_pairs:
            return

        max_pages = self.get_max_pages()
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if approved:
            validation_status = "Approved"
            comment = ""
        else:
            comment = simpledialog.askstring("Reject Comment", "Enter a comment for rejection:")
            if comment is None:
                return
            validation_status = "Rejected"

        # Enregistrer la validation de cette page
        page_key = (self.current_index, self.current_page)
        self.page_validations[page_key] = validation_status

        # Vérifier si toutes les pages sont validées
        all_pages_validated = True
        any_rejected = False
        for page in range(max_pages):
            key = (self.current_index, page)
            if key not in self.page_validations or self.page_validations[key] is None:
                all_pages_validated = False
            elif self.page_validations[key] == "Rejected":
                any_rejected = True

        # Déterminer le statut global du PDF
        if all_pages_validated:
            if any_rejected:
                global_status = "Rejected"
                global_bg_color = "lightcoral"
            else:
                global_status = "Approved"
                global_bg_color = "lightgreen"
        else:
            # Pas toutes les pages validées encore
            global_status = f"Pending ({self.count_validated_pages()}/{max_pages})"
            global_bg_color = "#FFF3CD"  # Jaune clair

        # Mettre à jour la liste
        current_item = self.image_listbox.item(self.image_listbox.get_children()[self.current_index])
        litho_code = current_item['values'][0]
        filename = current_item['values'][1]
        matching_status = current_item['values'][2]
        similarity = current_item['values'][3]

        self.image_listbox.item(self.image_listbox.get_children()[self.current_index],
                               values=(litho_code, filename, matching_status, similarity,
                                      global_status, comment, date))

        self.image_listbox.tag_configure(global_status, background=global_bg_color)
        self.image_listbox.item(self.image_listbox.get_children()[self.current_index],
                               tags=(global_status,))

        # Mettre à jour l'indicateur de pages validées
        self.update_page_validation_status()

        # Navigation: page suivante ou PDF suivant si toutes pages validées
        if max_pages > 1 and self.current_page < max_pages - 1:
            # Il reste des pages à valider, aller à la page suivante
            self.show_next_page()
        elif all_pages_validated:
            # Toutes les pages sont validées, aller au PDF suivant
            self.show_next()
        else:
            # Il reste des pages non validées, aller à la première page non validée
            self.go_to_first_unvalidated_page()

    def count_validated_pages(self):
        """Compte le nombre de pages validées pour le PDF actuel"""
        max_pages = self.get_max_pages()
        count = 0
        for page in range(max_pages):
            key = (self.current_index, page)
            if key in self.page_validations and self.page_validations[key] is not None:
                count += 1
        return count

    def go_to_first_unvalidated_page(self):
        """Va à la première page non encore validée"""
        max_pages = self.get_max_pages()
        for page in range(max_pages):
            key = (self.current_index, page)
            if key not in self.page_validations or self.page_validations[key] is None:
                self.current_page = page
                self.manual_bounds_original = None
                self.manual_bounds_printer = None
                self.show_current_images()
                return
        # Si toutes les pages sont validées, rester sur la page actuelle
        self.show_current_images()


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ImageComparator(root)
    root.mainloop()
