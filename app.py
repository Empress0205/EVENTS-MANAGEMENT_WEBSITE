from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  


# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect('instance/event.db')
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
            ''', (username, email, hashed_password))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            flash('Username already exists. Please try a different one.')
            return redirect(url_for('register'))

        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('instance/event.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):  # user[3] is the hashed password
            session['user_id'] = user[0]  # Store user ID in session
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.')

    return render_template('login.html')

@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        event_name = request.form['event_name']
        event_time = request.form['event_time']
        event_location = request.form['event_location']
        event_photo = None
        user_id = session['user_id']

        # Handle file upload
        if 'event_photo' in request.files:
            photo = request.files['event_photo']
            if photo:
                photo_filename = photo.filename
                photo_path = os.path.join('static', 'uploads', photo_filename)
                os.makedirs('static/uploads', exist_ok=True)
                photo.save(photo_path)
                event_photo = photo_filename

        conn = sqlite3.connect('instance/event.db')
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO events (name, time, photo, location, user_id)
        VALUES (?, ?, ?, ?, ?)
        ''', (event_name, event_time, event_photo, event_location, user_id))
        conn.commit()
        conn.close()

        flash('Event added successfully!')
        return redirect(url_for('index'))

    return render_template('add_event.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    user_id = session['user_id']  # Get logged-in user's ID

    try:
        # Fetch user details
        with sqlite3.connect('instance/event.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT username, email FROM users WHERE id = ?', (user_id,))
            user_data = cursor.fetchone()

            # Handle if user is not found (edge case)
            if not user_data:
                flash("User not found. Please log in again.")
                return redirect(url_for('logout'))

            # Fetch events created by this user
            cursor.execute('SELECT * FROM events WHERE user_id = ?', (user_id,))
            events = cursor.fetchall()  # Only this user's events

        # Create a user object to pass to the template
        user = {'username': user_data[0], 'email': user_data[1]}

        # Check if the user has no events
        if not events:
            flash("You have no events created yet.")

        return render_template('profile.html', user=user, events=events)
    except sqlite3.Error as e:
        flash(f"An error occurred while fetching data: {e}")
        return redirect(url_for('home'))

@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    # Fetch the event by ID and handle the edit logic here
    conn = sqlite3.connect('instance/event.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM events WHERE id = ?', (event_id,))
    event = cursor.fetchone()
    conn.close()
    
    if not event:
        flash("Event not found.")
        return redirect(url_for('profile'))
    
    # If the method is POST, handle the update logic
    if request.method == 'POST':
        event_name = request.form['name']
        event_time = request.form['time']
        event_location = request.form['location']
        
        conn = sqlite3.connect('instance/event.db')
        cursor = conn.cursor()
        cursor.execute('''UPDATE events SET name = ?, time = ?, location = ? WHERE id = ?''', 
                       (event_name, event_time, event_location, event_id))
        conn.commit()
        conn.close()
        
        flash("Event updated successfully!")
        return redirect(url_for('profile'))
    
    return render_template('edit_event.html', event=event)


@app.route('/delete_event/<int:event_id>', methods=['GET', 'POST'])
def delete_event(event_id):

    if request.method == 'POST':
        # Perform deletion logic
        conn = sqlite3.connect('instance/event.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
        conn.commit()
        conn.close()
        flash('Event deleted successfully!', 'success')
        return redirect(url_for('profile'))
    # Your existing logic
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    # Get the logged-in user's ID
    user_id = session['user_id']

    # Connect to the database and delete the event
    conn = sqlite3.connect('instance/event.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM events WHERE id = ? AND user_id = ?', (event_id, user_id))
    conn.commit()
    conn.close()

    # Redirect the user back to the profile page after deleting the event
    flash('Event deleted successfully!')
    return redirect(url_for('profile'))




# Landing Page (After successful login)
@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    return render_template('index.html')  # Your landing page template

# Home Page
@app.route('/')
def home():
    return render_template('home.html')



@app.route('/explore', methods=['GET'])
def explore():
    # Connect to the database
    conn = sqlite3.connect('instance/event.db')
    cursor = conn.cursor()
    
    # Fetch all events
    cursor.execute('SELECT id, name, time, location, photo FROM events')
    events = cursor.fetchall()
    
    conn.close()
    
    return render_template('explore.html', events=events)




@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('home'))



if __name__ == '__main__':
    app.run(debug=True)

