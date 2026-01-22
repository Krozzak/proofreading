import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk, ImageDraw, ImageFont
import datetime
import fitz  # PyMuPDF
import csv
import io


class ImageComparator:
    def __init__(self, master):
        self.master = master
        self.master.title("PRINTER PROOFREADING")
        self.master.geometry("1600x1200")

        self.original_folder = ""
        self.printer_folder = ""
        self.image_pairs = []
        self.current_index = 0
        self.show_only_matched = False  # NOUVEAU: État du filtre
        
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
        # Nettoie l'interface existante
        for widget in self.master.winfo_children():
            widget.destroy()

        self.master.configure(bg='#f0f0f0')
        
        # Titre principal
        title_label = tk.Label(self.master, text="PRINTER PROOFREADING", 
                              font=("Arial", 24, "bold"), bg='#f0f0f0', fg='#2649B2')
        title_label.pack(pady=30)

        subtitle_label = tk.Label(self.master, text="Sélectionnez les dossiers pour commencer", 
                                 font=("Arial", 14), bg='#f0f0f0', fg='#666666')
        subtitle_label.pack(pady=10)

        # Frame principal pour les zones de drop
        main_frame = tk.Frame(self.master, bg='#f0f0f0')
        main_frame.pack(expand=True, fill='both', padx=50, pady=50)

        # Zone pour dossier original
        self.original_frame = self.create_drop_zone(main_frame, "DOSSIER ORIGINAL", "original")
        self.original_frame.pack(side='left', expand=True, fill='both', padx=20)

        # Zone pour dossier imprimeur
        self.printer_frame = self.create_drop_zone(main_frame, "DOSSIER IMPRIMEUR", "printer")
        self.printer_frame.pack(side='right', expand=True, fill='both', padx=20)

        # Bouton pour continuer (désactivé au début)
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
        
        # Titre de la zone
        title_label = tk.Label(frame, text=title, font=("Arial", 16, "bold"), 
                              bg='white', fg='#2649B2')
        title_label.pack(pady=20)

        # Frame conteneur pour la zone de drop avec effet pointillé
        drop_container = tk.Frame(frame, bg='white')
        drop_container.pack(expand=True, fill='both', padx=20, pady=20)

        # Zone de drop avec bordure simulée
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

        # Label pour afficher le chemin sélectionné
        path_label = tk.Label(frame, text="Aucun dossier sélectionné", 
                             font=("Arial", 10), bg='white', fg='#999999',
                             wraplength=300)
        path_label.pack(pady=10, padx=20)

        # Configuration du drag & drop
        drop_label.drop_target_register(DND_FILES)
        drop_label.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, zone_type, path_label, drop_label))
        
        # Configuration du clic
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

        # Met à jour l'affichage
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
        # Nettoie l'interface de démarrage
        for widget in self.master.winfo_children():
            widget.destroy()

        self.master.configure(bg='SystemButtonFace')
        
        self.master.rowconfigure(0, weight=2)
        self.master.rowconfigure(1, weight=0)
        self.master.rowconfigure(2, weight=1)
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)

        # Images en haut
        self.top_frame = tk.Frame(self.master)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Frame pour le code litho en haut
        self.litho_frame = tk.Frame(self.top_frame, bg='#2649B2', relief='solid', bd=2)
        self.litho_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        tk.Label(self.litho_frame, text="Code Litho:", font=("Arial", 12, "bold"), 
                bg='#2649B2', fg='white').pack(side='left', padx=10, pady=5)
        
        self.litho_code_label = tk.Label(self.litho_frame, text="", font=("Arial", 14, "bold"), 
                                        bg='white', fg='#2649B2', relief='solid', bd=1, 
                                        cursor='hand2', padx=10, pady=2)
        self.litho_code_label.pack(side='left', padx=5, pady=5)
        self.litho_code_label.bind("<Button-1>", self.copy_litho_code)
        
        tk.Label(self.litho_frame, text="(Cliquer pour copier)", font=("Arial", 9), 
                bg='#2649B2', fg='white').pack(side='left', padx=5, pady=5)

        # Labels et images
        self.original_folder_label = tk.Label(self.top_frame, text="Dossier Original", font=("Arial", 10))
        self.original_folder_label.grid(row=1, column=0, sticky="n")
        
        self.original_image_label = tk.Label(self.top_frame)
        self.original_image_label.grid(row=2, column=0, sticky="nsew")
        
        self.original_filename_label = tk.Label(self.top_frame, text="", wraplength=self.master.winfo_width()//2 -20, justify="center")
        self.original_filename_label.grid(row=3, column=0, sticky="n")
        
        self.printer_folder_label = tk.Label(self.top_frame, text="Dossier Imprimeur", font=("Arial", 10))
        self.printer_folder_label.grid(row=4, column=0, sticky="n")
        
        self.printer_image_label = tk.Label(self.top_frame)
        self.printer_image_label.grid(row=5, column=0, sticky="nsew")
        
        self.printer_filename_label = tk.Label(self.top_frame, text="", wraplength=self.master.winfo_width()//2 -20, justify="center")
        self.printer_filename_label.grid(row=6, column=0, sticky="n")

        self.top_frame.columnconfigure(0, weight=1)
        self.top_frame.rowconfigure(2, weight=1)  # Pour l'image originale
        self.top_frame.rowconfigure(5, weight=1)  # Pour l'image imprimeur

        # Boutons de navigation et validation
        self.bottom_frame = tk.Frame(self.master)
        self.bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        button_frame = tk.Frame(self.bottom_frame)
        button_frame.pack(expand=True, fill=tk.X, pady=(10, 0))

        self.prev_button = tk.Button(button_frame, text="<< Précédent", command=self.show_previous, font=("Arial", 12), width=15)
        self.prev_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.next_button = tk.Button(button_frame, text="Suivant >>", command=self.show_next, font=("Arial", 12), width=15)
        self.next_button.pack(side=tk.RIGHT, padx=5, expand=True, fill=tk.X)

        validate_frame = tk.Frame(self.bottom_frame)
        validate_frame.pack(expand=True, fill=tk.X)

        self.approve_button = tk.Button(validate_frame, text="✔ Approuver", command=lambda: self.validate_image(True), bg="lightgreen", font=("Arial", 12), width=15)
        self.approve_button.pack(side=tk.LEFT, padx=5, pady=(0, 10), expand=True, fill=tk.X)

        self.reject_button = tk.Button(validate_frame, text="✖ Rejeter", command=lambda: self.validate_image(False), bg="lightcoral", font=("Arial", 12), width=15)
        self.reject_button.pack(side=tk.RIGHT, padx=5, pady=(0, 10), expand=True, fill=tk.X)

        # Frame pour la liste et les boutons d'export
        list_frame = tk.Frame(self.master)
        list_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Boutons d'export et filtre
        export_frame = tk.Frame(list_frame)
        export_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        # NOUVEAU: Bouton de filtre
        self.filter_button = tk.Button(export_frame, text="🔍 Fichiers correspondants", 
                                      command=self.toggle_filter, 
                                      font=("Arial", 10), bg="#9D5CE6", fg="white")
        self.filter_button.pack(side=tk.LEFT, padx=5)

        self.export_csv_button = tk.Button(export_frame, text="📋 Exporter CSV", command=self.export_to_csv, 
                                          font=("Arial", 10), bg="#4A74F3", fg="white")
        self.export_csv_button.pack(side=tk.LEFT, padx=5)

        self.copy_clipboard_button = tk.Button(export_frame, text="📋 Copier dans le presse-papiers", command=self.copy_to_clipboard, 
                                              font=("Arial", 10), bg="#8E7DE3", fg="white")
        self.copy_clipboard_button.pack(side=tk.LEFT, padx=5)

        # NOUVEAU: Label pour afficher le statut du filtre
        self.filter_status_label = tk.Label(export_frame, text="", font=("Arial", 9), fg="#666666")
        self.filter_status_label.pack(side=tk.LEFT, padx=10)

        self.back_button = tk.Button(export_frame, text="🔙 Retour à l'accueil", command=self.back_to_startup, 
                                    font=("Arial", 10), bg="#D4D9F0", fg="black")
        self.back_button.pack(side=tk.RIGHT, padx=5)

        # Liste avec colonnes incluant Code Litho
        columns = ('Code Litho', 'Filename', 'Matching', 'Validation', 'Comment', 'Date')
        self.image_listbox = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.image_listbox.heading(col, text=col)
            if col == 'Code Litho':
                self.image_listbox.column(col, width=100)
            elif col == 'Filename':
                self.image_listbox.column(col, width=200)
            elif col in ['Matching', 'Validation']:
                self.image_listbox.column(col, width=100)
            elif col == 'Comment':
                self.image_listbox.column(col, width=200)
            else:
                self.image_listbox.column(col, width=150)

        self.image_listbox.grid(row=1, column=0, sticky="nsew")

        # Binding pour cliquer sur une ligne
        self.image_listbox.bind('<<TreeviewSelect>>', self.on_listbox_select)

        # Scrollbar pour la liste
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.image_listbox.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.image_listbox.configure(yscrollcommand=scrollbar.set)

        # Menu
        self.setup_menu()

    def toggle_filter(self):
        """NOUVEAU: Bascule entre tous les fichiers et fichiers correspondants uniquement"""
        self.show_only_matched = not self.show_only_matched
        
        if self.show_only_matched:
            self.filter_button.config(text="🔍 Tous les fichiers", bg="#B55CE6")
            matched_count = len([pair for pair in self.image_pairs if pair[0] and pair[1]])
            self.filter_status_label.config(text=f"Affichage: {matched_count} fichier(s) correspondant(s)")
        else:
            self.filter_button.config(text="🔍 Fichiers correspondants", bg="#9D5CE6")
            self.filter_status_label.config(text=f"Affichage: {len(self.image_pairs)} fichier(s) total")
        
        # Réinitialise l'index et met à jour l'affichage
        self.current_index = 0
        self.update_image_list()
        if self.get_filtered_pairs():
            self.show_current_images()

    def get_filtered_pairs(self):
        """NOUVEAU: Retourne les paires filtrées selon le mode actuel"""
        if self.show_only_matched:
            return [(i, pair) for i, pair in enumerate(self.image_pairs) if pair[0] and pair[1]]
        else:
            return [(i, pair) for i, pair in enumerate(self.image_pairs)]

    def get_current_filtered_index(self):
        """NOUVEAU: Obtient l'index réel dans les paires filtrées"""
        filtered_pairs = self.get_filtered_pairs()
        if self.current_index < len(filtered_pairs):
            return filtered_pairs[self.current_index][0]  # Index réel dans image_pairs
        return 0

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
            # Obtient l'index de l'élément sélectionné dans la liste filtrée
            all_items = self.image_listbox.get_children()
            new_index = all_items.index(item_id)
            
            if new_index != self.current_index:
                self.current_index = new_index
                self.show_current_images()

    def update_listbox_selection(self):
        """Met à jour la sélection dans la liste pour correspondre à l'index actuel"""
        # Désélectionne tout
        for item in self.image_listbox.selection():
            self.image_listbox.selection_remove(item)
        
        # Sélectionne l'élément actuel
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

        # NOUVEAU: Menu filtre
        filter_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Filtre", menu=filter_menu)
        filter_menu.add_command(label="Tous les fichiers", command=lambda: self.set_filter_mode(False))
        filter_menu.add_command(label="Fichiers correspondants uniquement", command=lambda: self.set_filter_mode(True))

    def set_filter_mode(self, show_matched_only):
        """NOUVEAU: Définit le mode de filtre"""
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
                    
                    # En-têtes
                    writer.writerow(['Code Litho', 'Filename', 'Matching', 'Validation', 'Comment', 'Date'])
                    
                    # Données (toujours exporter tout, pas seulement les filtrés)
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
            # Créer le contenu texte
            output = io.StringIO()
            writer = csv.writer(output, delimiter='\t')
            
            # En-têtes
            writer.writerow(['Code Litho', 'Filename', 'Matching', 'Validation', 'Comment', 'Date'])
            
            # Données
            for item_id in self.image_listbox.get_children():
                item = self.image_listbox.item(item_id)
                writer.writerow(item['values'])
            
            # Copier dans le presse-papiers
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

        # Barre de progression
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

        # NOUVEAU: Met à jour le statut du filtre
        self.update_filter_status()

    def update_filter_status(self):
        """NOUVEAU: Met à jour l'affichage du statut du filtre"""
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
        """MODIFIÉ: Met à jour la liste selon le filtre actuel"""
        self.image_listbox.delete(*self.image_listbox.get_children())
        
        filtered_pairs = self.get_filtered_pairs()
        for i, (real_index, (original, printer)) in enumerate(filtered_pairs):
            filename = os.path.basename(original) if original else os.path.basename(printer)
            
            # Extrait le code litho
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

            # Inclut le code litho dans les valeurs
            self.image_listbox.insert('', 'end', values=(litho_code, filename, matching_status, validation_status, comment, date), iid=str(i))
    
    def show_current_images(self):
        """MODIFIÉ: Affiche les images selon le filtre actuel"""
        filtered_pairs = self.get_filtered_pairs()
        if not filtered_pairs:
            return

        if self.current_index >= len(filtered_pairs):
            self.current_index = 0

        real_index, (original, printer) = filtered_pairs[self.current_index]

        # Met à jour le code litho affiché
        self.current_litho_code = self.get_current_litho_code()
        self.litho_code_label.config(text=self.current_litho_code)

        # Met à jour la sélection dans la liste
        self.update_listbox_selection()

        self.master.update_idletasks()
        available_width = self.master.winfo_width() - 40
        available_height = (self.master.winfo_height() - 350) // 2

        try:
            if original:
                original_img = self.load_pdf_image(original)
                if original_img:
                    original_img = self.resize_image_to_fit(original_img, available_width, available_height)
                    original_photo = ImageTk.PhotoImage(original_img)
                    self.original_image_label.config(image=original_photo, text="")
                    self.original_image_label.image = original_photo
                    self.original_filename_label.config(text=os.path.basename(original))
                else:
                    self.original_image_label.config(image=None, text="Could not load PDF")
                    self.original_filename_label.config(text="Error loading file")
            else:
                placeholder_img = self.create_placeholder_image("No Original File", available_width//2, available_height)
                placeholder_photo = ImageTk.PhotoImage(placeholder_img)
                self.original_image_label.config(image=placeholder_photo, text="")
                self.original_image_label.image = placeholder_photo
                self.original_filename_label.config(text="No original file found")

            if printer:
                printer_img = self.load_pdf_image(printer)
                if printer_img:
                    printer_img = self.resize_image_to_fit(printer_img, available_width, available_height)
                    printer_photo = ImageTk.PhotoImage(printer_img)
                    self.printer_image_label.config(image=printer_photo, text="")
                    self.printer_image_label.image = printer_photo
                    self.printer_filename_label.config(text=os.path.basename(printer))
                else:
                    self.printer_image_label.config(image=None, text="Could not load PDF")
                    self.printer_filename_label.config(text="Error loading file")
            else:
                placeholder_img = self.create_placeholder_image("No Printer File", available_width//2, available_height)
                placeholder_photo = ImageTk.PhotoImage(placeholder_img)
                self.printer_image_label.config(image=placeholder_photo, text="")
                self.printer_image_label.image = placeholder_photo
                self.printer_filename_label.config(text="No printer file found")

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
        """MODIFIÉ: Navigation selon le filtre actuel"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_images()

    def show_next(self):
        """MODIFIÉ: Navigation selon le filtre actuel"""
        filtered_pairs = self.get_filtered_pairs()
        if self.current_index < len(filtered_pairs) - 1:
            self.current_index += 1
            self.show_current_images()

    def validate_image(self, approved):
        """MODIFIÉ: Validation selon le filtre actuel"""
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

        # Utilise la nouvelle structure avec Code Litho
        litho_code = current_item['values'][0]
        filename = current_item['values'][1]
        matching_status = current_item['values'][2]
        
        self.image_listbox.item(self.image_listbox.get_children()[self.current_index], 
                               values=(litho_code, filename, matching_status, validation_status, comment, date))

        self.image_listbox.tag_configure(validation_status, background=bg_color)
        self.image_listbox.item(self.image_listbox.get_children()[self.current_index], tags=(validation_status,))

        self.show_next()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ImageComparator(root)
    root.mainloop()