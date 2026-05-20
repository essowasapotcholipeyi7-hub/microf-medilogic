from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.client import Client
from app.forms import ClientForm
from datetime import datetime

bp = Blueprint('clients', __name__, url_prefix='/clients')

@bp.route('/')
@login_required
def index():
    search = request.args.get('search', '')
    gender_filter = request.args.get('gender', '')
    
    query = Client.query.filter_by(tenant_id=current_user.tenant_id)
    
    # Recherche par nom ou téléphone
    if search:
        query = query.filter(
            db.or_(
                Client.first_name.ilike(f'%{search}%'),
                Client.last_name.ilike(f'%{search}%'),
                Client.phone.ilike(f'%{search}%'),
                Client.national_id.ilike(f'%{search}%')
            )
        )
    
    # Filtre par genre
    if gender_filter:
        query = query.filter_by(gender=gender_filter)
    
    clients = query.order_by(Client.created_at.desc()).all()
    
    # Statistiques
    total_clients = Client.query.filter_by(tenant_id=current_user.tenant_id).count()
    male_count = Client.query.filter_by(tenant_id=current_user.tenant_id, gender='male').count()
    female_count = Client.query.filter_by(tenant_id=current_user.tenant_id, gender='female').count()
    
    return render_template('clients/index.html', 
                         clients=clients, 
                         search=search,
                         gender_filter=gender_filter,
                         total_clients=total_clients,
                         male_count=male_count,
                         female_count=female_count)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    from app.models.user import User
    agents = User.query.filter_by(tenant_id=current_user.tenant_id, role='agent', is_active=True).all()
    
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            tenant_id=current_user.tenant_id,
            agent_id=request.form.get('agent_id') or None,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            gender=form.gender.data,
            national_id=form.national_id.data,
            phone=form.phone.data,
            email=form.email.data,
            profession=form.profession.data,
            address=form.address.data,
            city=form.city.data,
            monthly_income=float(form.monthly_income.data) if form.monthly_income.data else None
        )
        
        if form.date_of_birth.data:
            try:
                client.date_of_birth = datetime.strptime(form.date_of_birth.data, '%Y-%m-%d')
            except:
                pass
        
        db.session.add(client)
        db.session.commit()
        
        flash(f'Client {client.full_name} ajouté avec succès!', 'success')
        return redirect(url_for('clients.index'))
    
    return render_template('clients/form.html', form=form, title='Ajouter un client', agents=agents)

@bp.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    client = Client.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    form = ClientForm(obj=client)
    
    if form.validate_on_submit():
        client.first_name = form.first_name.data
        client.last_name = form.last_name.data
        client.gender = form.gender.data
        client.national_id = form.national_id.data
        client.phone = form.phone.data
        client.email = form.email.data
        client.profession = form.profession.data
        client.address = form.address.data
        client.city = form.city.data
        client.monthly_income = float(form.monthly_income.data) if form.monthly_income.data else None
        
        db.session.commit()
        flash(f'Client {client.full_name} modifié avec succès!', 'success')
        return redirect(url_for('clients.index'))
    
    return render_template('clients/form.html', form=form, title='Modifier client', client=client)

@bp.route('/delete/<id>')
@login_required
def delete(id):
    client = Client.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    db.session.delete(client)
    db.session.commit()
    flash(f'Client {client.full_name} supprimé', 'warning')
    return redirect(url_for('clients.index'))