from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.client import Client
from app.models.tontine import TontineMember, TontinePayment
from app.services.cash_service import CashService
from datetime import datetime, date, timedelta
from datetime import datetime
from datetime import date  # Ajouter en haut



bp = Blueprint('tontine', __name__, url_prefix='/tontine')

@bp.route('/')
@login_required
def index():
    members = TontineMember.query.filter_by(tenant_id=current_user.tenant_id, is_active=True).all()
    
    stats = {
        'total_members': len(members),
        'total_saved': sum(m.total_paid for m in members),
        'total_interest': sum(m.interest_earned for m in members),
        'total_missing_days': sum(m.days_missing for m in members)
    }
    
    return render_template('tontine/index.html', members=members, stats=stats)


@bp.route('/register/<client_id>', methods=['GET', 'POST'])
@login_required
def register(client_id):
    client = Client.query.filter_by(id=client_id, tenant_id=current_user.tenant_id).first_or_404()
    
    # Vérifier si déjà inscrit
    existing = TontineMember.query.filter_by(client_id=client_id, is_active=True).first()
    if existing:
        flash(f'{client.full_name} est deja inscrit a la tontine', 'warning')
        return redirect(url_for('tontine.index'))
    
    if request.method == 'POST':
        daily_amount = float(request.form.get('daily_amount', 500))
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        
        member = TontineMember(
            tenant_id=current_user.tenant_id,
            client_id=client.id,
            daily_amount=daily_amount,
            start_date=start_date,
            is_active=True
        )
        db.session.add(member)
        db.session.commit()
        
        flash(f'{client.full_name} inscrit a la tontine avec un montant de {daily_amount:,.0f} FCFA/jour', 'success')
        return redirect(url_for('tontine.index'))
    
    return render_template('tontine/register.html', client=client, now=datetime.now())

@bp.route('/pay/<member_id>', methods=['POST'])
@login_required
def pay(member_id):
    member = TontineMember.query.filter_by(id=member_id, tenant_id=current_user.tenant_id).first_or_404()
    
    days = int(request.form.get('days', 1))
    if days < 1 or days > 30:
        flash('Le nombre de jours doit etre entre 1 et 30', 'danger')
        return redirect(url_for('tontine.view_member', member_id=member_id))
    
    amount = member.daily_amount * days
    
    # Vérifier que les dates ne sont pas déjà payées
    today = date.today()
    paid_dates = {p.payment_date for p in member.payments.filter_by(status='paid').all()}
    
    missing_dates = []
    for i in range(days):
        check_date = today + timedelta(days=i)
        if check_date < member.start_date:
            flash(f'La date {check_date.strftime("%d/%m/%Y")} est avant la date de debut', 'danger')
            return redirect(url_for('tontine.view_member', member_id=member_id))
        if check_date in paid_dates:
            flash(f'La date {check_date.strftime("%d/%m/%Y")} a deja ete payee', 'danger')
            return redirect(url_for('tontine.view_member', member_id=member_id))
        missing_dates.append(check_date)
    
    # Créer la transaction pour la première date (celle du jour)
    payment = TontinePayment(
        member_id=member.id,
        tenant_id=current_user.tenant_id,
        payment_date=missing_dates[0],
        amount=amount,
        days_covered=days,
        status='paid',
        paid_at=datetime.now(),
        created_by=current_user.id
    )
    db.session.add(payment)
    
    # Créditer la caisse
    CashService.deposit(
        tenant_id=current_user.tenant_id,
        amount=amount,
        description=f"Tontine: paiement de {days} jour(s) pour {member.client.full_name}",
        user_id=current_user.id
    )
    
    db.session.commit()
    
    flash(f'Paiement de {amount:,.0f} FCFA enregistre pour {member.client.full_name} ({days} jour(s))', 'success')
    return redirect(url_for('tontine.view_member', member_id=member_id))

@bp.route('/member/<member_id>')
@login_required
def view_member(member_id):
    member = TontineMember.query.filter_by(id=member_id, tenant_id=current_user.tenant_id).first_or_404()
    payments = member.payments.order_by(TontinePayment.payment_date.desc()).all()
    next_dates = member.next_payment_dates
    
    return render_template('tontine/member.html', 
                         member=member, 
                         payments=payments, 
                         next_dates=next_dates,
                         now=datetime.now(),
                         today=date.today())

@bp.route('/edit/<member_id>', methods=['GET', 'POST'])
@login_required
def edit(member_id):
    member = TontineMember.query.filter_by(id=member_id, tenant_id=current_user.tenant_id).first_or_404()
    
    if request.method == 'POST':
        member.daily_amount = float(request.form.get('daily_amount'))
        member.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        member.interest_rate = float(request.form.get('interest_rate', 5))
        db.session.commit()
        
        flash(f'Parametres modifies pour {member.client.full_name}', 'success')
        return redirect(url_for('tontine.view_member', member_id=member.id))
    
    return render_template('tontine/edit.html', member=member)

@bp.route('/unregister/<member_id>')
@login_required
def unregister(member_id):
    member = TontineMember.query.filter_by(id=member_id, tenant_id=current_user.tenant_id).first_or_404()
    
    # Vérifier les conditions de retrait
    if not member.can_withdraw:
        days_left = 60 - (date.today() - member.start_date).days
        flash(f'Retrait possible seulement apres 60 jours. Encore {days_left} jours.', 'warning')
        return redirect(url_for('tontine.view_member', member_id=member.id))
    
    # Calculer le montant à retirer
    withdraw_amount = member.total_with_interest
    
    # Enregistrer le retrait
    member.is_active = False
    
    # Débiter la caisse
    CashService.withdraw(
        tenant_id=current_user.tenant_id,
        amount=withdraw_amount,
        description=f"Tontine: retrait pour {member.client.full_name}",
        user_id=current_user.id
    )
    
    db.session.commit()
    
    flash(f'{member.client.full_name} a ete desinscrit. Montant retire: {withdraw_amount:,.0f} FCFA', 'success')
    return redirect(url_for('tontine.index'))