import tkinter as tk
from tkinter import ttk, messagebox
from email_scraper.database import DatabaseManager
from email_scraper.script import GmailManager, JOB_KEYWORDS, JOB_RELATED_KEYWORDS


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

        ttk.Button(button_frame, text="get new emails", command=self.fetch_new_emails).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="refresh", command=self.load_emails).pack(
            side=tk.LEFT, padx=5
        )

        # filter + search row
        filter_frame = ttk.Frame(main_frame)
        filter_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))

        ttk.Label(filter_frame, text="filter by label:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_label_var = tk.StringVar(value="all")
        self.filter_label_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_label_var,
            state="readonly",
            width=15,
        )
        # "all" + the same label categories used in classification
        self.filter_label_combo["values"] = ("all",) + tuple(JOB_KEYWORDS.keys())
        self.filter_label_combo.current(0)
        self.filter_label_combo.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(filter_frame, text="search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(filter_frame, text="apply", command=self.load_emails).pack(
            side=tk.LEFT, padx=(5, 0)
        )

        # email list
        self.tree = ttk.Treeview(
            main_frame,
            columns=("Date", "Subject", "Sender", "Label"),
            show="headings",
        )
        self.tree.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.tree.heading("Date", text="date")
        self.tree.heading("Subject", text="subject")
        self.tree.heading("Sender", text="sender")
        self.tree.heading("Label", text="label")

        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=2, column=2, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)

        # actions
        action_frame = ttk.LabelFrame(main_frame, text="actions", padding="5")
        action_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))

        label_frame = ttk.Frame(action_frame)
        label_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        ttk.Label(label_frame, text="label:").grid(row=0, column=0, padx=5)
        self.label_var = tk.StringVar()
        label_combo = ttk.Combobox(label_frame, textvariable=self.label_var)
        label_combo["values"] = tuple(JOB_KEYWORDS.keys())
        label_combo.grid(row=0, column=1, padx=5)
        ttk.Button(label_frame, text="update label", command=self.update_label).grid(
            row=0, column=2, padx=5
        )

        delete_frame = ttk.Frame(action_frame)
        delete_frame.grid(row=0, column=1, padx=20, pady=5, sticky=tk.E)
        ttk.Button(
            delete_frame,
            text="delete from database",
            command=self.delete_emails,
            style="Delete.TButton",
        ).grid(row=0, column=0, padx=5)

        self.root.style = ttk.Style()
        self.root.style.configure("Delete.TButton", foreground="red")

        # resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)  # row with the treeview

        # stats
        stats_frame = ttk.LabelFrame(main_frame, text="stats", padding="5")
        stats_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))

        self.stats_text = tk.Text(stats_frame, height=8, width=50)
        self.stats_text.grid(row=0, column=0, padx=5, pady=5)
        self.stats_text.config(state="disabled")

        self.update_statistics()

    def delete_emails(self):
        # deletes emails ONLY from the database not the actual inbox*
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("selection required", "please select an email to delete")
            return

        # confirm before deleting
        count = len(selected_items)
        confirm = messagebox.askyesno(
            "confirm deletion",
            f"are you sure you want to delete {count} email{'s' if count > 1 else ''} from the database?\n\n"
            + "this will only remove them from your tracking database, not from your Gmail inbox.",
        )

        if not confirm:
            return

        deleted_count = 0
        for item in selected_items:
            email_id = self.tree.item(item)["tags"][0]
            if self.db.delete_email(email_id):
                deleted_count += 1

        self.load_emails()
        messagebox.showinfo(
            "deletion complete",
            f"removed {deleted_count} email{'s' if deleted_count > 1 else ''} from database",
        )

    def update_statistics(self):
        stats = self.db.get_statistics()
        if not stats:
            return

        pipeline = stats.get("pipeline", {})
        apps = pipeline.get("applications", 0)
        interviews = pipeline.get("interviews", 0)
        offers = pipeline.get("offers", 0)

        resp_rate = f"{(interviews / apps * 100):.1f}%" if apps else "n/a"
        offer_rate = f"{(offers / apps * 100):.1f}%" if apps else "n/a"

        stats_str = ""
        stats_str += f"total tracked emails: {stats['total']}\n"
        stats_str += f"received in last 7 days: {stats['recent']}\n\n"

        stats_str += "by label:\n"
        for label, count in stats["by_label"]:
            stats_str += f"  • {label}: {count}\n"

        stats_str += "\npipeline (approx):\n"
        stats_str += f"  • applications: {apps}\n"
        stats_str += f"  • interviews:   {interviews}\n"
        stats_str += f"  • offers:       {offers}\n"
        stats_str += f"  • response rate (interviews / apps): {resp_rate}\n"
        stats_str += f"  • offer rate (offers / apps):        {offer_rate}\n"

        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert("1.0", stats_str)
        self.stats_text.config(state="disabled")

    def load_emails(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        # read filters if they exist
        label_filter = getattr(self, "filter_label_var", None)
        search_text = getattr(self, "search_var", None)

        label_value = label_filter.get() if label_filter else None
        search_value = search_text.get().strip() if search_text else None

        # fetch from DB
        if label_value or search_value:
            emails = self.db.get_emails(label=label_value, search=search_value)
        else:
            emails = self.db.get_all_emails()

        for email in emails:
            email_id, subject, sender, received_date, label = email
            self.tree.insert(
                "",
                "end",
                values=(
                    received_date.strftime("%Y-%m-%d %H:%M"),
                    subject,
                    sender,
                    label,
                ),
                tags=(str(email_id),),
            )

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
            email_id = self.tree.item(item)["tags"][0]
            if self.db.update_email_label(email_id, new_label):
                self.tree.set(item, "Label", new_label)

        self.update_statistics()

    def fetch_new_emails(self):
        if not self.gmail.service and not self.gmail.authenticate():
            messagebox.showerror("authentication error", "failed to authenticate with Gmail")
            return

        try:
            new_emails = self.gmail.fetch_emails()
            new_emails_count = 0

            for email in new_emails:
                message_id = email.get("message_id", None)
                if self.db.insert_email(
                    email["subject"],
                    email["sender"],
                    email["received_date"],
                    email["label"],
                    message_id,
                ):
                    new_emails_count += 1

            messagebox.showinfo("complete", f"added {new_emails_count} new emails")
            self.load_emails()
        except Exception as e:
            messagebox.showerror("error", f"error grabbing emails: {e}")


def main():
    root = tk.Tk()
    app = JobSearchGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
