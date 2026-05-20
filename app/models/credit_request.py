from app import db
import uuid

class CreditRequest(db.Model):
    __tablename__ = 'credit_requests'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('loan_products.id'), nullable=False)
    agent_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # Demande
    amount_requested = db.Column(db.Numeric(12, 2), nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.Text)
    
    # Garanties
    guarantor_names = db.Column(db.Text)  # JSON ou texte séparé par virgules
    collateral_description = db.Column(db.Text)
    
    # Statut: pending, approved, rejected, disbursed
    status = db.Column(db.String(20), default='pending')
    
    # Approbation
    approved_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    # Relations
    tenant = db.relationship('Tenant', backref='credit_requests')
    client = db.relationship('Client', backref='credit_requests')
    product = db.relationship('LoanProduct', backref='credit_requests')
    agent = db.relationship('User', foreign_keys=[agent_id])
    approver = db.relationship('User', foreign_keys=[approved_by])
    
    def __repr__(self):
        return f'<CreditRequest {self.client.full_name} - {self.amount_requested}>'