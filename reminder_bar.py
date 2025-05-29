# reminder_bar.py
import tkinter as tk
from datetime import datetime, timedelta
import sqlite3
import threading
import time
from plyer import notification

REMINDER_INTERVALS = [
    timedelta(days=1),     # 1 day before
    timedelta(hours=2),    # 2 hours before
    timedelta(minutes=30)  # 30 minutes before
]

def fetch_tasks_needing_reminder():
    now = datetime.now()
    
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, due_date, last_reminder 
        FROM tasks 
        WHERE status = 'pending'
    """)
    tasks = cursor.fetchall()
    conn.close()

    tasks_to_remind = []
    for task_id, title, due, last_reminder in tasks:
        try:
            due_datetime = datetime.strptime(due, "%Y-%m-%d %H:%M")
            time_until_due = due_datetime - now
            
            # Skip if task is already overdue
            if time_until_due.total_seconds() < 0:
                continue
                
            # Check if we need to send a reminder based on intervals
            for interval in REMINDER_INTERVALS:
                if timedelta(0) <= time_until_due <= interval:
                    # If no previous reminder or last reminder was more than 30 minutes ago
                    if not last_reminder or (now - datetime.strptime(last_reminder, "%Y-%m-%d %H:%M:%S")).total_seconds() >= 1800:
                        tasks_to_remind.append((task_id, title, due_datetime))
                        break
                        
        except ValueError:
            continue
            
    return tasks_to_remind

def update_last_reminder(task_id):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE tasks SET last_reminder = ? WHERE id = ?", (now, task_id))
    conn.commit()
    conn.close()

def show_reminder_popup(task_list):
    if not task_list:
        return

    popup = tk.Tk()
    popup.title("⏰ Task Reminder")
    popup.geometry("400x300+100+50")
    popup.attributes("-topmost", True)
    popup.configure(bg="#fffcf5")

    header = tk.Label(popup, text="Upcoming Tasks Reminder", bg="#fffcf5", 
                     font=('Arial', 14, 'bold'))
    header.pack(pady=10)

    for task_id, title, due_time in task_list:
        time_until = due_time - datetime.now()
        days = time_until.days
        hours = time_until.seconds // 3600
        minutes = (time_until.seconds % 3600) // 60
        
        if days > 0:
            time_text = f"{days} days, {hours} hours"
        elif hours > 0:
            time_text = f"{hours} hours, {minutes} minutes"
        else:
            time_text = f"{minutes} minutes"
            
        msg = f"📌 {title}\nDue in: {time_text}"
        task_frame = tk.Frame(popup, bg="#fff0f0", relief="raised", borderwidth=1)
        task_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(task_frame, text=msg, bg="#fff0f0", 
                font=('Arial', 10), justify='left').pack(anchor='w', padx=10, pady=5)
        
        # Update the last reminder time
        update_last_reminder(task_id)

    close_btn = tk.Button(popup, text="Dismiss", command=popup.destroy, 
                         bg="#4CAF50", fg="white")
    close_btn.pack(pady=10)

    # Auto-close after 30 seconds
    popup.after(30000, popup.destroy)
    popup.mainloop()

def reminder_loop():
    while True:
        try:
            due_tasks = fetch_tasks_needing_reminder()
            if due_tasks:
                threading.Thread(target=show_reminder_popup, 
                              args=(due_tasks,), daemon=True).start()
                
                # Send system notification as well
                notification.notify(
                    title="Task Reminder",
                    message=f"You have {len(due_tasks)} task(s) due soon!",
                    timeout=10
                )
        except Exception as e:
            print(f"Error in reminder loop: {e}")
            
        # Check every minute
        time.sleep(60)

def start_reminder_bar():
    thread = threading.Thread(target=reminder_loop, daemon=True)
    thread.start()

if __name__ == "__main__":
    start_reminder_bar()
    while True:
        time.sleep(1)  # Keep alive if run directly
