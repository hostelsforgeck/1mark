from flask import Flask, render_template, request, redirect, url_for, session, flash
from all_users import users
from quizes import quizzes
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get the current user
    username = session['username']
    user = users.get(username)
    
    # Fetch subjects for the dashboard
    subjects = quizzes['S5'].keys()
    
    # Pass user details and subjects to the template
    return render_template('dashboard.html', subjects=subjects, profile=user, user_id=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users.get(username)
        if user and user['pword'] == password:
            session['username'] = username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Credentials. Please try again.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/subject/<subject>')
def subject(subject):
    if 'username' not in session:
        return redirect(url_for('login'))
    modules = quizzes['S5'][subject].keys()
    return render_template('subject.html', subject=subject, modules=modules)

@app.route('/subject/<subject>/module/<module>')
def module(subject, module):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get the topics along with their titles
    topics = quizzes['S5'][subject][module]
    topic_titles = {key: value['title'] for key, value in topics.items()}
    
    return render_template('module.html', subject=subject, module=module, topics=topic_titles)

@app.route('/subject/<subject>/module/<module>/topic/<topic>', methods=['GET', 'POST'])
def quiz(subject, module, topic):
    if 'username' not in session:
        return redirect(url_for('login'))

    quiz_data = quizzes['S5'][subject][module][topic]
    total_questions = len(quiz_data['questions'])  # Get the total number of questions


    # Initialize session variables if not set
    if 'current_question' not in session:
        session['current_question'] = 0
        session['score'] = 0
        session['results'] = []

    current_question = session['current_question']

    # Handle form submission
    if request.method == 'POST':
        user_answer = request.form.get('answer')
        correct_answer = quiz_data['questions'][current_question]['answer']
        description = quiz_data['questions'][current_question]['description']

        if user_answer == correct_answer:
            session['score'] += 1
            session['results'].append({
                'question': quiz_data['questions'][current_question]['question'],
                'correct': True,
            })
        else:
            session['results'].append({
                'question': quiz_data['questions'][current_question]['question'],
                'correct': False,
                'correct_answer': correct_answer,
                'description': description,
            })

        # Move to the next question
        session['current_question'] += 1
        current_question = session['current_question']

        # If the quiz is finished
        if current_question >= len(quiz_data['questions']):
            score = session.pop('score')
            results = session.pop('results')
            session.pop('current_question')
            return render_template('results.html', score=score, results=results)

        return redirect(url_for('quiz', subject=subject, module=module, topic=topic))

    # Show the current question
    question_data = quiz_data['questions'][current_question]

    return render_template('quiz.html',
                            quiz_title=quiz_data['title'],
                            question=question_data,
                            question_num=current_question + 1,
                            total_questions=total_questions
    )

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('current_question', None)
    session.pop('score', None)
    session.pop('results', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Ensure the 'static/images' directory exists for profile pictures
    os.makedirs(os.path.join(app.root_path, 'static', 'images'), exist_ok=True)
    app.run(debug=True)
