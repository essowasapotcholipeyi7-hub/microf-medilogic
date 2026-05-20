from app import db
import uuid

class Repayment(db.Model):
    __tablename__ = 'repayments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    contract_id = db.Column(db.String(36), db.ForeignKey('loan_contracts.id'), nullable=False)
    
    # Échéance
    due_date = db.Column(db.Date, nullable=False)
    due_amount = db.Column(db.Numeric(12, 2), nullable=False)
    principal_part = db.Column(db.Numeric(12, 2), nullable=False)
    interest_part = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Paiement réel
    paid_date = db.Column(db.Date)
    paid_amount = db.Column(db.Numeric(12, 2), default=0)
    late_penalty = db.Column(db.Numeric(12, 2), default=0)
    
    # Statut: pending, paid, late
    status = db.Column(db.String(20), default='pending')
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Relations
    tenant = db.relationship('Tenant', backref='repayments')
    contract = db.relationship('LoanContract', backref='repayments')
    
    def __repr__(self):
        return f'<Repayment {self.due_date} - {self.due_amount}>'