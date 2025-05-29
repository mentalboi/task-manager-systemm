# task_widget.py
import tkinter as tk
from datetime import datetime
import sqlite3

def fetch_tasks():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute("SELECT title, due_date FROM tasks ORDER BY due_date ASC")
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def update_widget(widget_frame, label_list):
    tasks = fetch_tasks()
    today = datetime.today().date()

    for label in label_list:
        label.destroy()
    label_list.clear()

    for i, (title, due) in enumerate(tasks[:5]):  # Show top 5 tasks
        due_date = datetime.strptime(due, "%Y-%m-%d").date()
        overdue = due_date < today
        text = f"{title} - Due: {due}"

        lbl = tk.Label(widget_frame, text=text, fg="red" if overdue else "black", anchor='w')
        lbl.pack(fill='x')
        label_list.append(lbl)

def launch_widget():
    widget = tk.Tk()
    widget.title("Task Widget")
    widget.geometry("300x180")
    widget.resizable(False, False)
    widget.attributes("-topmost", True)

    frame = tk.Frame(widget)
    frame.pack(padx=10, pady=10, fill='both', expand=True)


    header = tk.Label(frame, text="Upcoming Tasks", font=('Arial', 12, 'bold'))
    header.pack()

    label_list = []

    def refresh():
        update_widget(frame, label_list)
        widget.after(60000, refresh)  # Refresh every 60 seconds

    refresh()
    widget.mainloop()

if __name__ == "__main__":
    launch_widget()
