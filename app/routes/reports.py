from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import db
from app.models.client import Client
from app.models.loan_contract import LoanContract
from app.models.repayment import Repayment
from app.models.user import User
from app.models.credit_request import CreditRequest
from sqlalchemy import func

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('/')
@login_required
def index():
    return render_template('reports/index.html')

@bp.route('/gender')
@login_required
def gender_stats():
    # Statistiques par genre
    male_clients = Client.query.filter_by(tenant_id=current_user.tenant_id, gender='male').count()
    female_clients = Client.query.filter_by(tenant_id=current_user.tenant_id, gender='female').count()
    total_clients = male_clients + female_clients
    
    # Crédits par genre
    male_loans = db.session.query(func.sum(LoanContract.principal)).join(Client).filter(
        Client.tenant_id == current_user.tenant_id,
        Client.gender == 'male'
    ).scalar() or 0
    
    female_loans = db.session.query(func.sum(LoanContract.principal)).join(Client).filter(
        Client.tenant_id == current_user.tenant_id,
        Client.gender == 'female'
    ).scalar() or 0
    
    # Taux de remboursement par genre
    male_repayments = db.session.query(func.sum(Repayment.paid_amount)).join(LoanContract).join(Client).filter(
        Client.tenant_id == current_user.tenant_id,
        Client.gender == 'male',
        Repayment.status == 'paid'
    ).scalar() or 0
    
    male_total = db.session.query(func.sum(LoanContract.total_amount)).join(Client).filter(
        Client.tenant_id == current_user.tenant_id,
        Client.gender == 'male'
    ).scalar() or 0
    
    female_repayments = db.session.query(func.sum(Repayment.paid_amount)).join(LoanContract).join(Client).filter(
        Client.tenant_id == current_user.tenant_id,
        Client.gender == 'female',
        Repayment.status == 'paid'
    ).scalar() or 0
    
    female_total = db.session.query(func.sum(LoanContract.total_amount)).join(Client).filter(
        Client.tenant_id == current_user.tenant_id,
        Client.gender == 'female'
    ).scalar() or 0
    
    male_rate = (male_repayments / male_total * 100) if male_total > 0 else 0
    female_rate = (female_repayments / female_total * 100) if female_total > 0 else 0
    
    return render_template('reports/gender.html',
                         male_clients=male_clients,
                         female_clients=female_clients,
                         total_clients=total_clients,
                         male_loans=male_loans,
                         female_loans=female_loans,
                         male_rate=male_rate,
                         female_rate=female_rate)

@bp.route('/agents')
@login_required
def agents_stats():
    # Statistiques par agent
    agents = User.query.filter_by(tenant_id=current_user.tenant_id, role='agent').all()
    
    agents_data = []
    for agent in agents:
        # Nombre de clients par agent
        clients_count = Client.query.filter_by(tenant_id=current_user.tenant_id, agent_id=agent.id).count()
        
        # Montant total des crédits déboursés par l'agent
        total_disbursed = db.session.query(func.sum(LoanContract.principal)).join(CreditRequest).filter(
            CreditRequest.agent_id == agent.id,
            CreditRequest.tenant_id == current_user.tenant_id
        ).scalar() or 0
        
        # Montant recouvré
        total_recovered = db.session.query(func.sum(Repayment.paid_amount)).join(LoanContract).join(CreditRequest).filter(
            CreditRequest.agent_id == agent.id,
            Repayment.status == 'paid'
        ).scalar() or 0
        
        # Taux de recouvrement
        recovery_rate = (total_recovered / total_disbursed * 100) if total_disbursed > 0 else 0
        
        agents_data.append({
            'agent': agent,
            'clients_count': clients_count,
            'total_disbursed': total_disbursed,
            'total_recovered': total_recovered,
            'recovery_rate': recovery_rate
        })
    
    return render_template('reports/agents.html', agents_data=agents_data)

@bp.route('/dashboard-stats')
@login_required
def dashboard_stats():
    # Statistiques pour le tableau de bord
    total_clients = Client.query.filter_by(tenant_id=current_user.tenant_id).count()
    
    total_active_loans = LoanContract.query.filter_by(tenant_id=current_user.tenant_id, status='active').count()
    
    total_disbursed = db.session.query(func.sum(LoanContract.principal)).filter_by(tenant_id=current_user.tenant_id).scalar() or 0
    
    total_expected = db.session.query(func.sum(LoanContract.total_amount)).filter_by(tenant_id=current_user.tenant_id).scalar() or 0
    
    total_recovered = db.session.query(func.sum(Repayment.paid_amount)).join(LoanContract).filter(
        LoanContract.tenant_id == current_user.tenant_id,
        Repayment.status == 'paid'
    ).scalar() or 0
    
    recovery_rate = (total_recovered / total_expected * 100) if total_expected > 0 else 0
    
    # Demandes en attente
    pending_requests = CreditRequest.query.filter_by(tenant_id=current_user.tenant_id, status='pending').count()
    
    return {
        'total_clients': total_clients,
        'total_active_loans': total_active_loans,
        'total_disbursed': total_disbursed,
        'total_expected': total_expected,
        'total_recovered': total_recovered,
        'recovery_rate': recovery_rate,
        'pending_requests': pending_requests
    }