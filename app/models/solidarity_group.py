from app import db
from datetime import datetime
import uuid

class SolidarityGroup(db.Model):
    __tablename__ = 'solidarity_groups'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Responsable du groupe
    leader_id = db.Column(db.String(36), db.ForeignKey('clients.id'))
    
    # Statut
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    tenant = db.relationship('Tenant', backref='solidarity_groups')
    leader = db.relationship('Client', foreign_keys=[leader_id])
    members = db.relationship('GroupMember', back_populates='group', cascade='all, delete-orphan')
    
    @property
    def member_count(self):
        return len(self.members)
    
    @property
    def total_liability(self):
        """Montant total de la dette solidaire"""
        total = 0
        for member in self.members:
            for contract in member.client.loan_contracts:
                if contract.status == 'active':
                    total += contract.remaining_amount if hasattr(contract, 'remaining_amount') else contract.total_amount
        return total
    
    def __repr__(self):
        return f'<SolidarityGroup {self.name}>'

class GroupMember(db.Model):
    __tablename__ = 'group_members'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = db.Column(db.String(36), db.ForeignKey('solidarity_groups.id'), nullable=False)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False)
    
    # Rôle dans le groupe
    role = db.Column(db.String(50), default='member')  # leader, secretary, member
    
    # Date d'adhésion
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    group = db.relationship('SolidarityGroup', back_populates='members')
    client = db.relationship('Client', backref='group_memberships')
    
    # Contrainte d'unicité: un client ne peut être qu'une fois dans un groupe
    __table_args__ = (db.UniqueConstraint('group_id', 'client_id', name='unique_group_client'),)
    
    def __repr__(self):
        return f'<GroupMember {self.client.full_name} in {self.group.name}>'