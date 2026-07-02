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
import numpy as np

class ImageComparator:
    def __init__(self, master):
        self.master = master
        self.master.title("PRINTER PROOFREADING")
        self.master.geometry("1600x1200")

        self.original_folder = ""
        self.printer_folder = ""
        self.image_pairs = []
        self.current_index = 0
        self.show_only_matched = False
        self.similarity_threshold = 0.85  # Seuil par défaut (85%)
        
        # État de l'interface
        self.startup_mode = True

        self.setup_startup_ui()

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
        
        title_label = tk.Label(self.master, text="PRINTER PROOFREADING", 
                              font=("Arial", 24, "bold"), bg='#f0f0f0', fg='#2649B2')
        title_label.pack(pady=30)

        subtitle_label = tk.Label(self.master, text="Sélectionnez les dossiers pour commencer", 
                                 font=("Arial", 14), bg='#f0f0f0', fg='#666666')
        subtitle_label.pack(pady=10)

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
        """Interface principale de comparaison - MODIFIÉ pour côte à côte"""
        for widget in self.master.winfo_children():
            widget.destroy()

        self.master.configure(bg='SystemButtonFace')
        
        # Configuration de la grille principale
        self.master.rowconfigure(0, weight=0)  # Barre de similarité
        self.master.rowconfigure(1, weight=3)  # Images
        self.master.rowconfigure(2, weight=0)  # Boutons
        self.master.rowconfigure(3, weight=1)  # Liste
        self.master.columnconfigure(0, weight=1)

        # NOUVEAU: Barre de similarité en haut
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
        self.original_filename_label.grid(row=2, column=0, sticky="ew", pady=5)

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
        self.printer_filename_label.grid(row=2, column=0, sticky="ew", pady=5)

        # Boutons de navigation et validation
        self.bottom_frame = tk.Frame(self.master)
        self.bottom_frame.grid(row=2, column=0, sticky="ew", padx=10)

        button_frame = tk.Frame(self.bottom_frame)
        button_frame.pack(expand=True, fill=tk.X, pady=(10, 0))

        self.prev_button = tk.Button(button_frame, text="<< Précédent", command=self.show_previous, 
                                     font=("Arial", 12), width=15)
        self.prev_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.next_button = tk.Button(button_frame, text="Suivant >>", command=self.show_next, 
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

    def create_similarity_bar(self):
        """NOUVEAU: Crée la barre de similarité en haut"""
        similarity_container = tk.Frame(self.master, bg='#f0f0f0', relief='solid', bd=2)
        similarity_container.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # Frame pour le code litho et contrôles
        top_bar = tk.Frame(similarity_container, bg='#2649B2', height=40)
        top_bar.pack(fill='x')

        # Code Litho à gauche
        litho_container = tk.Frame(top_bar, bg='#2649B2')
        litho_container.pack(side='left', padx=10, pady=5)
        
        tk.Label(litho_container, text="Code Litho:", font=("Arial", 11, "bold"), 
                bg='#2649B2', fg='white').pack(side='left', padx=(0, 5))
        
        self.litho_code_label = tk.Label(litho_container, text="", font=("Arial", 13, "bold"), 
                                        bg='white', fg='#2649B2', relief='solid', bd=1, 
                                        cursor='hand2', padx=8, pady=2)
        self.litho_code_label.pack(side='left')
        self.litho_code_label.bind("<Button-1>", self.copy_litho_code)

        # Contrôle du seuil à droite
        threshold_container = tk.Frame(top_bar, bg='#2649B2')
        threshold_container.pack(side='right', padx=10, pady=5)
        
        tk.Label(threshold_container, text="Seuil:", font=("Arial", 10, "bold"), 
                bg='#2649B2', fg='white').pack(side='left', padx=(0, 5))
        
        self.threshold_scale = tk.Scale(threshold_container, from_=0, to=100, 
                                       orient='horizontal', length=150,
                                       command=self.update_threshold,
                                       bg='#2649B2', fg='white', highlightthickness=0,
                                       troughcolor='white')
        self.threshold_scale.set(int(self.similarity_threshold * 100))
        self.threshold_scale.pack(side='left', padx=5)
        
        self.threshold_label = tk.Label(threshold_container, 
                                       text=f"{int(self.similarity_threshold * 100)}%", 
                                       font=("Arial", 10, "bold"), 
                                       bg='#2649B2', fg='white', width=5)
        self.threshold_label.pack(side='left')

        # Barre de similarité
        similarity_bar_frame = tk.Frame(similarity_container, bg='white', height=60)
        similarity_bar_frame.pack(fill='x', padx=10, pady=10)

        # Canvas pour la barre de progression
        self.similarity_canvas = tk.Canvas(similarity_bar_frame, height=40, bg='white', 
                                          highlightthickness=0)
        self.similarity_canvas.pack(fill='x', pady=5)

        # Label pour le score
        self.similarity_score_label = tk.Label(similarity_bar_frame, text="Similarité: --", 
                                              font=("Arial", 14, "bold"), bg='white')
        self.similarity_score_label.pack()

    def update_threshold(self, value):
        """NOUVEAU: Met à jour le seuil de similarité"""
        self.similarity_threshold = float(value) / 100
        self.threshold_label.config(text=f"{int(float(value))}%")
        # Redessine la barre avec le nouveau seuil
        if hasattr(self, 'current_similarity_score'):
            self.draw_similarity_bar(self.current_similarity_score)

    def calculate_similarity(self, img1, img2):
        """NOUVEAU: Calcule la similarité entre deux images"""
        if img1 is None or img2 is None:
            return 0.0

        try:
            # Redimensionne les images à la même taille
            size = (800, 800)
            img1_resized = img1.resize(size, Image.Resampling.LANCZOS)
            img2_resized = img2.resize(size, Image.Resampling.LANCZOS)

            # Convertit en numpy arrays
            img1_array = np.array(img1_resized.convert('L'))  # Grayscale
            img2_array = np.array(img2_resized.convert('L'))

            # Calcule SSIM (Structural Similarity Index)
            score, _ = ssim(img1_array, img2_array, full=True)
            
            return max(0.0, min(1.0, score))  # Assure que le score est entre 0 et 1

        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0

    def draw_similarity_bar(self, similarity_score):
        """NOUVEAU: Dessine la barre de similarité avec code couleur"""
        self.current_similarity_score = similarity_score
        
        # Nettoie le canvas
        self.similarity_canvas.delete("all")
        
        width = self.similarity_canvas.winfo_width()
        if width <= 1:  # Canvas pas encore initialisé
            width = 800
            
        height = 40
        
        # Couleur en fonction du seuil
        if similarity_score >= self.similarity_threshold:
            bar_color = "#28a745"  # Vert
            text_color = "#28a745"
            status = "✓ CONFORME"
        else:
            bar_color = "#dc3545"  # Rouge
            text_color = "#dc3545"
            status = "✗ NON CONFORME"
        
        # Dessine le fond
        self.similarity_canvas.create_rectangle(0, 0, width, height, 
                                               fill='#e9ecef', outline='#dee2e6')
        
        # Dessine la barre de progression
        progress_width = width * similarity_score
        self.similarity_canvas.create_rectangle(0, 0, progress_width, height, 
                                               fill=bar_color, outline='')
        
        # Dessine la ligne du seuil
        threshold_x = width * self.similarity_threshold
        self.similarity_canvas.create_line(threshold_x, 0, threshold_x, height, 
                                          fill='#ffc107', width=3, dash=(5, 3))
        
        # Texte du pourcentage
        percentage_text = f"{int(similarity_score * 100)}%"
        self.similarity_canvas.create_text(width/2, height/2, 
                                          text=percentage_text, 
                                          font=("Arial", 16, "bold"), 
                                          fill='white' if similarity_score > 0.3 else '#333')
        
        # Met à jour le label
        self.similarity_score_label.config(
            text=f"Similarité: {int(similarity_score * 100)}% - {status}",
            fg=text_color
        )

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
        self.show_only_matched = False
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
        """Affiche les images selon le filtre actuel"""
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
        available_height = self.master.winfo_height() - 500

        original_img_pil = None
        printer_img_pil = None

        try:
            if original:
                original_img_pil = self.load_pdf_image(original)
                if original_img_pil:
                    original_img_display = self.resize_image_to_fit(original_img_pil, available_width, available_height)
                    original_photo = ImageTk.PhotoImage(original_img_display)
                    self.original_image_label.config(image=original_photo, text="")
                    self.original_image_label.image = original_photo
                    self.original_filename_label.config(text=os.path.basename(original))
                else:
                    self.original_image_label.config(image=None, text="Could not load PDF")
                    self.original_filename_label.config(text="Error loading file")
            else:
                placeholder_img = self.create_placeholder_image("No Original File", available_width, available_height)
                placeholder_photo = ImageTk.PhotoImage(placeholder_img)
                self.original_image_label.config(image=placeholder_photo, text="")
                self.original_image_label.image = placeholder_photo
                self.original_filename_label.config(text="No original file found")

            if printer:
                printer_img_pil = self.load_pdf_image(printer)
                if printer_img_pil:
                    printer_img_display = self.resize_image_to_fit(printer_img_pil, available_width, available_height)
                    printer_photo = ImageTk.PhotoImage(printer_img_display)
                    self.printer_image_label.config(image=printer_photo, text="")
                    self.printer_image_label.image = printer_photo
                    self.printer_filename_label.config(text=os.path.basename(printer))
                else:
                    self.printer_image_label.config(image=None, text="Could not load PDF")
                    self.printer_filename_label.config(text="Error loading file")
            else:
                placeholder_img = self.create_placeholder_image("No Printer File", available_width, available_height)
                placeholder_photo = ImageTk.PhotoImage(placeholder_img)
                self.printer_image_label.config(image=placeholder_photo, text="")
                self.printer_image_label.image = placeholder_photo
                self.printer_filename_label.config(text="No printer file found")

            # NOUVEAU: Calcule et affiche la similarité
            if original_img_pil and printer_img_pil:
                similarity_score = self.calculate_similarity(original_img_pil, printer_img_pil)
                self.draw_similarity_bar(similarity_score)
                
                # Met à jour la liste avec le score de similarité
                current_item = self.image_listbox.get_children()[self.current_index]
                current_values = list(self.image_listbox.item(current_item)['values'])
                current_values[3] = f"{int(similarity_score * 100)}%"
                self.image_listbox.item(current_item, values=current_values)
            else:
                self.draw_similarity_bar(0.0)
                self.similarity_score_label.config(text="Similarité: N/A (fichier manquant)")

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
         
    def load_pdf_image(self, pdf_path):
        try:
            doc = fitz.open(pdf_path)
            page = doc.load_page(0)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            return img
        except Exception as e:
            print(f"Error loading PDF {pdf_path}: {e}")
            return None

    def show_previous(self):
        """Navigation selon le filtre actuel"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_images()

    def show_next(self):
        """Navigation selon le filtre actuel"""
        filtered_pairs = self.get_filtered_pairs()
        if self.current_index < len(filtered_pairs) - 1:
            self.current_index += 1
            self.show_current_images()

    def validate_image(self, approved):
        """Validation selon le filtre actuel"""
        filtered_pairs = self.get_filtered_pairs()
        if not filtered_pairs:
            return

        current_item = self.image_listbox.item(self.image_listbox.get_children()[self.current_index])
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if approved:
            validation_status = "Approved"
            bg_color = "lightgreen"
            comment = ""
        else:
            comment = simpledialog.askstring("Reject Comment", "Enter a comment for rejection:")
            if comment is None:
                return
            validation_status = "Rejected"
            bg_color = "lightcoral"

        litho_code = current_item['values'][0]
        filename = current_item['values'][1]
        matching_status = current_item['values'][2]
        similarity = current_item['values'][3]
        
        self.image_listbox.item(self.image_listbox.get_children()[self.current_index], 
                               values=(litho_code, filename, matching_status, similarity, 
                                      validation_status, comment, date))

        self.image_listbox.tag_configure(validation_status, background=bg_color)
        self.image_listbox.item(self.image_listbox.get_children()[self.current_index], 
                               tags=(validation_status,))

        self.show_next()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ImageComparator(root)
    root.mainloop()