from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.tenant import Tenant
from app.models.user import User
from datetime import datetime

bp = Blueprint('super_admin', __name__, url_prefix='/super-admin')

@bp.route('/tenants')
@login_required
def tenants():
    # Seul le super admin peut acceder
    if current_user.role != 'super_admin':
        flash('Acces non autorise', 'danger')
        return redirect(url_for('dashboard.index'))
    
    tenants = Tenant.query.all()
    return render_template('super_admin/tenants.html', tenants=tenants)

@bp.route('/tenant/view/<id>')
@login_required
def view_tenant(id):
    if current_user.role != 'super_admin':
        flash('Acces non autorise', 'danger')
        return redirect(url_for('dashboard.index'))
    
    tenant = Tenant.query.get_or_404(id)
    users = User.query.filter_by(tenant_id=id).all()
    return render_template('super_admin/view_tenant.html', tenant=tenant, users=users)

@bp.route('/tenant/approve/<id>')
@login_required
def approve_tenant(id):
    if current_user.role != 'super_admin':
        flash('Acces non autorise', 'danger')
        return redirect(url_for('dashboard.index'))
    
    tenant = Tenant.query.get_or_404(id)
    tenant.status = 'approved'
    tenant.is_active = True
    
    # Activer tous les utilisateurs de cette microfinance
    users = User.query.filter_by(tenant_id=id).all()
    for user in users:
        user.is_active = True
    
    db.session.commit()
    flash(f'Microfinance {tenant.name} approuvee avec succes', 'success')
    return redirect(url_for('super_admin.tenants'))

@bp.route('/tenant/reject/<id>')
@login_required
def reject_tenant(id):
    if current_user.role != 'super_admin':
        flash('Acces non autorise', 'danger')
        return redirect(url_for('dashboard.index'))
    
    tenant = Tenant.query.get_or_404(id)
    tenant.status = 'rejected'
    tenant.is_active = False
    db.session.commit()
    
    flash(f'Microfinance {tenant.name} rejetee', 'warning')
    return redirect(url_for('super_admin.tenants'))

@bp.route('/tenant/suspend/<id>')
@login_required
def suspend_tenant(id):
    if current_user.role != 'super_admin':
        flash('Acces non autorise', 'danger')
        return redirect(url_for('dashboard.index'))
    
    tenant = Tenant.query.get_or_404(id)
    tenant.status = 'suspended'
    tenant.is_active = False
    
    # Desactiver tous les utilisateurs
    users = User.query.filter_by(tenant_id=id).all()
    for user in users:
        user.is_active = False
    
    db.session.commit()
    flash(f'Microfinance {tenant.name} suspendue', 'warning')
    return redirect(url_for('super_admin.tenants'))

@bp.route('/tenant/activate/<id>')
@login_required
def activate_tenant(id):
    if current_user.role != 'super_admin':
        flash('Acces non autorise', 'danger')
        return redirect(url_for('dashboard.index'))
    
    tenant = Tenant.query.get_or_404(id)
    tenant.status = 'approved'
    tenant.is_active = True
    
    # Reactiver tous les utilisateurs
    users = User.query.filter_by(tenant_id=id).all()
    for user in users:
        user.is_active = True
    
    db.session.commit()
    flash(f'Microfinance {tenant.name} reactived', 'success')
    return redirect(url_for('super_admin.tenants'))

@bp.route('/tenant/reset-password/<tenant_id>/<user_id>', methods=['GET', 'POST'])
@login_required
def reset_user_password(tenant_id, user_id):
    if current_user.role != 'super_admin':
        flash('Acces non autorise', 'danger')
        return redirect(url_for('dashboard.index'))
    
    tenant = Tenant.query.get_or_404(tenant_id)
    user = User.query.filter_by(id=user_id, tenant_id=tenant_id).first_or_404()
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or len(new_password) < 4:
            flash('Le mot de passe doit contenir au moins 4 caracteres', 'danger')
            return redirect(url_for('super_admin.reset_user_password', tenant_id=tenant_id, user_id=user_id))
        
        if new_password != confirm_password:
            flash('Les mots de passe ne correspondent pas', 'danger')
            return redirect(url_for('super_admin.reset_user_password', tenant_id=tenant_id, user_id=user_id))
        
        user.set_password(new_password)
        db.session.commit()
        
        flash(f'Mot de passe reinitialise pour {user.first_name} {user.last_name}', 'success')
        return redirect(url_for('super_admin.view_tenant', id=tenant_id))
    
    return render_template('super_admin/reset_password.html', tenant=tenant, user=user)

@bp.route('/tenant/delete/<id>')
@login_required
def delete_tenant(id):
    if current_user.role != 'super_admin':
        flash('Acces non autorise', 'danger')
        return redirect(url_for('dashboard.index'))
    
    tenant = Tenant.query.get_or_404(id)
    name = tenant.name
    
    # Supprimer tous les utilisateurs de cette microfinance
    User.query.filter_by(tenant_id=id).delete()
    
    # Supprimer la microfinance
    db.session.delete(tenant)
    db.session.commit()
    
    flash(f'Microfinance {name} supprimee', 'warning')
    return redirect(url_for('super_admin.tenants'))