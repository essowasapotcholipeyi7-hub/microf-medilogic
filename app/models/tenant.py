from app import db
from datetime import datetime
import uuid

class Tenant(db.Model):
    __tablename__ = 'tenants'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    logo = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation avec User (back_populates explicite)
    user_list = db.relationship('User', back_populates='tenant', lazy='dynamic')
    
    def __repr__(self):
        return f'<Tenant {self.name}>'