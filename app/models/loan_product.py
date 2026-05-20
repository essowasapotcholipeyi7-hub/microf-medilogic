from app import db
import uuid

class LoanProduct(db.Model):
    __tablename__ = 'loan_products'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Taux et durée
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)  # en pourcentage
    interest_type = db.Column(db.String(20), default='compound')  # 'simple' ou 'compound'
    compounding_frequency = db.Column(db.String(20), default='monthly')  # 'monthly', 'weekly', 'daily'
    min_duration_months = db.Column(db.Integer, default=1)
    max_duration_months = db.Column(db.Integer, default=36)
    min_amount = db.Column(db.Numeric(12, 2), nullable=False)
    max_amount = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Frais et pénalités
    processing_fee = db.Column(db.Numeric(5, 2), default=0)  # pourcentage
    late_penalty_rate = db.Column(db.Numeric(5, 2), default=5)  # pourcentage
    grace_period_days = db.Column(db.Integer, default=0)
    
    # Garantie
    requires_guarantor = db.Column(db.Boolean, default=False)
    min_guarantors = db.Column(db.Integer, default=0)
    requires_collateral = db.Column(db.Boolean, default=False)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    tenant = db.relationship('Tenant', backref='loan_products')

    # Exigences supplémentaires
    requires_savings = db.Column(db.Boolean, default=False)  # Nécessite un fonds d'épargne
    savings_percentage = db.Column(db.Numeric(5, 2), default=10.0)  # Pourcentage du montant à épargner
    requires_guarantor = db.Column(db.Boolean, default=False)
    min_guarantors = db.Column(db.Integer, default=1)
    
    def __repr__(self):
        return f'<LoanProduct {self.name}>'