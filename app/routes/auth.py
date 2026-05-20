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
        # Créer la microfinance
        tenant = Tenant(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            is_active=True
        )
        db.session.add(tenant)
        db.session.flush()  # Pour obtenir l'ID du tenant
        
        # Créer l'administrateur
        admin = User(
            tenant_id=tenant.id,
            username=form.email.data,
            email=form.email.data,
            first_name=form.admin_name.data,
            role='admin',
            is_active=True
        )
        admin.set_password(form.admin_password.data)
        db.session.add(admin)
        
        db.session.commit()
        
        flash('Votre microfinance a été créée avec succès ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'Bienvenue {user.first_name or user.username}!', 'success')
            
            # Redirection selon le rôle
            if user.role == 'admin':
                return redirect(url_for('dashboard.index'))
            else:
                # Pour les agents, rediriger vers la liste des clients
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