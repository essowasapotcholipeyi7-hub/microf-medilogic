from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.client import Client
from app.models.loan_contract import LoanContract
from app.models.repayment import Repayment
from app.models.credit_request import CreditRequest
from sqlalchemy import func

bp = Blueprint('users', __name__, url_prefix='/users')

@bp.route('/agents')
@login_required
def agents():
    # Seul l'admin peut voir les agents
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard.index'))
    
    agents = User.query.filter_by(tenant_id=current_user.tenant_id, role='agent').all()
    return render_template('users/agents.html', agents=agents)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_agent():
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        gender = request.form.get('gender')
        role = request.form.get('role')  # NOUVEAU : récupérer le rôle
        
        # Vérifier si l'utilisateur existe déjà
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Cet email est déjà utilisé', 'danger')
            return redirect(url_for('users.add_agent'))
        
        user = User(
            tenant_id=current_user.tenant_id,
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            gender=gender,
            role=role,  # 'admin' ou 'agent'
            is_active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'{role.capitalize()} {first_name} {last_name} ajouté avec succès', 'success')
        return redirect(url_for('users.list_users'))
    
    return render_template('users/add_user.html')

@bp.route('/agents/toggle/<id>')
@login_required
def toggle_agent(id):
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard.index'))
    
    agent = User.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    agent.is_active = not agent.is_active
    db.session.commit()
    
    status = "activé" if agent.is_active else "désactivé"
    flash(f'Agent {agent.first_name} {status}', 'info')
    return redirect(url_for('users.agents'))

@bp.route('/agents/delete/<id>')
@login_required
def delete_agent(id):
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard.index'))
    
    agent = User.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    db.session.delete(agent)
    db.session.commit()
    
    flash(f'Agent {agent.first_name} supprimé', 'warning')
    return redirect(url_for('users.agents'))

@bp.route('/agent-stats/<agent_id>')
@login_required
def agent_stats(agent_id):
    """Statistiques détaillées d'un agent"""
    agent = User.query.filter_by(id=agent_id, tenant_id=current_user.tenant_id).first_or_404()
    
    # Clients suivis par l'agent
    clients = Client.query.filter_by(tenant_id=current_user.tenant_id, agent_id=agent.id).all()
    clients_count = len(clients)
    
    # Crédits déboursés via les demandes de l'agent
    total_disbursed = db.session.query(func.sum(LoanContract.principal)).join(CreditRequest).filter(
        CreditRequest.agent_id == agent.id,
        CreditRequest.tenant_id == current_user.tenant_id
    ).scalar() or 0
    
    # Montant recouvré
    total_recovered = db.session.query(func.sum(Repayment.paid_amount)).join(LoanContract).join(CreditRequest).filter(
        CreditRequest.agent_id == agent.id,
        Repayment.status == 'paid'
    ).scalar() or 0
    
    recovery_rate = (total_recovered / total_disbursed * 100) if total_disbursed > 0 else 0
    
    # Détail des clients avec leurs crédits
    client_details = []
    for client in clients:
        contracts = LoanContract.query.filter_by(client_id=client.id, tenant_id=current_user.tenant_id).all()
        total_loan = sum(float(c.principal) for c in contracts)
        total_paid = sum(
            float(r.paid_amount) for c in contracts for r in c.repayments if r.status == 'paid'
        )
        client_rate = (total_paid / total_loan * 100) if total_loan > 0 else 0
        
        client_details.append({
            'client': client,
            'total_loan': total_loan,
            'total_paid': total_paid,
            'rate': client_rate
        })
    
    return render_template('users/agent_stats.html', 
                         agent=agent,
                         clients_count=clients_count,
                         total_disbursed=total_disbursed,
                         total_recovered=total_recovered,
                         recovery_rate=recovery_rate,
                         client_details=client_details)

@bp.route('/list')
@login_required
def list_users():
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard.index'))
    
    users = User.query.filter_by(tenant_id=current_user.tenant_id).all()
    return render_template('users/list_users.html', users=users)

@bp.route('/toggle/<id>')
@login_required
def toggle_user(id):
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard.index'))
    
    user = User.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    
    # Empêcher de se désactiver soi-même
    if user.id == current_user.id:
        flash('Vous ne pouvez pas modifier votre propre statut', 'warning')
        return redirect(url_for('users.list_users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "activé" if user.is_active else "désactivé"
    flash(f'Utilisateur {user.first_name} {status}', 'info')
    return redirect(url_for('users.list_users'))

@bp.route('/delete/<id>')
@login_required
def delete_user(id):
    if current_user.role != 'admin':
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard.index'))
    
    user = User.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    
    # Empêcher de se supprimer soi-même
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte', 'warning')
        return redirect(url_for('users.list_users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Utilisateur {user.first_name} {user.last_name} supprimé', 'warning')
    return redirect(url_for('users.list_users'))