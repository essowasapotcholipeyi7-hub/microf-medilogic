from app import db
from datetime import datetime
import uuid
from dateutil.easter import easter
from dateutil.relativedelta import relativedelta

class Holiday(db.Model):
    __tablename__ = 'holidays'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    # Type: 'fixed' (date fixe) ou 'movable' (date mobile)
    holiday_type = db.Column(db.String(20), default='fixed')
    
    # Pour les jours fixes (ex: 01-01 pour Nouvel An)
    fixed_date = db.Column(db.String(10))  # Format MM-DD
    
    # Pour les jours mobiles (ex: easter, easter+1, etc.)
    movable_rule = db.Column(db.String(50))  # easter, easter+1, ascension, pentecost
    
    year = db.Column(db.Integer)  # Année spécifique (None = tous les ans)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tenant = db.relationship('Tenant', backref='holidays')
    
    @staticmethod
    def get_movable_date(rule, year):
        """Calcule la date d'un jour mobile pour une année donnée"""
        if rule == 'easter':
            return easter(year)
        elif rule == 'easter_monday':
            return easter(year) + relativedelta(days=1)
        elif rule == 'ascension':
            return easter(year) + relativedelta(days=39)
        elif rule == 'pentecost':
            return easter(year) + relativedelta(days=50)
        elif rule == 'pentecost_monday':
            return easter(year) + relativedelta(days=51)
        elif rule.startswith('easter+'):
            days = int(rule.split('+')[1])
            return easter(year) + relativedelta(days=days)
        return None
    
    def get_date_for_year(self, year):
        """Retourne la date du jour férié pour une année donnée"""
        if self.holiday_type == 'fixed' and self.fixed_date:
            return datetime.strptime(f"{year}-{self.fixed_date}", '%Y-%m-%d').date()
        elif self.holiday_type == 'movable' and self.movable_rule:
            return self.get_movable_date(self.movable_rule, year)
        return None
    
    def __repr__(self):
        return f'<Holiday {self.name}>'