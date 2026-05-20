from app import db
from datetime import datetime
import uuid

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    agent_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # Informations personnelles
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # male, female
    national_id = db.Column(db.String(50))
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    date_of_birth = db.Column(db.Date)
    profession = db.Column(db.String(100))
    
    # Adresse
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    
    # Revenus
    monthly_income = db.Column(db.Numeric(12, 2))
    
    # Statut
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    tenant = db.relationship('Tenant', backref='clients')
    agent = db.relationship('User', foreign_keys=[agent_id], backref='assigned_clients')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<Client {self.full_name}>'