# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(50))
    length = db.Column(db.Float, nullable=False)  # بالمتر
    width = db.Column(db.Float, nullable=False)   # بالمتر
    thickness = db.Column(db.Float, nullable=False) # بالملليمتر
    unit_weight = db.Column(db.Float, nullable=False) # وزن الحبة بالكجم
    notes = db.Column(db.Text)
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LoadCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)
    item_name = db.Column(db.String(100))
    item_color = db.Column(db.String(50))
    quantity = db.Column(db.Integer, nullable=False)
    expected_weight = db.Column(db.Float, nullable=False)
    actual_weight = db.Column(db.Float, default=0)
    difference = db.Column(db.Float, default=0)
    difference_percent = db.Column(db.Float, default=0)
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CalibrationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    old_weight = db.Column(db.Float, nullable=False)
    new_weight = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    item = db.relationship('Item', backref=db.backref('calibrations', lazy=True))