from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# Simulated database for blog posts
posts = []

@app.route('/')
def index():
    return render_template('index.html', posts=posts)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = request.form['author']
        posts.append({'title': title, 'content': content, 'author': author})
        return redirect(url_for('index'))
    return render_template('create.html')

if __name__ == '__main__':
    app.run(debug=True)

