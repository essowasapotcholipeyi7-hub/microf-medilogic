from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.holiday import Holiday
from datetime import datetime

bp = Blueprint('holidays', __name__, url_prefix='/holidays')

@bp.route('/')
@login_required
def index():
    holidays = Holiday.query.filter_by(tenant_id=current_user.tenant_id).all()
    return render_template('holidays/index.html', holidays=holidays)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        holiday_type = request.form.get('holiday_type')
        
        holiday = Holiday(
            tenant_id=current_user.tenant_id,
            name=name,
            holiday_type=holiday_type
        )
        
        if holiday_type == 'fixed':
            fixed_date = request.form.get('fixed_date')
            holiday.fixed_date = fixed_date
        else:
            movable_rule = request.form.get('movable_rule')
            holiday.movable_rule = movable_rule
            year = request.form.get('year')
            holiday.year = int(year) if year else None
        
        db.session.add(holiday)
        db.session.commit()
        
        flash(f'Jour férié "{name}" ajouté avec succès!', 'success')
        return redirect(url_for('holidays.index'))
    
    return render_template('holidays/add.html')

@bp.route('/delete/<id>')
@login_required
def delete(id):
    holiday = Holiday.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    db.session.delete(holiday)
    db.session.commit()
    flash(f'Jour férié "{holiday.name}" supprimé', 'warning')
    return redirect(url_for('holidays.index'))

@bp.route('/toggle/<id>')
@login_required
def toggle(id):
    holiday = Holiday.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    holiday.is_active = not holiday.is_active
    db.session.commit()
    status = "activé" if holiday.is_active else "désactivé"
    flash(f'Jour férié "{holiday.name}" {status}', 'info')
    return redirect(url_for('holidays.index'))

@bp.route('/preview/<int:year>')
@login_required
def preview(year):
    holidays = Holiday.query.filter_by(tenant_id=current_user.tenant_id, is_active=True).all()
    holiday_dates = []
    for holiday in holidays:
        date = holiday.get_date_for_year(year)
        if date:
            holiday_dates.append({
                'name': holiday.name,
                'date': date,
                'type': holiday.holiday_type
            })
    holiday_dates.sort(key=lambda x: x['date'])
    return render_template('holidays/preview.html', holidays=holiday_dates, year=year)