from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.loan_product import LoanProduct
from app.forms import LoanProductForm

bp = Blueprint('products', __name__, url_prefix='/products')

@bp.route('/')
@login_required
def index():
    products = LoanProduct.query.filter_by(tenant_id=current_user.tenant_id).all()
    return render_template('products/index.html', products=products)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = LoanProductForm()
    if form.validate_on_submit():
        product = LoanProduct(
            tenant_id=current_user.tenant_id,
            name=form.name.data,
            description=form.description.data,
            interest_rate=float(form.interest_rate.data),
            interest_type=form.interest_type.data,
            compounding_frequency=form.compounding_frequency.data,
            min_duration_months=int(form.min_duration_months.data),
            max_duration_months=int(form.max_duration_months.data),
            min_amount=float(form.min_amount.data),
            max_amount=float(form.max_amount.data),
            processing_fee=float(form.processing_fee.data) if form.processing_fee.data else 0,
            late_penalty_rate=float(form.late_penalty_rate.data) if form.late_penalty_rate.data else 5,
            grace_period_days=int(form.grace_period_days.data) if form.grace_period_days.data else 0,
            requires_guarantor=form.requires_guarantor.data,
            min_guarantors=int(form.min_guarantors.data) if form.min_guarantors.data else 0,
            requires_collateral=form.requires_collateral.data
        )
        db.session.add(product)
        db.session.commit()
        flash(f'Produit "{product.name}" créé avec succès!', 'success')
        return redirect(url_for('products.index'))
    return render_template('products/form.html', form=form, title='Ajouter un produit')

@bp.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    product = LoanProduct.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    form = LoanProductForm(obj=product)
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.interest_rate = float(form.interest_rate.data)
        product.interest_type = form.interest_type.data
        product.compounding_frequency = form.compounding_frequency.data
        product.min_duration_months = int(form.min_duration_months.data)
        product.max_duration_months = int(form.max_duration_months.data)
        product.min_amount = float(form.min_amount.data)
        product.max_amount = float(form.max_amount.data)
        product.processing_fee = float(form.processing_fee.data) if form.processing_fee.data else 0
        product.late_penalty_rate = float(form.late_penalty_rate.data) if form.late_penalty_rate.data else 5
        product.grace_period_days = int(form.grace_period_days.data) if form.grace_period_days.data else 0
        product.requires_guarantor = form.requires_guarantor.data
        product.min_guarantors = int(form.min_guarantors.data) if form.min_guarantors.data else 0
        product.requires_collateral = form.requires_collateral.data
        db.session.commit()
        flash(f'Produit "{product.name}" modifié!', 'success')
        return redirect(url_for('products.index'))
    return render_template('products/form.html', form=form, title='Modifier produit', product=product)

@bp.route('/delete/<id>')
@login_required
def delete(id):
    product = LoanProduct.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    db.session.delete(product)
    db.session.commit()
    flash(f'Produit "{product.name}" supprimé', 'warning')
    return redirect(url_for('products.index'))

@bp.route('/toggle/<id>')
@login_required
def toggle(id):
    product = LoanProduct.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    product.is_active = not product.is_active
    db.session.commit()
    status = "activé" if product.is_active else "désactivé"
    flash(f'Produit "{product.name}" {status}', 'info')
    return redirect(url_for('products.index'))