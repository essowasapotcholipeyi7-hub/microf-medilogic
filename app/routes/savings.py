from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.client import Client
from app.models.savings_account import SavingsAccount, SavingsTransaction  # Ajouter SavingsTransaction ici
from app.services.savings_service import SavingsService
from decimal import Decimal

bp = Blueprint('savings', __name__, url_prefix='/savings')

@bp.route('/')
@login_required
def index():
    # Tous les comptes d'épargne de la microfinance
    accounts = SavingsAccount.query.filter_by(tenant_id=current_user.tenant_id).all()
    
    # Statistiques
    total_balance = sum(float(a.balance) for a in accounts)
    total_accounts = len(accounts)
    total_interest = sum(float(a.total_interest_earned) for a in accounts)
    
    return render_template('savings/index.html', 
                         accounts=accounts,
                         total_balance=total_balance,
                         total_accounts=total_accounts,
                         total_interest=total_interest)

@bp.route('/client/<client_id>')
@login_required
def client_account(client_id):
    client = Client.query.filter_by(id=client_id, tenant_id=current_user.tenant_id).first_or_404()
    account = SavingsService.get_or_create_account(current_user.tenant_id, client_id)
    
    # Récupérer les transactions
    transactions = account.transactions.order_by(SavingsTransaction.created_at.desc()).limit(50).all()
    
    # Calculer les intérêts en cours
    pending_interest = SavingsService.calculate_interest(account)
    
    return render_template('savings/client_account.html', 
                         client=client,
                         account=account,
                         transactions=transactions,
                         pending_interest=pending_interest)

@bp.route('/deposit/<account_id>', methods=['POST'])
@login_required
def deposit(account_id):
    amount = float(request.form.get('amount'))
    description = request.form.get('description', '')
    
    if amount <= 0:
        flash('Le montant doit être positif', 'danger')
        return redirect(request.referrer)
    
    try:
        SavingsService.deposit(account_id, amount, current_user.id, description)
        flash(f'✅ Dépôt de {amount:,.0f} FCFA effectué avec succès', 'success')
    except Exception as e:
        flash(f'❌ Erreur: {str(e)}', 'danger')
    
    return redirect(request.referrer)

@bp.route('/withdraw/<account_id>', methods=['POST'])
@login_required
def withdraw(account_id):
    amount = float(request.form.get('amount'))
    description = request.form.get('description', '')
    
    if amount <= 0:
        flash('Le montant doit être positif', 'danger')
        return redirect(request.referrer)
    
    try:
        SavingsService.withdraw(account_id, amount, current_user.id, description)
        flash(f'✅ Retrait de {amount:,.0f} FCFA effectué avec succès', 'success')
    except Exception as e:
        flash(f'❌ Erreur: {str(e)}', 'danger')
    
    return redirect(request.referrer)

@bp.route('/pay-interest/<account_id>')
@login_required
def pay_interest(account_id):
    try:
        transaction = SavingsService.pay_interest(account_id, current_user.id)
        if transaction:
            flash(f'✅ Intérêts de {transaction.amount:,.0f} FCFA versés', 'success')
        else:
            flash('ℹ️ Aucun intérêt à verser pour le moment', 'info')
    except Exception as e:
        flash(f'❌ Erreur: {str(e)}', 'danger')
    
    return redirect(request.referrer)

@bp.route('/update-rate/<account_id>', methods=['POST'])
@login_required
def update_rate(account_id):
    new_rate = float(request.form.get('interest_rate'))
    
    if new_rate < 0 or new_rate > 30:
        flash('Le taux doit être entre 0 et 30%', 'danger')
        return redirect(request.referrer)
    
    account = SavingsAccount.query.filter_by(id=account_id, tenant_id=current_user.tenant_id).first_or_404()
    account.interest_rate = new_rate
    db.session.commit()
    
    flash(f'✅ Taux d\'intérêt modifié à {new_rate}%', 'success')
    return redirect(request.referrer)

@bp.route('/print/<transaction_id>')
@login_required
def print_receipt(transaction_id):
    from app.models.savings_account import SavingsTransaction
    from datetime import datetime
    
    transaction = SavingsTransaction.query.filter_by(
        id=transaction_id, 
        tenant_id=current_user.tenant_id
    ).first_or_404()
    
    # Récupérer les 5 dernières transactions du compte
    recent_transactions = SavingsTransaction.query.filter_by(
        account_id=transaction.account_id
    ).order_by(SavingsTransaction.created_at.desc()).limit(5).all()
    
    return render_template('savings/print_receipt.html',
                         transaction=transaction,
                         recent_transactions=recent_transactions,
                         now=datetime.now())