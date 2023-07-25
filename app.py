from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder for image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)

# Simulated database for blog posts
posts = []

# Create the User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Create the Comment model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('comments', lazy=True))
    

# Create the Post model
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('posts', lazy=True))
    tags = db.relationship('Tag', secondary='post_tag', backref=db.backref('posts', lazy=True))
    image = db.Column(db.String(255))  # File path of the uploaded image
    status = db.Column(db.String(10), default='draft')  # 'draft', 'published', or 'archived'

# Create the Tag model
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

# Create the association table for Post and Tag
post_tag = db.Table('post_tag',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

# Follows model to represent user-to-user follows
class Follows(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed_at = db.Column(db.DateTime, default=datetime.utcnow)

# Likes model to represent post likes
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

# Load a user from the database for login
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        return None

#Image upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/',methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 1, type=int)
    posts_per_page = 5  # Number of blog posts per page

    if request.method == 'POST':
        search_query = request.form.get('search_query', '')
        posts = Post.query.filter(Post.title.contains(search_query) | Post.content.contains(search_query)).paginate(page=page, per_page=posts_per_page)
    else:
        posts = Post.query.order_by(Post.id.desc()).paginate(page=page, per_page=posts_per_page)

    return render_template('index.html', posts=posts)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        tags = [Tag.query.get(int(tag)) for tag in request.form.getlist('tags')]
        # Image upload handling
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = url_for('uploaded_file', filename=filename)
            else:
                flash('Invalid file format. Allowed formats are PNG, JPG, JPEG, and GIF.', 'error')
                return redirect(url_for('create'))
        else:
            image_url = None

        post = Post(title=title, content=content, author=current_user, tags=tags, image=image_url)
        db.session.add(post)
        db.session.commit()

        if status == 'draft':
            flash('Post saved as draft.', 'success')
            return redirect(url_for('drafts'))
        else:
            flash('Post published successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('create.html', tags=Tag.query.all())

@app.route('/drafts')
@login_required
def drafts():
    drafts = Post.query.filter_by(author=current_user, status='draft').all()
    return render_template('drafts.html', drafts=drafts)

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    post = Post.query.get_or_404(post_id)

    # Check if the user is the author of the post
    if post.author != current_user:
        flash('You are not authorized to edit this post.', 'error')
        return redirect(url_for('post', post_id=post.id))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        tags = [Tag.query.get(int(tag)) for tag in request.form.getlist('tags')]
        status = request.form['status']
        
        # Image upload handling (similar to create route)

        post.title = title
        post.content = content
        post.tags = tags
        post.status = status
        db.session.commit()

        if status == 'draft':
            flash('Post saved as draft.', 'success')
            return redirect(url_for('drafts'))
        else:
            flash('Post updated successfully!', 'success')
            return redirect(url_for('post', post_id=post.id))

    return render_template('edit.html', post=post, tags=Tag.query.all())

@app.route('/archives')
def archives():
    posts = Post.query.filter_by(status='published').order_by(Post.created_at.desc()).all()
    return render_template('archives.html', posts=posts)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get(post_id)
    if request.method == 'POST':
        content = request.form['content']
        comment = Comment(content=content, post=post, author=current_user)
        db.session.add(comment)
        db.session.commit()
    return render_template('post.html', post=post)

@app.route('/approve_comment/<int:comment_id>', methods=['POST'])
@login_required
def approve_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    # Check if the user is an admin before approving the comment
    if current_user.is_admin:
        comment.is_approved = True
        db.session.commit()

    return redirect(url_for('post', post_id=comment.post_id))

@app.route('/disapprove_comment/<int:comment_id>', methods=['POST'])
@login_required
def disapprove_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    # Check if the user is an admin before disapproving the comment
    if current_user.is_admin:
        comment.is_approved = False
        db.session.commit()
    return redirect(url_for('post', post_id=comment.post_id))

@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        is_admin = 'is_admin' in request.form

        # Check if the username is available
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return redirect(url_for('register'))

        user = User(username=username, password=password, full_name=full_name, is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Follow user route
@app.route('/follow/<int:user_id>')
@login_required
def follow_user(user_id):
    user_to_follow = User.query.get_or_404(user_id)
    if user_to_follow != current_user:
        current_user.following.append(user_to_follow)
        db.session.commit()
        flash(f'You are now following {user_to_follow.username}.', 'success')
    return redirect(url_for('profile', user_id=user_id))

# Unfollow user route
@app.route('/unfollow/<int:user_id>')
@login_required
def unfollow_user(user_id):
    user_to_unfollow = User.query.get_or_404(user_id)
    if user_to_unfollow != current_user:
        current_user.following.remove(user_to_unfollow)
        db.session.commit()
        flash(f'You have unfollowed {user_to_unfollow.username}.', 'success')
    return redirect(url_for('profile', user_id=user_id))

# Like post route
@app.route('/like/<int:post_id>')
@login_required
def like_post(post_id):
    post_to_like = Post.query.get_or_404(post_id)
    if post_to_like not in current_user.likes:
        like = Like(user_id=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()
        flash('You liked the post.', 'success')
    return redirect(url_for('post', post_id=post_id))

# Unlike post route
@app.route('/unlike/<int:post_id>')
@login_required
def unlike_post(post_id):
    post_to_unlike = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
        flash('You unliked the post.', 'success')
    return redirect(url_for('post', post_id=post_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)