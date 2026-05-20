from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, TelField, TextAreaField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.tenant import Tenant

class RegistrationForm(FlaskForm):
    name = StringField('Nom de la microfinance', validators=[DataRequired(), Length(min=3, max=200)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone = TelField('Téléphone', validators=[DataRequired(), Length(max=20)])
    address = TextAreaField('Adresse', validators=[DataRequired()])
    admin_name = StringField('Nom de l\'administrateur', validators=[DataRequired(), Length(min=2, max=100)])
    admin_password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[DataRequired(), EqualTo('admin_password')])
    submit = SubmitField('S\'inscrire')
    
    def validate_email(self, email):
        tenant = Tenant.query.filter_by(email=email.data).first()
        if tenant:
            raise ValidationError('Cette adresse email est déjà utilisée.')

# Formulaire Client
class ClientForm(FlaskForm):
    first_name = StringField('Prénom', validators=[DataRequired(), Length(min=2, max=100)])
    last_name = StringField('Nom', validators=[DataRequired(), Length(min=2, max=100)])
    gender = StringField('Genre', validators=[DataRequired()])
    national_id = StringField('Pièce d\'identité', validators=[Length(max=50)])
    phone = StringField('Téléphone', validators=[DataRequired(), Length(max=20)])
    email = EmailField('Email', validators=[Email()])
    date_of_birth = StringField('Date de naissance')
    profession = StringField('Profession', validators=[Length(max=100)])
    address = TextAreaField('Adresse')
    city = StringField('Ville', validators=[Length(max=100)])
    monthly_income = StringField('Revenu mensuel (FCFA)')
    submit = SubmitField('Enregistrer')

# Formulaire Produit de prêt
class LoanProductForm(FlaskForm):
    name = StringField('Nom du produit', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    interest_rate = StringField('Taux d\'intérêt (%)', validators=[DataRequired()])
    interest_type = StringField('Type d\'intérêt', validators=[DataRequired()])
    compounding_frequency = StringField('Fréquence de composition', default='monthly')
    min_duration_months = StringField('Durée minimale (mois)', validators=[DataRequired()])
    max_duration_months = StringField('Durée maximale (mois)', validators=[DataRequired()])
    min_amount = StringField('Montant minimal (FCFA)', validators=[DataRequired()])
    max_amount = StringField('Montant maximal (FCFA)', validators=[DataRequired()])
    processing_fee = StringField('Frais de dossier (%)', default='0')
    late_penalty_rate = StringField('Pénalité de retard (%)', default='5')
    grace_period_days = StringField('Délai de grâce (jours)', default='0')
    requires_guarantor = BooleanField('Nécessite un garant ?')
    min_guarantors = StringField('Nombre minimum de garants', default='0')
    requires_collateral = BooleanField('Nécessite une garantie matérielle ?')
    submit = SubmitField('Enregistrer')

# Formulaire Demande de crédit
class CreditRequestForm(FlaskForm):
    client_id = StringField('Client', validators=[DataRequired()])
    product_id = StringField('Produit', validators=[DataRequired()])
    amount_requested = StringField('Montant demandé (FCFA)', validators=[DataRequired()])
    duration_months = StringField('Durée (mois)', validators=[DataRequired()])
    purpose = TextAreaField('Objet du prêt')
    guarantor_names = StringField('Noms des garants (séparés par virgule)')
    collateral_description = TextAreaField('Description de la garantie')
    submit = SubmitField('Soumettre la demande')

# Formulaire Approbation de crédit
class CreditApprovalForm(FlaskForm):
    approve = BooleanField('Approuver')
    rejection_reason = TextAreaField('Motif du rejet')
    submit = SubmitField('Valider')