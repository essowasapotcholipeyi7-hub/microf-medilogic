from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.client import Client
from app.models.loan_product import LoanProduct
from app.models.credit_request import CreditRequest
from app.forms import CreditRequestForm, CreditApprovalForm
from datetime import datetime
from app.services.eligibility_service import EligibilityService


bp = Blueprint('credit_requests', __name__, url_prefix='/credit-requests')

@bp.route('/')
@login_required
def index():
    requests = CreditRequest.query.filter_by(tenant_id=current_user.tenant_id).order_by(CreditRequest.created_at.desc()).all()
    return render_template('credit_requests/index.html', requests=requests)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    from app.services.eligibility_service import EligibilityService
    
    form = CreditRequestForm()
    
    # Remplir les choix dynamiques
    clients = Client.query.filter_by(tenant_id=current_user.tenant_id, is_active=True).all()
    products = LoanProduct.query.filter_by(tenant_id=current_user.tenant_id, is_active=True).all()
    
    if request.method == 'POST':
        form.client_id.data = request.form.get('client_id')
        form.product_id.data = request.form.get('product_id')
    
    if form.validate_on_submit():
        # Vérifier que le produit est actif
        product = LoanProduct.query.get(form.product_id.data)
        amount = float(form.amount_requested.data)
        duration = int(form.duration_months.data)
        
        # 1. VÉRIFIER L'ÉLIGIBILITÉ DU CLIENT
        is_eligible, reasons = EligibilityService.check_client_eligibility(
            form.client_id.data,
            amount,
            duration,
            product,
            db
        )
        
        if not is_eligible:
            for reason in reasons:
                flash(f'❌ {reason}', 'danger')
            return render_template('credit_requests/new.html', form=form, clients=clients, products=products)
        
        # 2. VALIDATION DES MONTANTS
        if amount < float(product.min_amount) or amount > float(product.max_amount):
            flash(f'Le montant doit être entre {product.min_amount:,.0f} et {product.max_amount:,.0f} FCFA', 'danger')
            return render_template('credit_requests/new.html', form=form, clients=clients, products=products)
        
        # 3. VALIDATION DE LA DURÉE
        if duration < product.min_duration_months or duration > product.max_duration_months:
            flash(f'La durée doit être entre {product.min_duration_months} et {product.max_duration_months} mois', 'danger')
            return render_template('credit_requests/new.html', form=form, clients=clients, products=products)
        
        # 4. CRÉER LA DEMANDE DE CRÉDIT
        credit_request = CreditRequest(
            tenant_id=current_user.tenant_id,
            client_id=form.client_id.data,
            product_id=form.product_id.data,
            agent_id=current_user.id,
            amount_requested=amount,
            duration_months=duration,
            purpose=form.purpose.data,
            guarantor_names=form.guarantor_names.data,
            collateral_description=form.collateral_description.data,
            status='pending'
        )
        db.session.add(credit_request)
        db.session.commit()
        
        flash(f'Demande de crédit pour {credit_request.client.full_name} soumise avec succès!', 'success')
        return redirect(url_for('credit_requests.index'))
    
    return render_template('credit_requests/new.html', form=form, clients=clients, products=products)

@bp.route('/view/<id>')
@login_required
def view(id):
    request = CreditRequest.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    return render_template('credit_requests/view.html', request=request)

@bp.route('/approve/<id>', methods=['GET', 'POST'])
@login_required
def approve(id):
    credit_request = CreditRequest.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    form = CreditApprovalForm()
    
    if form.validate_on_submit():
        if form.approve.data:
            credit_request.status = 'approved'
            credit_request.approved_by = current_user.id
            credit_request.approved_at = datetime.utcnow()
            flash(f'Demande approuvée pour {credit_request.client.full_name}', 'success')
        else:
            credit_request.status = 'rejected'
            credit_request.rejection_reason = form.rejection_reason.data
            flash(f'Demande rejetée', 'warning')
        
        db.session.commit()
        return redirect(url_for('credit_requests.index'))
    
    return render_template('credit_requests/approve.html', request=credit_request, form=form)

@bp.route('/delete/<id>')
@login_required
def delete(id):
    credit_request = CreditRequest.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    client_name = credit_request.client.full_name
    db.session.delete(credit_request)
    db.session.commit()
    flash(f'Demande de {client_name} supprimée', 'warning')
    return redirect(url_for('credit_requests.index'))