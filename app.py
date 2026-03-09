from flask import Flask, render_template, request, redirect, url_for, flash, abort
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Database configuration
DATABASE = 'database.db'

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tasks table"""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            due_date DATE,
            completed BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
if not os.path.exists(DATABASE):
    init_db()

# Routes

@app.route('/')
def index():
    """Display all tasks with optional search"""
    conn = get_db_connection()
    
    # Handle search
    search_query = request.args.get('q', '')
    
    if search_query:
        tasks = conn.execute(
            'SELECT * FROM tasks WHERE title LIKE ? ORDER BY created_at DESC',
            ('%' + search_query + '%',)
        ).fetchall()
    else:
        tasks = conn.execute('SELECT * FROM tasks ORDER BY created_at DESC').fetchall()
    
    conn.close()
    
    # Add today's date for overdue checking
    from datetime import date
    today = date.today().isoformat()
    
    return render_template('index.html', tasks=tasks, search_query=search_query, today=today)

@app.route('/add', methods=['GET', 'POST'])
def add_task():
    """Add new task"""
    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form['description'].strip()
        due_date = request.form.get('due_date', '')
        
        # Validation
        if not title:
            flash('Title is required!', 'error')
            return redirect(url_for('add_task'))
        
        if len(title) > 100:
            flash('Title must be less than 100 characters!', 'error')
            return redirect(url_for('add_task'))
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO tasks (title, description, due_date) VALUES (?, ?, ?)',
            (title, description, due_date if due_date else None)
        )
        conn.commit()
        conn.close()
        
        flash('Task added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_task(id):
    """Edit existing task"""
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (id,)).fetchone()
    
    if task is None:
        abort(404)
    
    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form['description'].strip()
        due_date = request.form.get('due_date', '')
        
        if not title:
            flash('Title is required!', 'error')
            return redirect(url_for('edit_task', id=id))
        
        conn.execute(
            'UPDATE tasks SET title = ?, description = ?, due_date = ? WHERE id = ?',
            (title, description, due_date if due_date else None, id)
        )
        conn.commit()
        conn.close()
        
        flash('Task updated successfully!', 'success')
        return redirect(url_for('index'))
    
    conn.close()
    return render_template('edit.html', task=task)

@app.route('/delete/<int:id>')
def delete_task(id):
    """Delete task"""
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (id,)).fetchone()
    
    if task is None:
        abort(404)
    
    conn.execute('DELETE FROM tasks WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/complete/<int:id>')
def complete_task(id):
    """Toggle task completion status"""
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (id,)).fetchone()
    
    if task is None:
        abort(404)
    
    new_status = not task['completed']
    conn.execute('UPDATE tasks SET completed = ? WHERE id = ?', (new_status, id))
    conn.commit()
    conn.close()
    
    status_text = 'completed' if new_status else 'pending'
    flash(f'Task marked as {status_text}!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)