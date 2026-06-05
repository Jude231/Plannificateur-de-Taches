import tkinter as tk
from tkinter import ttk, messagebox
from crontab import CronTab
import json
import os

# Fichier pour sauvegarder les tâches
TASKS_FILE = "tasks_data.json"

class TaskSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Planificateur de Tâches (Bash & Python)")
        self.root.geometry("650x450")
        self.root.minsize(550, 350)
        
        # Style général
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Chargement des tâches
        self.tasks = self.load_tasks()
        
        self.create_widgets()
        self.refresh_task_list()

    def create_widgets(self):
        # --- Zone de saisie ---
        input_frame = ttk.LabelFrame(self.root, text=" Ajouter une nouvelle tâche ", padding=15)
        input_frame.pack(fill="x", padx=15, pady=15, side="top")
        
        # Nom de la tâche
        ttk.Label(input_frame, text="Commande / Nom :").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.task_name_entry = ttk.Entry(input_frame, width=30)
        self.task_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Intervalle
        ttk.Label(input_frame, text="Intervalle :").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.interval_combo = ttk.Combobox(input_frame, values=["Toutes les heures", "Quotidien", "Hebdomadaire"], state="readonly", width=15)
        self.interval_combo.current(1) # Par défaut : Quotidien
        self.interval_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # Bouton Ajouter
        add_btn = ttk.Button(input_frame, text="Ajouter", command=self.add_task)
        add_btn.grid(row=0, column=4, padx=10, pady=5)
        
        input_frame.columnconfigure(1, weight=1)

        # --- Liste des tâches (Milieu) ---
        list_frame = ttk.LabelFrame(self.root, text=" Tâches planifiées ", padding=15)
        list_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Tableau (Treeview)
        columns = ("id", "task", "interval")
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        
        # Définition des entêtes
        self.task_tree.heading("id", text="ID")
        self.task_tree.heading("task", text="Commande / Tâche")
        self.task_tree.heading("interval", text="Intervalle")
        
        # Configuration des colonnes
        self.task_tree.column("id", width=50, minwidth=50, anchor="center")
        self.task_tree.column("task", width=350, minwidth=200, anchor="w")
        self.task_tree.column("interval", width=150, minwidth=100, anchor="center")
        
        # Barre de défilement (Scrollbar)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        self.task_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Actions ---
        action_frame = ttk.Frame(self.root, padding=10)
        action_frame.pack(fill="x", padx=15, side="bottom")
        
        # Bouton Supprimer
        delete_btn = ttk.Button(action_frame, text="Supprimer la tâche sélectionnée", command=self.delete_task)
        delete_btn.pack(side="left")
        
        # Bouton Quitter
        quit_btn = ttk.Button(action_frame, text="Quitter", command=self.root.quit)
        quit_btn.pack(side="right")

    
    
    def load_tasks(self):
        """Lit les vraies tâches cron de l'utilisateur actuel."""
        cron = CronTab(user=True)
        tasks_list = []
        #filtre / récupère les tâches gérées par notre application
        for job in cron:
            # (commentaire) pour identifier nos tâches
            if job.comment and job.comment.startswith("BashCronPy_"):
                tasks_list.append({
                    "name": job.command,
                    "interval": job.comment.split("_")[1]
                })
        return tasks_list

    def save_tasks(self):
        """Sauvegarde les tâches dans le fichier JSON."""
        try:
            with open(TASKS_FILE, "w") as f:
                json.dump(self.tasks, f, indent=4)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder les tâches : {e}")

    def refresh_task_list(self):
        """Met à jour l'affichage de la liste des tâches."""
        
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        
        for idx, task in enumerate(self.tasks, start=1):
            self.task_tree.insert("", "end", values=(idx, task["name"], task["interval"]))

    def add_task(self):
        """Ajoute une vraie tâche dans la crontab."""
        task_name = self.task_name_entry.get().strip()
        interval = self.interval_combo.get()
        
        if not task_name:
            messagebox.showwarning("Saisie incomplète", "Veuillez entrer une commande.")
            return
            
        cron = CronTab(user=True)
        # Création d'un nouveau tache 
        job = cron.new(command=task_name, comment=f"BashCronPy_{interval}")
        
        # timing du cron selon le choix de l'Utilisateur
        if interval == "Toutes les heures":
            job.minute.on(0)  
        elif interval == "Quotidien":
            job.every_day()
        elif interval == "Hebdomadaire":
            job.every_week()
        # Sauvegarde dans la crontab
        cron.write() 
        #rafraîchissement de la liste
        self.tasks = self.load_tasks()
        self.refresh_task_list()
        self.task_name_entry.delete(0, tk.END)
        

    def delete_task(self):
        """Supprime la tâche sélectionnée de la crontab."""
        selected_item = self.task_tree.selection()
        if not selected_item:
            messagebox.showwarning("Sélection requise", "Sélectionnez une tâche.")
            return
            
        item_values = self.task_tree.item(selected_item, "values")
        task_name = item_values[1]
        interval = item_values[2]
        
        confirm = messagebox.askyesno("Confirmation", f"Supprimer la tâche : '{task_name}' ?")
        if confirm:
            cron = CronTab(user=True)
            # Recherche et suppression du tache correspondant exact
            for job in cron:
                if job.command == task_name and job.comment == f"BashCronPy_{interval}":
                    cron.remove(job)
                    break
            
            # Sauvegarde des modifications dans la crontab
            cron.write()
            
            # Rafraîchir l'interface
            self.tasks = self.load_tasks()
            self.refresh_task_list()
if __name__ == "__main__":
    root = tk.Tk()
    app = TaskSchedulerApp(root)
    root.mainloop()
