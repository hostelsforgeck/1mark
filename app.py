from flask import Flask, render_template, request, redirect, url_for, session, flash
from urllib.parse import unquote
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

    # Decode the URL-encoded subject name
    decoded_subject = unquote(subject)
    
    if decoded_subject not in quizzes['S5']:
        flash('Subject not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    modules = quizzes['S5'][decoded_subject].keys()
    return render_template('subject.html', subject=decoded_subject, modules=modules)

@app.route('/subject/<subject>/module/<module>')
def module(subject, module):
    if 'username' not in session:
        return redirect(url_for('login'))

    # Decode the URL-encoded subject and module names
    decoded_subject = unquote(subject)
    decoded_module = unquote(module)
    
    # Ensure the subject and module exist in the quizzes dictionary
    if decoded_subject not in quizzes['S5']:
        flash('Subject not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    if decoded_module not in quizzes['S5'][decoded_subject]:
        flash('Module not found.', 'danger')
        return redirect(url_for('subject', subject=decoded_subject))
    
    # Get the topics along with their titles
    topics = quizzes['S5'][decoded_subject][decoded_module]
    topic_titles = {key: value['title'] for key, value in topics.items()}
    
    return render_template('module.html', subject=decoded_subject, module=decoded_module, topics=topic_titles)

@app.route('/subject/<subject>/module/<module>/topic/<topic>', methods=['GET', 'POST'])
def quiz(subject, module, topic):
    if 'username' not in session:
        return redirect(url_for('login'))

    # Decode the URL-encoded subject, module, and topic names
    decoded_subject = unquote(subject)
    decoded_module = unquote(module)
    decoded_topic = unquote(topic)

    # Ensure the subject, module, and topic exist in the quizzes dictionary
    if decoded_subject not in quizzes['S5'] or \
       decoded_module not in quizzes['S5'][decoded_subject] or \
       decoded_topic not in quizzes['S5'][decoded_subject][decoded_module]:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('dashboard'))

    quiz_data = quizzes['S5'][decoded_subject][decoded_module][decoded_topic]
    total_questions = len(quiz_data['questions'])  # Get the total number of questions

    # Initialize session variables if not set
    if 'current_question' not in session:
        session['current_question'] = 0
        session['score'] = 0
        session['results'] = []
        session['attempted'] = False  # Track if the question was attempted before showing explanation

    current_question = session['current_question']
    show_description = False

    # Handle form submission
    if request.method == 'POST':
        user_answer = request.form.get('answer')
        correct_answer = quiz_data['questions'][current_question]['answer']
        description = quiz_data['questions'][current_question]['description']

        if user_answer == correct_answer:
            if not session['attempted']:  # If it's the first attempt
                session['score'] += 1
                session['results'].append({
                    'question': quiz_data['questions'][current_question]['question'],
                    'correct': True,
                })
                session['current_question'] += 1  # Move to the next question
            else:
                # Move to the next question without incrementing the score
                session['results'][-1]['correct'] = False  # Ensure the last entry is marked as incorrect
                session['results'][-1]['description'] = description
                session['results'][-1]['correct_answer'] = correct_answer
                session['current_question'] += 1
            session['attempted'] = False  # Reset for the next question
        else:
            if not session['attempted']:
                # Add the wrong answer to the results and show the description
                session['results'].append({
                    'question': quiz_data['questions'][current_question]['question'],
                    'correct': False,
                    'correct_answer': correct_answer,
                    'description': description,
                })
            show_description = True
            session['attempted'] = True  # Mark that the question was attempted and failed

        current_question = session['current_question']

        # If the quiz is finished
        if current_question >= total_questions:
            score = session.pop('score')
            results = session.pop('results')
            session.pop('current_question')
            session.pop('attempted')  # Clean up
            return render_template('results.html', score=score, results=results, total_questions=total_questions)

    # Show the current question
    question_data = quiz_data['questions'][current_question]

    return render_template('quiz.html',
                            quiz_title=quiz_data['title'],
                            question=question_data,
                            question_num=current_question + 1,
                            total_questions=total_questions,
                            show_description=show_description  # Pass this flag to the template
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
