from decimal import Decimal
from datetime import datetime
from app.models.client import Client
from app.models.loan_contract import LoanContract
from app.models.savings_account import SavingsAccount

class EligibilityService:
    
    @staticmethod
    def check_client_eligibility(client_id, requested_amount, duration_months, product, db_session):
        """
        Vérifie si un client est éligible à un prêt
        Retourne: (is_eligible, list_of_reasons)
        """
        client = Client.query.get(client_id)
        if not client:
            return False, ["Client non trouvé"]
        
        reasons = []
        
        # 1. Vérifier l'âge (au moins 18 ans)
        if client.date_of_birth:
            age = (datetime.now().date() - client.date_of_birth).days // 365
            if age < 18:
                reasons.append(f"Âge minimum requis: 18 ans (actuel: {age} ans)")
        
        # 2. Vérifier la pièce d'identité
        if not client.national_id:
            reasons.append("Pièce d'identité manquante")
        
        # 3. Vérifier le téléphone
        if not client.phone:
            reasons.append("Numéro de téléphone manquant")
        
        # 4. Vérifier les crédits actifs
        active_loans = LoanContract.query.filter_by(
            client_id=client.id, 
            status='active'
        ).count()
        
        if active_loans >= 2:
            reasons.append(f"Client a déjà {active_loans} crédits actifs (maximum: 2)")
        
        # 5. Vérifier l'historique des défauts
        defaulted_loans = LoanContract.query.filter_by(
            client_id=client.id, 
            status='defaulted'
        ).count()
        
        if defaulted_loans > 0:
            reasons.append(f"Antécédent de défaut de paiement ({defaulted_loans} crédit(s) impayé(s))")
        
        # 6. Vérifier la capacité de remboursement
        if client.monthly_income:
            # Convertir en float pour les calculs
            monthly_income = float(client.monthly_income)
            
            # Calculer la mensualité approximative (taux 12%)
            monthly_rate = 0.12 / 12
            monthly_payment = requested_amount * (monthly_rate * (1 + monthly_rate) ** duration_months) / ((1 + monthly_rate) ** duration_months - 1)
            
            max_monthly_payment = monthly_income * 0.5  # max 50% du revenu
            
            if monthly_payment > max_monthly_payment:
                reasons.append(f"Mensualité trop élevée par rapport au revenu (max: {max_monthly_payment:,.0f} FCFA, proposé: {monthly_payment:,.0f} FCFA)")
        
        # 7. Vérifier le fonds d'épargne (optionnel selon produit)
        savings = SavingsAccount.query.filter_by(client_id=client.id).first()
        required_savings = float(requested_amount) * 0.10  # 10% du montant
        
        if hasattr(product, 'requires_savings') and product.requires_savings:
            savings_balance = float(savings.balance) if savings else 0
            if savings_balance < required_savings:
                reasons.append(f"Fonds d'épargne insuffisant (requis: {required_savings:,.0f} FCFA, disponible: {savings_balance:,.0f} FCFA)")
        
        # 8. Vérifier la garantie
        if product.requires_guarantor:
            # Vérifier si le client est dans un groupe solidaire
            from app.models.solidarity_group import GroupMember
            group_membership = GroupMember.query.filter_by(client_id=client.id).first()
            if not group_membership:
                reasons.append("Le client doit être membre d'un groupe solidaire pour ce produit")
        
        # 9. Vérifier le montant minimum et maximum
        if requested_amount < float(product.min_amount):
            reasons.append(f"Montant minimum: {float(product.min_amount):,.0f} FCFA")
        if requested_amount > float(product.max_amount):
            reasons.append(f"Montant maximum: {float(product.max_amount):,.0f} FCFA")
        
        # 10. Vérifier la durée
        if duration_months < product.min_duration_months:
            reasons.append(f"Durée minimale: {product.min_duration_months} mois")
        if duration_months > product.max_duration_months:
            reasons.append(f"Durée maximale: {product.max_duration_months} mois")
        
        is_eligible = len(reasons) == 0
        return is_eligible, reasons
    
    @staticmethod
    def get_client_summary(client_id):
        """Retourne un résumé de la situation du client"""
        client = Client.query.get(client_id)
        if not client:
            return None
        
        # Crédits actifs
        active_loans = LoanContract.query.filter_by(client_id=client.id, status='active').all()
        total_active = sum(float(l.total_amount) for l in active_loans)
        
        # Historique
        completed_loans = LoanContract.query.filter_by(client_id=client.id, status='completed').count()
        
        # Épargne
        savings = SavingsAccount.query.filter_by(client_id=client.id).first()
        savings_balance = float(savings.balance) if savings else 0
        
        # Capacité d'emprunt (basée sur revenu)
        if client.monthly_income:
            monthly_income = float(client.monthly_income)
            max_loan_amount = (monthly_income * 0.4) * 12 * 2  # 40% revenu sur 24 mois
        else:
            max_loan_amount = 0
        
        return {
            'client': client,
            'active_loans_count': len(active_loans),
            'total_active_amount': total_active,
            'completed_loans_count': completed_loans,
            'savings_balance': savings_balance,
            'max_loan_amount': max_loan_amount,
            'monthly_income': float(client.monthly_income) if client.monthly_income else 0
        }