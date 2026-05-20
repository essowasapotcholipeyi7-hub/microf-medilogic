from app import db
from datetime import datetime
import uuid
from decimal import Decimal

class SavingsAccount(db.Model):
    __tablename__ = 'savings_accounts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False)
    
    # Numéro de compte
    account_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # Solde du compte
    balance = db.Column(db.Numeric(12, 2), default=0)
    
    # Taux d'intérêt annuel (par défaut 5%)
    interest_rate = db.Column(db.Numeric(5, 2), default=5.0)
    
    # Date de dernière capitalisation des intérêts
    last_interest_date = db.Column(db.Date, default=datetime.now().date)
    
    # Statut: active, frozen, closed
    status = db.Column(db.String(20), default='active')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    tenant = db.relationship('Tenant', backref='savings_accounts')
    client = db.relationship('Client', backref='savings_accounts')
    transactions = db.relationship('SavingsTransaction', backref='account', lazy='dynamic')
    
    @property
    def total_interest_earned(self):
        """Total des intérêts gagnés depuis l'ouverture"""
        total = 0
        for trans in self.transactions:
            if trans.transaction_type == 'interest':
                total += float(trans.amount)
        return total
    
    def __repr__(self):
        return f'<SavingsAccount {self.account_number} - {self.balance} FCFA>'

class SavingsTransaction(db.Model):
    __tablename__ = 'savings_transactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey('savings_accounts.id'), nullable=False)
    
    # Type: deposit, withdrawal, interest
    transaction_type = db.Column(db.String(20), nullable=False)
    
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    balance_after = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.Text)
    
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tenant = db.relationship('Tenant', backref='savings_transactions')
    user = db.relationship('User', backref='savings_transactions')
    
    def __repr__(self):
        return f'<SavingsTransaction {self.transaction_type} {self.amount}>'