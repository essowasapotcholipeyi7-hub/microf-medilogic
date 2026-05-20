from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.forms import RegistrationForm
from app.models.tenant import Tenant
from app.models.user import User
from flask_login import login_user, logout_user, login_required

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Creer la microfinance avec statut 'pending'
        tenant = Tenant(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            status='pending',     # En attente d'approbation
            is_active=False       # Desactive jusqu'a approbation
        )
        db.session.add(tenant)
        db.session.flush()
        
        # Creer l'administrateur (desactive aussi)
        admin = User(
            tenant_id=tenant.id,
            username=form.email.data,
            email=form.email.data,
            first_name=form.admin_name.data,
            role='admin',
            is_active=False       # Desactive jusqu'a approbation
        )
        admin.set_password(form.admin_password.data)
        db.session.add(admin)
        
        db.session.commit()
        
        flash('Votre demande d\'inscription a ete envoyee. Elle sera traitee sous 48h.', 'success')
        return redirect(url_for('auth.pending'))
    
    return render_template('auth/register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Verifier si l'utilisateur est actif
            if not user.is_active:
                flash('Votre compte est en attente de validation. Veuillez patienter.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Verifier si la microfinance est active (sauf super admin)
            if user.role != 'super_admin':
                if user.tenant and not user.tenant.is_active:
                    flash('Votre microfinance est en attente de validation.', 'warning')
                    return redirect(url_for('auth.login'))
            
            login_user(user)
            flash(f'Bienvenue {user.first_name or user.username}!', 'success')
            
            if user.role == 'super_admin':
                return redirect(url_for('super_admin.tenants'))
            elif user.role == 'admin':
                return redirect(url_for('dashboard.index'))
            else:
                return redirect(url_for('clients.index'))
        else:
            flash('Email ou mot de passe incorrect', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('auth.login'))