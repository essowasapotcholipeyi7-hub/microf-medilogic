from app import db
from datetime import datetime, date
import uuid
from datetime import datetime, date, timedelta

from app import db
from datetime import datetime, date, timedelta
import uuid

class TontineMember(db.Model):
    __tablename__ = 'tontine_members'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False)
    
    # Paramètres
    daily_amount = db.Column(db.Numeric(12, 2), nullable=False, default=500)
    start_date = db.Column(db.Date, nullable=False, default=datetime.now().date)
    interest_rate = db.Column(db.Numeric(5, 2), default=5.0)
    
    # Statut
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = db.relationship('Tenant', backref='tontine_members')
    client = db.relationship('Client', backref='tontine_membership')
    payments = db.relationship('TontinePayment', back_populates='member', lazy='dynamic')
    
    @property
    def total_paid(self):
        total = db.session.query(db.func.sum(TontinePayment.amount)).filter(
            TontinePayment.member_id == self.id,
            TontinePayment.status == 'paid'
        ).scalar() or 0
        return float(total)
    
    @property
    def total_days_paid(self):
        """Nombre total de jours payes (cumul des days_covered)"""
        total = db.session.query(db.func.sum(TontinePayment.days_covered)).filter(
            TontinePayment.member_id == self.id,
            TontinePayment.status == 'paid'
        ).scalar() or 0
        return int(total)
    
    @property
    def expected_days(self):
        days = (date.today() - self.start_date).days
        return max(0, days)
    
    @property
    def days_missing(self):
        return max(0, self.expected_days - self.total_days_paid)
    
    @property
    def expected_amount(self):
        return self.expected_days * float(self.daily_amount)
    
    @property
    def interest_earned(self):
        rate = float(self.interest_rate) / 100
        days_in_year = 365
        days_active = (date.today() - self.start_date).days
        if days_active <= 0:
            return 0
        interest = self.total_paid * rate * (days_active / days_in_year)
        return round(interest, 2)
    
    @property
    def total_with_interest(self):
        return self.total_paid + self.interest_earned
    
    @property
    def can_withdraw(self):
        """Peut retirer apres 60 jours"""
        days_active = (date.today() - self.start_date).days
        return days_active >= 60
    
    @property
    def next_payment_dates(self):
        """Prochaines dates à payer (max 7)"""
        today = date.today()
        
        # Récupérer toutes les dates déjà payées (en déroulant les jours couverts)
        paid_dates = set()
        for payment in self.payments.filter_by(status='paid').all():
            start_date_payment = payment.payment_date
            for i in range(payment.days_covered):
                covered_date = start_date_payment + timedelta(days=i)
                paid_dates.add(covered_date)
        
        # Trouver les prochaines dates manquantes
        missing = []
        for i in range(60):
            current_date = today + timedelta(days=i)
            if current_date < self.start_date:
                continue
            if current_date not in paid_dates:
                missing.append(current_date)
                if len(missing) >= 7:
                    break
        
        return missing
    
    def __repr__(self):
        return f'<TontineMember {self.client.full_name}>'


class TontinePayment(db.Model):
    __tablename__ = 'tontine_payments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    member_id = db.Column(db.String(36), db.ForeignKey('tontine_members.id'), nullable=False)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    
    payment_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    days_covered = db.Column(db.Integer, default=1)
    
    status = db.Column(db.String(20), default='pending')
    paid_at = db.Column(db.DateTime)
    
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    member = db.relationship('TontineMember', back_populates='payments')
    tenant = db.relationship('Tenant', backref='tontine_payments')
    user = db.relationship('User', backref='tontine_payments')
    
    def __repr__(self):
        return f'<TontinePayment {self.payment_date} - {self.amount}>'