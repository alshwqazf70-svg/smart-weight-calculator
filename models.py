# models.py
models = '''from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    item_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    color = db.Column(db.String(100), nullable=False)
    length = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    thickness = db.Column(db.Float, nullable=False)
    unit_weight = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    history = db.relationship('CalculationHistory', backref='item', lazy=True, cascade='all, delete-orphan')
    calibrations = db.relationship('CalibrationLog', backref='item', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_number': self.item_number,
            'name': self.name,
            'color': self.color,
            'length': self.length,
            'width': self.width,
            'thickness': self.thickness,
            'unit_weight': self.unit_weight,
            'notes': self.notes,
            'usage_count': self.usage_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Item {self.name}>'


class CalculationHistory(db.Model):
    __tablename__ = 'calculation_history'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    item_color = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    expected_weight = db.Column(db.Float, nullable=False)
    actual_weight = db.Column(db.Float, nullable=True)
    difference = db.Column(db.Float, nullable=True)
    difference_percent = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'item_name': self.item_name,
            'item_color': self.item_color,
            'quantity': self.quantity,
            'expected_weight': round(self.expected_weight, 2),
            'actual_weight': round(self.actual_weight, 2) if self.actual_weight else None,
            'difference': round(self.difference, 2) if self.difference else None,
            'difference_percent': round(self.difference_percent, 2) if self.difference_percent else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }


class CalibrationLog(db.Model):
    __tablename__ = 'calibration_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    old_weight = db.Column(db.Float, nullable=False)
    new_weight = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'old_weight': self.old_weight,
            'new_weight': self.new_weight,
            'reason': self.reason,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'details': self.details,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }
