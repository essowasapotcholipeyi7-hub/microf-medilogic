from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.client import Client
from app.models.loan_product import LoanProduct
from app.models.credit_request import CreditRequest
from app.models.loan_contract import LoanContract
from app.models.repayment import Repayment
from app.services.interest_service import InterestService
from datetime import datetime, timedelta
from app.services.cash_service import CashService
import uuid

bp = Blueprint('contracts', __name__, url_prefix='/contracts')

@bp.route('/')
@login_required
def index():
    contracts = LoanContract.query.filter_by(tenant_id=current_user.tenant_id).order_by(LoanContract.created_at.desc()).all()
    return render_template('contracts/index.html', contracts=contracts)

@bp.route('/create/<credit_request_id>', methods=['GET', 'POST'])
@login_required
def create(credit_request_id):
    from app.services.cash_service import CashService
    
    # Récupérer la demande approuvée
    credit_request = CreditRequest.query.filter_by(
        id=credit_request_id, 
        tenant_id=current_user.tenant_id,
        status='approved'
    ).first_or_404()
    
    product = credit_request.product
    client = credit_request.client
    
    # Calculer les intérêts et l'échéancier
    if product.interest_type == 'compound':
        interest_result = InterestService.calculate_compound_interest(
            credit_request.amount_requested,
            product.interest_rate,
            credit_request.duration_months,
            product.compounding_frequency
        )
        amortization = InterestService.generate_amortization_schedule(
            credit_request.amount_requested,
            product.interest_rate,
            credit_request.duration_months,
            'compound'
        )
    else:
        interest_result = InterestService.calculate_simple_interest(
            credit_request.amount_requested,
            product.interest_rate,
            credit_request.duration_months
        )
        amortization = InterestService.generate_amortization_schedule(
            credit_request.amount_requested,
            product.interest_rate,
            credit_request.duration_months,
            'simple'
        )
    
    # Générer un numéro de contrat unique
    contract_number = f"MICROF-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    
    if request.method == 'POST':
        # VÉRIFICATION DES FONDS DISPONIBLES
        current_balance = CashService.get_balance(current_user.tenant_id)
        requested_amount = float(credit_request.amount_requested)
        
        if current_balance < requested_amount:
            flash(f'❌ Fonds insuffisants en caisse! Solde actuel: {current_balance:,.0f} FCFA, Montant demandé: {requested_amount:,.0f} FCFA', 'danger')
            return redirect(url_for('credit_requests.index'))
        
        # Créer le contrat
        contract = LoanContract(
            tenant_id=current_user.tenant_id,
            client_id=client.id,
            credit_request_id=credit_request.id,
            product_id=product.id,
            contract_number=contract_number,
            principal=credit_request.amount_requested,
            total_interest=interest_result['total_interest'],
            total_amount=interest_result['total_amount'],
            monthly_payment=amortization['monthly_payment'],
            start_date=datetime.now().date(),
            end_date=datetime.now().date() + timedelta(days=30 * credit_request.duration_months),
            interest_rate=product.interest_rate,
            interest_type=product.interest_type,
            processing_fee=float(product.processing_fee) * float(credit_request.amount_requested) / 100 if product.processing_fee else 0,
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
        
        # DÉBITER LA CAISSE
        CashService.withdraw(
            tenant_id=current_user.tenant_id,
            amount=credit_request.amount_requested,
            description=f"Déboursement contrat {contract_number} - {client.full_name}",
            user_id=current_user.id,
            contract_id=contract.id
        )
        
        # Mettre à jour le statut de la demande
        credit_request.status = 'disbursed'
        
        db.session.commit()
        
        flash(f'✅ Contrat {contract_number} créé avec succès! Montant total à rembourser: {interest_result["total_amount"]:,.0f} FCFA', 'success')
        return redirect(url_for('contracts.index'))
    
    # GET request - afficher le formulaire de confirmation
    return render_template('contracts/create.html', 
                         credit_request=credit_request, 
                         product=product, 
                         client=client,
                         interest_result=interest_result,
                         amortization=amortization,
                         contract_number=contract_number)

@bp.route('/view/<id>')
@login_required
def view(id):
    contract = LoanContract.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    repayments = Repayment.query.filter_by(contract_id=contract.id).order_by(Repayment.due_date).all()
    
    # Calculer les statistiques
    total_paid = sum(r.paid_amount for r in repayments if r.status == 'paid')
    remaining = contract.total_amount - total_paid
    paid_count = len([r for r in repayments if r.status == 'paid'])
    total_count = len(repayments)
    
    return render_template('contracts/view.html', 
                         contract=contract, 
                         repayments=repayments,
                         total_paid=total_paid,
                         remaining=remaining,
                         paid_count=paid_count,
                         total_count=total_count)

@bp.route('/repay/<repayment_id>', methods=['POST'])
@login_required
def repay(repayment_id):
    from app.services.cash_service import CashService
    from app.services.interest_service import InterestService
    
    repayment = Repayment.query.filter_by(id=repayment_id).first_or_404()
    contract = repayment.contract
    
    # Vérifier que le contrat appartient à la même microfinance
    if contract.tenant_id != current_user.tenant_id:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Calculer les jours de retard
    today = datetime.now().date()
    if today > repayment.due_date:
        days_late = (today - repayment.due_date).days
        penalty = InterestService.calculate_late_penalty(repayment.due_amount, days_late, contract.late_penalty_rate)
    else:
        penalty = 0
    
    total_paid = repayment.due_amount + penalty
    
    repayment.paid_date = today
    repayment.paid_amount = total_paid
    repayment.late_penalty = penalty
    repayment.status = 'paid'
    
    # CRÉDITER LA CAISSE
    CashService.deposit(
        tenant_id=current_user.tenant_id,
        amount=total_paid,
        description=f"Remboursement {contract.contract_number} - Échéance du {repayment.due_date.strftime('%d/%m/%Y')}",
        user_id=current_user.id,
        contract_id=contract.id
    )
    
    db.session.commit()
    
    flash(f'✅ Remboursement de {repayment.due_amount:,.0f} FCFA enregistré', 'success')
    if penalty > 0:
        flash(f'⚠️ Pénalité de retard appliquée: {penalty:,.0f} FCFA', 'warning')
    
    return redirect(url_for('contracts.view', id=contract.id))

@bp.route('/generate-schedule/<contract_id>')
@login_required
def generate_schedule(contract_id):
    contract = LoanContract.query.filter_by(id=contract_id, tenant_id=current_user.tenant_id).first_or_404()
    
    # Générer l'échéancier au format HTML pour impression
    repayments = Repayment.query.filter_by(contract_id=contract.id).order_by(Repayment.due_date).all()
    
    return render_template('contracts/schedule.html', contract=contract, repayments=repayments)

@bp.route('/print/<id>')
@login_required
def print_contract(id):
    contract = LoanContract.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    repayments = Repayment.query.filter_by(contract_id=contract.id).order_by(Repayment.due_date).all()
    
    # Recalculer l'échéancier complet pour l'affichage
    from app.services.interest_service import InterestService
    amortization = InterestService.generate_amortization_schedule(
        float(contract.principal),
        float(contract.interest_rate),
        len(repayments),
        contract.interest_type
    )
    
    return render_template('contracts/print_contract.html',
                         contract=contract,
                         repayments=repayments,
                         amortization_schedule=amortization['schedule'],
                         now=datetime.now())