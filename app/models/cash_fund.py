from app import db
from datetime import datetime
import uuid

class CashFund(db.Model):
    __tablename__ = 'cash_funds'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    
    # Solde actuel
    balance = db.Column(db.Numeric(12, 2), default=0)
    
    # Seuil minimum d'alerte
    min_balance = db.Column(db.Numeric(12, 2), default=0)
    
    # Devise
    currency = db.Column(db.String(3), default='FCFA')
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = db.relationship('Tenant', backref='cash_fund', uselist=False)
    
    def __repr__(self):
        return f'<CashFund {self.balance} FCFA>'

class CashTransaction(db.Model):
    __tablename__ = 'cash_transactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    contract_id = db.Column(db.String(36), db.ForeignKey('loan_contracts.id'), nullable=True)
    
    # Type: deposit, withdrawal, disbursement, repayment
    transaction_type = db.Column(db.String(50), nullable=False)
    
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.Text)
    
    # Balance après transaction
    balance_after = db.Column(db.Numeric(12, 2), nullable=False)
    
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tenant = db.relationship('Tenant', backref='cash_transactions')
    contract = db.relationship('LoanContract', backref='cash_transactions')
    user = db.relationship('User', backref='cash_transactions')
    
    def __repr__(self):
        return f'<CashTransaction {self.transaction_type} {self.amount}>'