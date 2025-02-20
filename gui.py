import tkinter as tk
from tkinter import ttk, messagebox
from database import DatabaseManager
from script import GmailManager, JOB_KEYWORDS

class JobSearchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("job application tracker")
        self.db = DatabaseManager()
        self.gmail = GmailManager()
        self.setup_gui()
        self.load_emails()

    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="get new emails", command=self.fetch_new_emails).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="refresh", command=self.load_emails).pack(side=tk.LEFT, padx=5)

        # email list
        self.tree = ttk.Treeview(main_frame, columns=('Date', 'Subject', 'Sender', 'Label'), show='headings')
        self.tree.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.tree.heading('Date', text='date')
        self.tree.heading('Subject', text='subject')
        self.tree.heading('Sender', text='sender')
        self.tree.heading('Label', text='label')

        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)

        label_frame = ttk.LabelFrame(main_frame, text="modify label", padding="5")
        label_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        self.label_var = tk.StringVar()
        label_combo = ttk.Combobox(label_frame, textvariable=self.label_var)
        label_combo['values'] = tuple(JOB_KEYWORDS.keys())
        label_combo.grid(row=0, column=0, padx=5)

        ttk.Button(label_frame, text="update label", command=self.update_label).grid(row=0, column=1, padx=5)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        stats_frame = ttk.LabelFrame(main_frame, text="stats", padding="5")
        stats_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        self.stats_text = tk.Text(stats_frame, height=6, width=40)
        self.stats_text.grid(row=0, column=0, padx=5, pady=5)
        self.stats_text.config(state='disabled')
        
        self.update_statistics()
        
    def update_statistics(self):
        stats = self.db.get_statistics()
        if not stats:
            return
            
        stats_str = f"📊 total: {stats['total']}\n"
        stats_str += f"📥 last week: {stats['recent']}\n\n"
        stats_str += "📌 overall:\n"
        for label, count in stats['by_label']:
            stats_str += f"  • {label}: {count}\n"
            
        self.stats_text.config(state='normal')
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.insert('1.0', stats_str)
        self.stats_text.config(state='disabled')

    def load_emails(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        emails = self.db.get_all_emails()
        for email in emails:
            email_id, subject, sender, received_date, label = email
            self.tree.insert('', 'end', values=(
                received_date.strftime('%Y-%m-%d %H:%M'),
                subject,
                sender,
                label
            ), tags=(str(email_id),))
            self.update_statistics()

    def update_label(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("selection required", "please select an email to update")
            return

        new_label = self.label_var.get()
        if not new_label:
            messagebox.showwarning("label required", "please select a label")
            return

        for item in selected_items:
            email_id = self.tree.item(item)['tags'][0]
            if self.db.update_email_label(email_id, new_label):
                self.tree.set(item, 'Label', new_label)

    def fetch_new_emails(self):
        if not self.gmail.service and not self.gmail.authenticate():
            messagebox.showerror("authentication error", "failed to authenticate with Gmail")
            return

        try:
            new_emails = self.gmail.fetch_emails()
            new_emails_count = 0

            for email in new_emails:
                if self.db.insert_email(
                    email['subject'],
                    email['sender'],
                    email['received_date'],
                    email['label']
                ):
                    new_emails_count += 1

            messagebox.showinfo("complete", f"added {new_emails_count} new emails")
            self.load_emails()
            self.update_statistics()
        except Exception as e:
            messagebox.showerror("Error", f"error grabbing emails: {e}")

def main():
    root = tk.Tk()
    app = JobSearchGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()