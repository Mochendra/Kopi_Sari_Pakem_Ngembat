from pymongo import MongoClient
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client["your_database_name_coffe"]
cards_collection = db["cards_coffe"]

# Valid credentials
valid_username = os.getenv('VALID_USERNAME')
valid_password = os.getenv('VALID_PASSWORD')

# Folder untuk menyimpan gambar
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = os.getenv('SECRET_KEY')

def login_required(f):
    def wrap(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Anda harus login terlebih dahulu.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/')
def index():
    cards = list(cards_collection.find())
    return render_template('index.html', cards=cards)

@app.route('/admin')
@login_required
def admin():
    cards = list(cards_collection.find())
    return render_template('admin.html', cards=cards)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == valid_username and password == valid_password:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('Username atau password anda salah!', 'danger')
            session['logged_in'] = False
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session['logged_in'] = False
    flash('Anda telah logout, login kembali.', 'success')
    return redirect(url_for('index'))

@app.route('/add_card', methods=['POST'])
@login_required
def add_card():
    new_card = {
        "title": request.form['title'],
        "text": request.form['text']
    }

    if 'image' in request.files:
        image = request.files['image']
        if image.filename != '':
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)
            new_card['image'] = filepath

    cards_collection.insert_one(new_card)
    return redirect(url_for('admin'))

@app.route('/edit_card/<id>', methods=['GET'])
@login_required
def edit_card(id):
    card = cards_collection.find_one({"_id": ObjectId(id)})
    return render_template('edit.html', card=card)

@app.route('/update_card/<id>', methods=['POST'])
@login_required
def update_card(id):
    card = cards_collection.find_one({"_id": ObjectId(id)})

    title = request.form['title']
    text = request.form['text']
    image = request.files['image']

    if image and image.filename != '':
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        image_url = url_for('static', filename='images/' + filename)
    else:
        image_url = card['image']

    updated_card = {
        "title": title,
        "text": text,
        "image": image_url
    }

    cards_collection.update_one({"_id": ObjectId(id)}, {"$set": updated_card})
    return redirect(url_for('admin'))

@app.route('/delete_card/<id>', methods=['POST'])
@login_required
def delete_card(id):
    cards_collection.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(port=5000, debug=True)
