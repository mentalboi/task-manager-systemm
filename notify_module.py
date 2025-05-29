# notify_module.py
import sqlite3
from datetime import datetime
from plyer import notification
import tkinter as tk
from tkinter import ttk

def check_and_notify():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute("""
        SELECT id, title, due_date 
        FROM tasks 
        WHERE status = 'pending' OR status = 'overdue'
    """)
    tasks = cursor.fetchall()
    
    overdue = []
    for task_id, title, due in tasks:
        try:
            due_datetime = datetime.strptime(due, "%Y-%m-%d %H:%M")
            if due_datetime < now:
                overdue.append((task_id, title, due))
                # Update status to overdue
                cursor.execute("UPDATE tasks SET status = 'overdue' WHERE id = ?", (task_id,))
        except ValueError:
            continue

    conn.commit()
    conn.close()

    if overdue:
        show_overdue_alert(overdue)

def show_overdue_alert(overdue_tasks):
    # System notification
    notification.notify(
        title="❗ URGENT: Overdue Tasks",
        message=f"You have {len(overdue_tasks)} overdue task(s)!\nPlease check them immediately!",
        timeout=0  # Stay until clicked
    )
    
    # Create detailed popup window
    root = tk.Tk()
    root.title("⚠️ Overdue Tasks Alert")
    root.geometry("500x400+200+200")
    root.configure(bg="#ffebeb")
    root.attributes("-topmost", True)
    
    # Header
    header_frame = tk.Frame(root, bg="#ffebeb")
    header_frame.pack(fill="x", pady=20)
    
    warning_label = tk.Label(
        header_frame,
        text="⚠️ ATTENTION: OVERDUE TASKS ⚠️",
        font=("Arial", 16, "bold"),
        fg="#cc0000",
        bg="#ffebeb"
    )
    warning_label.pack()
    
    sub_text = tk.Label(
        header_frame,
        text="The following tasks need immediate attention:",
        font=("Arial", 12),
        bg="#ffebeb"
    )
    sub_text.pack(pady=10)
    
    # Create scrollable frame for tasks
    container = ttk.Frame(root)
    canvas = tk.Canvas(container, bg="#ffebeb")
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Add tasks to scrollable frame
    for task_id, title, due in overdue_tasks:
        task_frame = tk.Frame(scrollable_frame, bg="#ffe0e0", relief="raised", borderwidth=1)
        task_frame.pack(fill="x", padx=10, pady=5)
        
        days_overdue = (datetime.now() - datetime.strptime(due, "%Y-%m-%d %H:%M")).days
        
        task_title = tk.Label(
            task_frame,
            text=f"📌 {title}",
            font=("Arial", 11, "bold"),
            bg="#ffe0e0",
            wraplength=400,
            justify="left"
        )
        task_title.pack(anchor="w", padx=10, pady=(5,0))
        
        due_text = tk.Label(
            task_frame,
            text=f"Due date: {due}\nOverdue by: {days_overdue} days",
            font=("Arial", 10),
            bg="#ffe0e0",
            fg="#cc0000"
        )
        due_text.pack(anchor="w", padx=10, pady=(0,5))
    
    container.pack(fill="both", expand=True, padx=10, pady=10)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Add close button
    close_btn = tk.Button(
        root,
        text="I Will Handle These Tasks Now",
        command=root.destroy,
        bg="#cc0000",
        fg="white",
        font=("Arial", 10, "bold"),
        padx=20,
        pady=5
    )
    close_btn.pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    check_and_notify()
