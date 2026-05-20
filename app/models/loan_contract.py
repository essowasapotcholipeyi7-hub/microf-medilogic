from app import db
import uuid

class LoanContract(db.Model):
    __tablename__ = 'loan_contracts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False)
    credit_request_id = db.Column(db.String(36), db.ForeignKey('credit_requests.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('loan_products.id'), nullable=False)
    
    # Numéro de contrat unique
    contract_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # Montants
    principal = db.Column(db.Numeric(12, 2), nullable=False)
    total_interest = db.Column(db.Numeric(12, 2), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)  # principal + intérêts
    monthly_payment = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Dates
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # Taux appliqués
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)
    interest_type = db.Column(db.String(20), nullable=False)  # simple ou compound
    processing_fee = db.Column(db.Numeric(12, 2), default=0)
    
    # État: active, completed, defaulted, written_off
    status = db.Column(db.String(20), default='active')
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Relations
    tenant = db.relationship('Tenant', backref='loan_contracts')
    client = db.relationship('Client', backref='loan_contracts')
    credit_request = db.relationship('CreditRequest', backref='loan_contract')
    product = db.relationship('LoanProduct', backref='loan_contracts')
    
    def __repr__(self):
        return f'<LoanContract {self.contract_number}>'