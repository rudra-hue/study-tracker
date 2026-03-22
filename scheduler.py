from datetime import datetime, timedelta
import database

def calculate_days(start_date, end_date):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    return max((end_date - start_date).days, 1)

def generate_schedule():
    """Reads all pending topics, available time, and generates a smart valid schedule."""
    conn = database.get_connection()
    cursor = conn.cursor()

    # Fetch subjects
    cursor.execute("SELECT id, name, exam_date, daily_hours_allocated FROM subjects")
    subjects = [dict(row) for row in cursor.fetchall()]

    if not subjects:
        return {"error": "No subjects found. Please add subjects first."}
    
    # Clear any old uncompleted schedule to regenerate dynamically
    cursor.execute("DELETE FROM schedule WHERE is_completed = FALSE")
    
    today = datetime.now().date()
    
    # Fetch all pending topics, prioritizing closest exams and hard topics
    cursor.execute("""
        SELECT t.id, t.subject_id, t.name, t.difficulty, t.estimated_hours, s.exam_date 
        FROM topics t 
        JOIN subjects s ON t.subject_id = s.id 
        WHERE t.status = 'Pending'
        ORDER BY s.exam_date ASC, t.difficulty DESC
    """)
    topics = [dict(row) for row in cursor.fetchall()]
    
    if not topics:
        conn.commit()
        return {"message": "All topics are already completed! You are good to go."}

    # Sum up all global daily limit across subjects (user capacity)
    global_daily_limit = sum(s['daily_hours_allocated'] for s in subjects)
    if global_daily_limit <= 0:
        global_daily_limit = 4.0 # default fallback
        
    schedule_plan = []
    current_date = today
    unassigned_topics = list(topics)
    
    while unassigned_topics:
        daily_assigned_hours = 0
        assigned_subjects_today = set()
        topics_to_consider = list(unassigned_topics)
        assigned_any_today = False
        
        for topic in topics_to_consider:
            if daily_assigned_hours >= global_daily_limit:
                break
            
            exam_date_str = topic.get('exam_date')
            exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date() if exam_date_str else None
            is_urgent = False
            if exam_date:
                days_until_exam = (exam_date - current_date).days
                if days_until_exam <= 3:
                     is_urgent = True

            # Avoid monotony by switching subjects if possible, dropping this rule if exam is urgent
            if not is_urgent and topic['subject_id'] in assigned_subjects_today and len(set(t['subject_id'] for t in unassigned_topics)) > 1:
                continue
            
            # If a topic pushes us slightly over the limit, attach it cautiously unless it's huge
            if daily_assigned_hours + topic['estimated_hours'] > global_daily_limit:
                if assigned_any_today:
                    continue
                
            # Assign main study session
            schedule_plan.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'topic_id': topic['id'],
                'is_revision': False
            })
            
            # Smart Feature: Spaced Repetition! (Revise at day+3 and day+7)
            # Only add revisions if they fall before the exam date (or if there is no exam date)
            rev1_date = current_date + timedelta(days=3)
            if not exam_date or rev1_date < exam_date:
                schedule_plan.append({'date': rev1_date.strftime('%Y-%m-%d'), 'topic_id': topic['id'], 'is_revision': True})
                
            rev2_date = current_date + timedelta(days=7)
            if not exam_date or rev2_date < exam_date:
                schedule_plan.append({'date': rev2_date.strftime('%Y-%m-%d'), 'topic_id': topic['id'], 'is_revision': True})
            
            daily_assigned_hours += topic['estimated_hours']
            assigned_subjects_today.add(topic['subject_id'])
            unassigned_topics.remove(topic)
            assigned_any_today = True

        current_date += timedelta(days=1)
        
        # Deadlock breaker
        if not assigned_any_today and unassigned_topics:
             topic = unassigned_topics.pop(0)
             schedule_plan.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'topic_id': topic['id'],
                'is_revision': False
             })
             current_date += timedelta(days=1)


    # Insert the brand new schedule into DB
    for entry in schedule_plan:
        cursor.execute('''
            INSERT INTO schedule (date, topic_id, is_revision) 
            VALUES (?, ?, ?)
        ''', (entry['date'], entry['topic_id'], entry['is_revision']))

    conn.commit()
    conn.close()
    return {"message": "Schedule generated dynamically with Spaced Repetition!", "days_planned": (current_date - today).days}

if __name__ == '__main__':
    print(generate_schedule())
