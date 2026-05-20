from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.solidarity_group import SolidarityGroup, GroupMember
from app.models.client import Client
from app.models.loan_contract import LoanContract
from app.models.repayment import Repayment
from app.services.interest_service import InterestService
from datetime import datetime
import uuid
from datetime import timedelta

bp = Blueprint('groups', __name__, url_prefix='/groups')

@bp.route('/')
@login_required
def index():
    groups = SolidarityGroup.query.filter_by(tenant_id=current_user.tenant_id).all()
    return render_template('groups/index.html', groups=groups)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        leader_id = request.form.get('leader_id')
        
        group = SolidarityGroup(
            tenant_id=current_user.tenant_id,
            name=name,
            description=description,
            leader_id=leader_id if leader_id else None
        )
        db.session.add(group)
        db.session.commit()
        
        flash(f'Groupe "{name}" créé avec succès!', 'success')
        return redirect(url_for('groups.index'))
    
    clients = Client.query.filter_by(tenant_id=current_user.tenant_id, is_active=True).all()
    return render_template('groups/add.html', clients=clients)

@bp.route('/view/<id>')
@login_required
def view(id):
    group = SolidarityGroup.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    
    # Calcul des statistiques du groupe
    total_loans = 0.0
    total_repaid = 0.0
    active_loans = 0
    
    for member in group.members:
        contracts = LoanContract.query.filter_by(client_id=member.client_id, tenant_id=current_user.tenant_id).all()
        for contract in contracts:
            total_loans += float(contract.principal)
            repaid = sum(float(r.paid_amount) for r in contract.repayments if r.status == 'paid')
            total_repaid += repaid
            if contract.status == 'active':
                active_loans += 1
    
    recovery_rate = (total_repaid / total_loans * 100) if total_loans > 0 else 0
    
    return render_template('groups/view.html', 
                         group=group, 
                         total_loans=total_loans,
                         total_repaid=total_repaid,
                         active_loans=active_loans,
                         recovery_rate=recovery_rate)

@bp.route('/add-member/<group_id>', methods=['POST'])
@login_required
def add_member(group_id):
    group = SolidarityGroup.query.filter_by(id=group_id, tenant_id=current_user.tenant_id).first_or_404()
    client_id = request.form.get('client_id')
    
    # Vérifier si le client est déjà dans le groupe
    existing = GroupMember.query.filter_by(group_id=group_id, client_id=client_id).first()
    if existing:
        flash('Ce client est déjà membre du groupe', 'warning')
        return redirect(url_for('groups.view', id=group_id))
    
    member = GroupMember(
        group_id=group_id,
        client_id=client_id,
        role=request.form.get('role', 'member')
    )
    db.session.add(member)
    db.session.commit()
    
    client = Client.query.get(client_id)
    flash(f'{client.full_name} a été ajouté au groupe', 'success')
    return redirect(url_for('groups.view', id=group_id))

@bp.route('/remove-member/<member_id>')
@login_required
def remove_member(member_id):
    member = GroupMember.query.filter_by(id=member_id).first_or_404()
    group_id = member.group_id
    group = SolidarityGroup.query.filter_by(id=group_id, tenant_id=current_user.tenant_id).first_or_404()
    
    # Vérifier que ce n'est pas le seul membre
    if len(group.members) <= 1:
        flash('Un groupe doit avoir au moins un membre', 'danger')
        return redirect(url_for('groups.view', id=group_id))
    
    client_name = member.client.full_name
    db.session.delete(member)
    db.session.commit()
    
    flash(f'{client_name} a été retiré du groupe', 'warning')
    return redirect(url_for('groups.view', id=group_id))

@bp.route('/delete/<id>')
@login_required
def delete(id):
    group = SolidarityGroup.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    db.session.delete(group)
    db.session.commit()
    flash(f'Groupe "{group.name}" supprimé', 'warning')
    return redirect(url_for('groups.index'))

@bp.route('/group-loan/<group_id>', methods=['GET', 'POST'])
@login_required
def group_loan(group_id):
    group = SolidarityGroup.query.filter_by(id=group_id, tenant_id=current_user.tenant_id).first_or_404()
    
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        duration = int(request.form.get('duration_months'))
        interest_rate = float(request.form.get('interest_rate', 12))
        
        # Créer un prêt pour chaque membre
        for member in group.members:
            # Montant réparti équitablement
            member_amount = amount / len(group.members)
            
            # Calculer les intérêts
            interest_result = InterestService.calculate_compound_interest(
                member_amount, interest_rate, duration, 'monthly'
            )
            
            amortization = InterestService.generate_amortization_schedule(
                member_amount, interest_rate, duration, 'compound'
            )
            
            # Générer le numéro de contrat
            contract_number = f"GROUP-{group.name[:5]}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
            
            contract = LoanContract(
                tenant_id=current_user.tenant_id,
                client_id=member.client_id,
                credit_request_id=None,
                product_id=None,
                contract_number=contract_number,
                principal=member_amount,
                total_interest=interest_result['total_interest'],
                total_amount=interest_result['total_amount'],
                monthly_payment=amortization['monthly_payment'],
                start_date=datetime.now().date(),
                end_date=datetime.now().date() + timedelta(days=30 * duration),
                interest_rate=interest_rate,
                interest_type='compound',
                status='active'
            )
            db.session.add(contract)
            db.session.flush()
            
            # Créer les échéances
            for payment in amortization['schedule']:
                repayment = Repayment(
                    tenant_id=current_user.tenant_id,
                    contract_id=contract.id,
                    due_date=payment['due_date'],
                    due_amount=payment['payment'],
                    principal_part=payment['principal'],
                    interest_part=payment['interest'],
                    status='pending'
                )
                db.session.add(repayment)
        
        db.session.commit()
        flash(f'Prêt solidaire de {amount:,.0f} FCFA accordé au groupe {group.name}', 'success')
        return redirect(url_for('groups.view', id=group_id))
    
    return render_template('groups/group_loan.html', group=group)