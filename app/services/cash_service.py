from decimal import Decimal
from flask import flash
from app import db
from app.models.cash_fund import CashFund, CashTransaction
from datetime import datetime

class CashService:
    
    @staticmethod
    def get_or_create_fund(tenant_id):
        """Récupère ou crée le fonds de caisse pour une microfinance"""
        fund = CashFund.query.filter_by(tenant_id=tenant_id).first()
        if not fund:
            fund = CashFund(tenant_id=tenant_id, balance=0, min_balance=0)
            db.session.add(fund)
            db.session.commit()
        return fund
    
    @staticmethod
    def check_sufficient_funds(tenant_id, amount):
        """Vérifie si le fonds a assez d'argent"""
        fund = CashService.get_or_create_fund(tenant_id)
        return float(fund.balance) >= float(amount)
    
    @staticmethod
    def deposit(tenant_id, amount, description, user_id=None, contract_id=None):
        """Ajoute de l'argent à la caisse"""
        fund = CashService.get_or_create_fund(tenant_id)
        amount = Decimal(str(amount))
        
        fund.balance += amount
        
        transaction = CashTransaction(
            tenant_id=tenant_id,
            contract_id=contract_id,
            transaction_type='deposit',
            amount=amount,
            description=description,
            balance_after=fund.balance,
            created_by=user_id
        )
        db.session.add(transaction)
        db.session.commit()
        
        return True
    
    @staticmethod
    def withdraw(tenant_id, amount, description, user_id=None, contract_id=None):
        """Retire de l'argent de la caisse (déboursement)"""
        fund = CashService.get_or_create_fund(tenant_id)
        amount = Decimal(str(amount))
        
        if fund.balance < amount:
            raise ValueError(f"Fonds insuffisants. Solde: {fund.balance} FCFA, Demandé: {amount} FCFA")
        
        fund.balance -= amount
        
        transaction = CashTransaction(
            tenant_id=tenant_id,
            contract_id=contract_id,
            transaction_type='withdrawal',
            amount=amount,
            description=description,
            balance_after=fund.balance,
            created_by=user_id
        )
        db.session.add(transaction)
        db.session.commit()
        
        return True
    
    @staticmethod
    def get_balance(tenant_id):
        """Retourne le solde actuel"""
        fund = CashService.get_or_create_fund(tenant_id)
        return float(fund.balance)
    
    @staticmethod
    def get_transactions(tenant_id, limit=50):
        """Retourne l'historique des transactions"""
        return CashTransaction.query.filter_by(tenant_id=tenant_id).order_by(CashTransaction.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_balance_at_date(tenant_id, target_date):
        """Retourne le solde de la caisse à une date donnée"""
        from datetime import datetime, date
        
        # Convertir la date en datetime pour la comparaison
        if isinstance(target_date, date) and not isinstance(target_date, datetime):
            target_datetime = datetime.combine(target_date, datetime.max.time())
        else:
            target_datetime = target_date
        
        # Récupérer la dernière transaction avant ou à cette date
        last_transaction = CashTransaction.query.filter(
            CashTransaction.tenant_id == tenant_id,
            CashTransaction.created_at <= target_datetime
        ).order_by(CashTransaction.created_at.desc()).first()
        
        if last_transaction:
            return float(last_transaction.balance_after)
        
        # Si aucune transaction, retourner le solde initial
        fund = CashFund.query.filter_by(tenant_id=tenant_id).first()
        if fund:
            return float(fund.balance)
        
        return 0.0