from flask import Flask, request, jsonify, render_template
import database
import scheduler

app = Flask(__name__)

# --- PAGE ROUTING ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/schedule_view')
def schedule_view():
    return render_template('schedule.html')

@app.route('/progress_view')
def progress_view():
    return render_template('progress.html')

# --- REST APIs ---
@app.route('/api/subjects', methods=['GET', 'POST'])
def manage_subjects():
    conn = database.get_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        data = request.json
        cursor.execute("INSERT INTO subjects (name, exam_date, daily_hours_allocated) VALUES (?, ?, ?)",
                       (data['name'], data['exam_date'], float(data['daily_hours_allocated'])))
        conn.commit()
        return jsonify({"message": "Subject added successfully"})
    else:
        cursor.execute("SELECT * FROM subjects")
        subjects = [dict(row) for row in cursor.fetchall()]
        return jsonify(subjects)

@app.route('/api/topics', methods=['POST'])
def add_topic():
    data = request.json
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # Calculate estimated hours based on difficulty logic
    base_calc = float(data['difficulty']) * 1.5 # 1.5 hr for easy, 3 hr for medium, 4.5 hr for hard
    
    cursor.execute("INSERT INTO topics (subject_id, name, difficulty, estimated_hours) VALUES (?, ?, ?, ?)",
                   (data['subject_id'], data['name'], data['difficulty'], base_calc))
    conn.commit()
    return jsonify({"message": "Topic added successfully"})

@app.route('/api/topics', methods=['GET'])
def get_topics():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*, s.name as subject_name 
        FROM topics t 
        JOIN subjects s ON t.subject_id = s.id
    """)
    topics = [dict(row) for row in cursor.fetchall()]
    return jsonify(topics)

@app.route('/api/schedule/generate', methods=['POST'])
def generate_schedule_api():
    result = scheduler.generate_schedule()
    return jsonify(result)

@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sch.id, sch.date, sch.is_revision, sch.is_completed, 
               t.name as topic_name, t.difficulty, s.name as subject_name
        FROM schedule sch
        JOIN topics t ON sch.topic_id = t.id
        JOIN subjects s ON t.subject_id = s.id
        ORDER BY sch.date ASC
    """)
    schedule = [dict(row) for row in cursor.fetchall()]
    return jsonify(schedule)

@app.route('/api/schedule/<int:schedule_id>/complete', methods=['PUT'])
def mark_schedule_complete(schedule_id):
    conn = database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE schedule SET is_completed = TRUE WHERE id = ?", (schedule_id,))
    
    # Smart Recalculation Trigger logic: mark topic complete if it's the main study task
    cursor.execute("""
        UPDATE topics SET status = 'Completed' 
        WHERE id = (SELECT topic_id FROM schedule WHERE id = ? AND is_revision = FALSE)
    """, (schedule_id,))
    
    conn.commit()
    return jsonify({"message": "Task marked as complete! Great job!"})

if __name__ == '__main__':
    database.init_db() # Ensure DB is robust on boot
    app.run(debug=True, port=5000)
