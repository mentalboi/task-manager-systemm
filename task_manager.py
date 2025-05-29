import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime
import pystray
from PIL import Image, ImageDraw
import threading
import os
from plyer import notification

class TaskManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Homework/Project Task Manager")
        self.root.geometry("500x600")  # Made taller for new buttons
        self.root.protocol('WM_DELETE_WINDOW', self.hide_window)
        self.setup_gui()
        self.create_db()
        self.setup_tray()
        
    def setup_gui(self):
        # Add some styling
        self.root.configure(bg='#f0f0f0')
        title_frame = tk.Frame(self.root, bg='#f0f0f0')
        title_frame.pack(pady=10)

        tk.Label(title_frame, text="📚 Task Manager", font=('Arial', 16, 'bold'), bg='#f0f0f0').pack()

        input_frame = tk.Frame(self.root, bg='#f0f0f0')
        input_frame.pack(pady=5)

        tk.Label(input_frame, text="Title:", bg='#f0f0f0').pack()
        self.entry_title = tk.Entry(input_frame, width=50)
        self.entry_title.pack()

        tk.Label(input_frame, text="Description:", bg='#f0f0f0').pack()
        self.entry_desc = tk.Entry(input_frame, width=50)
        self.entry_desc.pack()

        tk.Label(input_frame, text="Due Date (YYYY-MM-DD HH:MM):", bg='#f0f0f0').pack()
        self.entry_due = tk.Entry(input_frame, width=50)
        self.entry_due.pack()

        tk.Button(self.root, text="Add Task", command=self.add_task, bg='#4CAF50', fg='white', padx=20).pack(pady=10)

        tk.Label(self.root, text="Your Tasks:", font=('Arial', 12, 'bold'), bg='#f0f0f0').pack()
        self.listbox_tasks = tk.Listbox(self.root, width=70, height=10, selectmode=tk.SINGLE)
        self.listbox_tasks.pack(pady=10)

        # Buttons frame
        buttons_frame = tk.Frame(self.root, bg='#f0f0f0')
        buttons_frame.pack(pady=5)

        # Mark as Completed button
        tk.Button(
            buttons_frame,
            text="✓ Mark as Completed",
            command=self.mark_task_completed,
            bg='#4CAF50',
            fg='white',
            padx=10
        ).pack(side=tk.LEFT, padx=5)

        # Delete Completed Tasks button
        tk.Button(
            buttons_frame,
            text="🗑 Delete Completed Tasks",
            command=self.delete_completed_tasks,
            bg='#ff6b6b',
            fg='white',
            padx=10
        ).pack(side=tk.LEFT, padx=5)

        # Legend frame
        legend_frame = tk.Frame(self.root, bg='#f0f0f0')
        legend_frame.pack(pady=5)
        tk.Label(legend_frame, text="🔴 Overdue", bg='#f0f0f0').pack(side=tk.LEFT, padx=5)
        tk.Label(legend_frame, text="🟡 Pending", bg='#f0f0f0').pack(side=tk.LEFT, padx=5)
        tk.Label(legend_frame, text="🟢 Completed", bg='#f0f0f0').pack(side=tk.LEFT, padx=5)

    def create_db(self):
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            description TEXT,
                            due_date TEXT NOT NULL,
                            status TEXT DEFAULT 'pending',
                            last_reminder TIMESTAMP
                        )''')
        conn.commit()
        conn.close()

    def add_task(self):
        title = self.entry_title.get()
        desc = self.entry_desc.get()
        due = self.entry_due.get()

        if not title or not due:
            messagebox.showwarning("Input Error", "Title and Due Date are required!")
            return

        try:
            try:
                datetime.strptime(due, "%Y-%m-%d %H:%M")
            except ValueError:
                datetime.strptime(due, "%Y-%m-%d")
                due = due + " 23:59"
        except ValueError:
            messagebox.showerror("Date Error", "Enter due date in YYYY-MM-DD or YYYY-MM-DD HH:MM format!")
            return

        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (title, description, due_date, status) VALUES (?, ?, ?, 'pending')",
                    (title, desc, due))
        conn.commit()
        conn.close()

        self.entry_title.delete(0, tk.END)
        self.entry_desc.delete(0, tk.END)
        self.entry_due.delete(0, tk.END)

        messagebox.showinfo("Success", "Task added successfully!")
        self.show_tasks()
        self.check_overdue()

    def show_tasks(self):
        self.listbox_tasks.delete(0, tk.END)
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, due_date, status FROM tasks ORDER BY due_date")
        rows = cursor.fetchall()
        
        # Store task IDs for later reference
        self.task_ids = [row[0] for row in rows]
        
        for row in rows:
            status_symbol = "🔴" if row[3] == 'overdue' else "🟡" if row[3] == 'pending' else "🟢"
            self.listbox_tasks.insert(tk.END, f"{status_symbol} {row[1]} - Due: {row[2]}")
        conn.close()

    def mark_task_completed(self):
        selection = self.listbox_tasks.curselection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select a task to mark as completed!")
            return
            
        task_idx = selection[0]
        task_id = self.task_ids[task_idx]
        
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Success", "Task marked as completed!")
        self.show_tasks()

    def delete_completed_tasks(self):
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
        count = cursor.fetchone()[0]
        
        if count == 0:
            messagebox.showinfo("No Tasks", "No completed tasks to delete!")
            conn.close()
            return
            
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {count} completed task(s)?"):
            cursor.execute("DELETE FROM tasks WHERE status = 'completed'")
            conn.commit()
            messagebox.showinfo("Success", f"{count} completed task(s) deleted!")
            self.show_tasks()
            
        conn.close()

    def check_overdue(self):
        import notify_module
        notify_module.check_and_notify()

    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), 'white')
        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, 56, 56], outline='black', width=2)
        draw.line([32, 32, 32, 16], fill='black', width=2)
        draw.line([32, 32, 44, 32], fill='black', width=2)
        return image

    def setup_tray(self):
        menu = (
            pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Check Tasks", self.check_overdue),
            pystray.MenuItem("Exit", self.quit_window)
        )
        self.icon = pystray.Icon("task_manager", self.create_tray_icon(), "Task Manager", menu)
        self.tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.tray_thread.start()

    def show_window(self, icon=None, item=None):
        self.icon.visible = True
        self.root.deiconify()
        self.show_tasks()

    def hide_window(self):
        self.root.withdraw()
        if self.icon is not None:
            self.icon.visible = True
            notification.notify(
                title="Task Manager",
                message="Task Manager is still running in the background",
                timeout=3
            )

    def quit_window(self, icon=None, item=None):
        if self.icon is not None:
            self.icon.stop()
        self.root.quit()

    def run(self):
        import reminder_bar
        reminder_bar.start_reminder_bar()
        self.show_tasks()
        self.check_overdue()
        self.root.mainloop()

if __name__ == "__main__":
    app = TaskManager()
    app.run()

