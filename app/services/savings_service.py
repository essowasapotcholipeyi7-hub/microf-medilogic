from decimal import Decimal
from datetime import datetime, timedelta
from flask import flash
from app import db
from app.models.savings_account import SavingsAccount, SavingsTransaction
from app.models.cash_fund import CashFund
from app.services.cash_service import CashService

class SavingsService:
    
    @staticmethod
    def create_account(tenant_id, client_id, interest_rate=5.0):
        """Crée un compte d'épargne pour un client"""
        import uuid
        account_number = f"EPARGNE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        account = SavingsAccount(
            tenant_id=tenant_id,
            client_id=client_id,
            account_number=account_number,
            balance=0,
            interest_rate=interest_rate,
            status='active'
        )
        db.session.add(account)
        db.session.commit()
        
        return account
    
    @staticmethod
    def deposit(account_id, amount, user_id=None, description=None):
        """Dépôt d'argent sur un compte épargne"""
        account = SavingsAccount.query.get(account_id)
        if not account:
            raise ValueError("Compte non trouvé")
        
        amount = Decimal(str(amount))
        
        # Enregistrer la transaction
        new_balance = account.balance + amount
        
        transaction = SavingsTransaction(
            tenant_id=account.tenant_id,
            account_id=account.id,
            transaction_type='deposit',
            amount=amount,
            balance_after=new_balance,
            description=description or f"Dépôt de {amount:,.0f} FCFA",
            created_by=user_id
        )
        
        account.balance = new_balance
        
        # CRÉDITER LA CAISSE (l'argent entre dans la caisse)
        CashService.deposit(
            tenant_id=account.tenant_id,
            amount=amount,
            description=f"Dépôt épargne {account.account_number} - {account.client.full_name}",
            user_id=user_id
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return transaction
    
    @staticmethod
    def withdraw(account_id, amount, user_id=None, description=None):
        """Retrait d'argent d'un compte épargne"""
        account = SavingsAccount.query.get(account_id)
        if not account:
            raise ValueError("Compte non trouvé")
        
        amount = Decimal(str(amount))
        
        if account.balance < amount:
            raise ValueError(f"Solde insuffisant. Solde: {account.balance:,.0f} FCFA, Demandé: {amount:,.0f} FCFA")
        
        new_balance = account.balance - amount
        
        transaction = SavingsTransaction(
            tenant_id=account.tenant_id,
            account_id=account.id,
            transaction_type='withdrawal',
            amount=amount,
            balance_after=new_balance,
            description=description or f"Retrait de {amount:,.0f} FCFA",
            created_by=user_id
        )
        
        account.balance = new_balance
        
        # DÉBIter LA CAISSE (l'argent sort de la caisse)
        CashService.withdraw(
            tenant_id=account.tenant_id,
            amount=amount,
            description=f"Retrait épargne {account.account_number} - {account.client.full_name}",
            user_id=user_id
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return transaction
    
    @staticmethod
    def calculate_interest(account, current_date=None):
        """Calcule les intérêts à payer sur un compte"""
        if current_date is None:
            current_date = datetime.now().date()
        
        # Nombre de jours depuis le dernier calcul
        last_date = account.last_interest_date
        days_diff = (current_date - last_date).days
        
        if days_diff <= 0:
            return 0
        
        # Formule: Intérêt = Solde * taux * (jours/365)
        rate = float(account.interest_rate) / 100
        interest = float(account.balance) * rate * (days_diff / 365)
        
        return Decimal(str(round(interest, 2)))
    
    @staticmethod
    def pay_interest(account_id, user_id=None):
        """Verse les intérêts sur un compte"""
        account = SavingsAccount.query.get(account_id)
        if not account:
            raise ValueError("Compte non trouvé")
        
        current_date = datetime.now().date()
        interest = SavingsService.calculate_interest(account, current_date)
        
        if interest <= 0:
            return None
        
        # Ajouter les intérêts au compte
        new_balance = account.balance + interest
        
        transaction = SavingsTransaction(
            tenant_id=account.tenant_id,
            account_id=account.id,
            transaction_type='interest',
            amount=interest,
            balance_after=new_balance,
            description=f"Intérêts au taux de {account.interest_rate}% du {account.last_interest_date} au {current_date}",
            created_by=user_id
        )
        
        account.balance = new_balance
        account.last_interest_date = current_date
        
        # DÉBITER LA CAISSE (la microfinance paie les intérêts)
        CashService.withdraw(
            tenant_id=account.tenant_id,
            amount=interest,
            description=f"Paiement intérêts épargne {account.account_number}",
            user_id=user_id
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return transaction
    
    @staticmethod
    def get_account_by_client(tenant_id, client_id):
        """Récupère le compte épargne d'un client"""
        return SavingsAccount.query.filter_by(tenant_id=tenant_id, client_id=client_id).first()
    
    @staticmethod
    def get_or_create_account(tenant_id, client_id, interest_rate=5.0):
        """Récupère ou crée un compte épargne"""
        account = SavingsService.get_account_by_client(tenant_id, client_id)
        if not account:
            account = SavingsService.create_account(tenant_id, client_id, interest_rate)
        return account