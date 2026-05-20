from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.services.cash_service import CashService
from decimal import Decimal

bp = Blueprint('cash', __name__, url_prefix='/cash')

@bp.route('/')
@login_required
def index():
    balance = CashService.get_balance(current_user.tenant_id)
    transactions = CashService.get_transactions(current_user.tenant_id)
    return render_template('cash/index.html', balance=balance, transactions=transactions)

@bp.route('/deposit', methods=['POST'])
@login_required
def deposit():
    amount = float(request.form.get('amount'))
    description = request.form.get('description')
    
    if amount <= 0:
        flash('Le montant doit être positif', 'danger')
        return redirect(url_for('cash.index'))
    
    CashService.deposit(
        tenant_id=current_user.tenant_id,
        amount=amount,
        description=description or "Dépôt manuel",
        user_id=current_user.id
    )
    
    flash(f'{amount:,.0f} FCFA ajoutés à la caisse', 'success')
    return redirect(url_for('cash.index'))