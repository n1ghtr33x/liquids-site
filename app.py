from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_basicauth import BasicAuth

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['BASIC_AUTH_USERNAME'] = 'admin'
app.config['BASIC_AUTH_PASSWORD'] = '11223344558w'

db = SQLAlchemy(app)
basic_auth = BasicAuth(app)

class Liquid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Float)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    votes = db.relationship('Vote', backref='liquid', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Liquid {self.name}>"

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    liquid_id = db.Column(db.Integer, db.ForeignKey('liquid.id'), nullable=False)
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Vote for liquid {self.liquid_id}>"

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    liquids = Liquid.query.order_by(Liquid.added_at.desc()).all()
    return render_template('index.html', liquids=liquids)

@app.route('/add_liquid', methods=['POST'])
def add_liquid():
    name = request.form.get('name')
    price = request.form.get('price', type=float)
    if name:
        existing_liquid = Liquid.query.filter_by(name=name).first()
        if existing_liquid is None:
            new_liquid = Liquid(name=name, price=price)
            db.session.add(new_liquid)
            db.session.commit()
        else:
            pass
    return redirect(url_for('index'))

@app.route('/vote/<int:liquid_id>', methods=['POST'])
def vote(liquid_id):
    liquid = Liquid.query.get_or_404(liquid_id)
    new_vote = Vote(liquid_id=liquid.id)
    db.session.add(new_vote)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/analytics')
def analytics():
    liquids = Liquid.query.all()
    analytics_data = {}
    for liquid in liquids:
        analytics_data[liquid.name] = len(liquid.votes)
    return render_template('analytics.html', analytics=analytics_data)

@app.route('/api/liquids')
def api_liquids():
    liquids = Liquid.query.all()
    liquid_list = [{'id': liquid.id, 'name': liquid.name, 'price': liquid.price} for liquid in liquids]
    return jsonify(liquid_list)

@app.route('/api/analytics')
def api_analytics():
    analytics_data = {}
    liquids = Liquid.query.all()
    for liquid in liquids:
        analytics_data[liquid.name] = len(liquid.votes)
    sorted_analytics = dict(sorted(analytics_data.items(), key=lambda item: item[1], reverse=True))
    return jsonify(sorted_analytics)

# Админ-панель
@app.route('/admin')
@basic_auth.required
def admin():
    liquids = Liquid.query.order_by(Liquid.name).all()
    return render_template('admin.html', liquids=liquids)

@app.route('/admin/delete/<int:liquid_id>', methods=['POST'])
@basic_auth.required
def delete_liquid(liquid_id):
    liquid = Liquid.query.get_or_404(liquid_id)
    db.session.delete(liquid)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/edit/<int:liquid_id>', methods=['GET'])
@basic_auth.required
def edit_liquid(liquid_id):
    liquid = Liquid.query.get_or_404(liquid_id)
    return render_template('edit_liquid.html', liquid=liquid)

@app.route('/admin/edit/<int:liquid_id>', methods=['POST'])
@basic_auth.required
def update_liquid(liquid_id):
    liquid = Liquid.query.get_or_404(liquid_id)
    liquid.name = request.form.get('name')
    liquid.price = request.form.get('price', type=float)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/api/docs')
def api_docs():
    return render_template('api_docs.html')

if __name__ == '__main__':
    app.run(debug=False, port=8001, host='0.0.0.0')