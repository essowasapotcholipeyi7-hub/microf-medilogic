from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.client import Client
from app.models.loan_contract import LoanContract
from app.models.credit_request import CreditRequest
from app.models.repayment import Repayment
from app.services.cash_service import CashService
from datetime import datetime, timedelta
from sqlalchemy import func
import urllib.parse

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    tenant_id = current_user.tenant_id
    
    # Statistiques de base
    total_clients = Client.query.filter_by(tenant_id=tenant_id).count()
    male_count = Client.query.filter_by(tenant_id=tenant_id, gender='male').count()
    female_count = Client.query.filter_by(tenant_id=tenant_id, gender='female').count()
    
    active_loans = LoanContract.query.filter_by(tenant_id=tenant_id, status='active').count()
    pending_requests = CreditRequest.query.filter_by(tenant_id=tenant_id, status='pending').count()
    
    # Taux de recouvrement
    total_disbursed = LoanContract.query.filter_by(tenant_id=tenant_id).with_entities(func.sum(LoanContract.principal)).scalar() or 0
    total_repaid = Repayment.query.join(LoanContract).filter(
        LoanContract.tenant_id == tenant_id,
        Repayment.status == 'paid'
    ).with_entities(func.sum(Repayment.paid_amount)).scalar() or 0
    
    recovery_rate = (total_repaid / total_disbursed * 100) if total_disbursed > 0 else 0
    
    # Données pour les graphiques (6 derniers mois)
    months = []
    loan_amounts = []
    cash_amounts = []
    
    for i in range(5, -1, -1):
        month_date = datetime.now().replace(day=1) - timedelta(days=30 * i)
        month_name = month_date.strftime('%b %Y')
        months.append(month_name)
        
        # Crédits du mois
        total = LoanContract.query.filter(
            LoanContract.tenant_id == tenant_id,
            LoanContract.start_date >= month_date,
            LoanContract.start_date < month_date + timedelta(days=32)
        ).with_entities(func.sum(LoanContract.principal)).scalar() or 0
        loan_amounts.append(float(total))
        
        # Solde caisse à la fin du mois (approx)
        # On récupère les transactions jusqu'à la fin du mois
        end_of_month = (month_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        cash_balance = CashService.get_balance_at_date(tenant_id, end_of_month)
        cash_amounts.append(cash_balance)
    
    # Récupérer les retards de paiement (≥ 7 jours)
    today = datetime.now().date()
    late_repayments = []
    
    overdue_repayments = Repayment.query.join(LoanContract).filter(
        LoanContract.tenant_id == tenant_id,
        Repayment.status == 'pending',
        Repayment.due_date < today
    ).all()
    
    for repayment in overdue_repayments:
        days_late = (today - repayment.due_date).days
        if days_late >= 7:
            client = repayment.contract.client
            phone = client.phone or ''
            clean_phone = ''.join(filter(str.isdigit, phone))
            
            if len(clean_phone) >= 8:
                if not clean_phone.startswith('228') and len(clean_phone) == 8:
                    clean_phone = '228' + clean_phone
                
                message = f"Bonjour {client.full_name}, votre échéance de {repayment.due_amount:,.0f} FCFA du {repayment.due_date.strftime('%d/%m/%Y')} est en retard de {days_late} jours. Veuillez régulariser. Merci."
                encoded_msg = urllib.parse.quote(message)
                whatsapp_link = f"https://wa.me/{clean_phone}?text={encoded_msg}"
            else:
                whatsapp_link = "#"
            
            late_repayments.append({
                'client_name': client.full_name,
                'contract_number': repayment.contract.contract_number,
                'amount_due': float(repayment.due_amount),
                'days_late': days_late,
                'whatsapp_link': whatsapp_link
            })
    
    return render_template('dashboard/index.html',
                         user=current_user,
                         total_clients=total_clients,
                         male_count=male_count,
                         female_count=female_count,
                         active_loans=active_loans,
                         pending_requests=pending_requests,
                         recovery_rate=recovery_rate,
                         loan_labels=months,
                         loan_data=loan_amounts,
                         cash_data=cash_amounts,
                         now=datetime.now(),
                         late_repayments=late_repayments)