from decimal import Decimal
from datetime import datetime, timedelta
import math

class InterestService:
    
    @staticmethod
    def calculate_compound_interest(principal, annual_rate, duration_months, compounding_frequency='monthly'):
        """
        Calcule les intérêts composés
        principal: montant du prêt
        annual_rate: taux annuel en pourcentage (ex: 12 pour 12%)
        duration_months: durée en mois
        compounding_frequency: 'monthly', 'weekly', 'daily'
        """
        principal = Decimal(str(principal))
        rate = Decimal(str(annual_rate)) / Decimal('100')
        
        # Nombre de périodes de composition
        periods_per_year = {
            'monthly': 12,
            'weekly': 52,
            'daily': 365
        }
        n = periods_per_year.get(compounding_frequency, 12)
        t = duration_months / 12  # durée en années
        
        # Formule A = P(1 + r/n)^(nt)
        exponent = n * t
        rate_per_period = rate / n
        amount = principal * (Decimal('1') + rate_per_period) ** Decimal(str(exponent))
        interest = amount - principal
        
        return {
            'total_amount': round(amount, 2),
            'total_interest': round(interest, 2),
            'effective_rate': round((interest / principal) * 100, 2)
        }
    
    @staticmethod
    def calculate_simple_interest(principal, annual_rate, duration_months):
        """
        Calcule les intérêts simples
        Formule: I = P * r * t
        """
        principal = Decimal(str(principal))
        rate = Decimal(str(annual_rate)) / Decimal('100')
        t = Decimal(str(duration_months)) / Decimal('12')
        
        interest = principal * rate * t
        total_amount = principal + interest
        
        return {
            'total_amount': round(total_amount, 2),
            'total_interest': round(interest, 2),
            'effective_rate': round((interest / principal) * 100, 2)
        }
    
    @staticmethod
    def generate_amortization_schedule(principal, annual_rate, duration_months, interest_type='compound', start_date=None):
        """
        Génère le tableau d'amortissement mensuel
        """
        principal = Decimal(str(principal))
        rate = Decimal(str(annual_rate)) / Decimal('100') / Decimal('12')  # taux mensuel
        
        if start_date is None:
            start_date = datetime.now().date()
        
        schedule = []
        remaining = principal
        
        # Calcul de la mensualité avec la formule d'amortissement
        if rate > 0:
            monthly_payment = principal * (rate * (Decimal('1') + rate) ** Decimal(str(duration_months))) / ((Decimal('1') + rate) ** Decimal(str(duration_months)) - Decimal('1'))
        else:
            monthly_payment = principal / Decimal(str(duration_months))
        
        total_interest = Decimal('0')
        
        for month in range(1, duration_months + 1):
            interest = remaining * rate
            principal_part = monthly_payment - interest
            remaining -= principal_part
            
            due_date = start_date + timedelta(days=30 * month)
            
            schedule.append({
                'month': month,
                'due_date': due_date,
                'payment': round(monthly_payment, 2),
                'principal': round(principal_part, 2),
                'interest': round(interest, 2),
                'remaining': round(max(remaining, 0), 2)
            })
            total_interest += interest
        
        return {
            'schedule': schedule,
            'monthly_payment': round(monthly_payment, 2),
            'total_interest': round(total_interest, 2),
            'total_amount': round(principal + total_interest, 2)
        }
    
    @staticmethod
    def calculate_late_penalty(due_amount, days_late, penalty_rate=5):
        """
        Calcule la pénalité de retard
        penalty_rate: pourcentage annuel
        """
        due_amount = Decimal(str(due_amount))
        daily_rate = Decimal(str(penalty_rate)) / Decimal('100') / Decimal('365')
        penalty = due_amount * daily_rate * Decimal(str(days_late))
        return round(penalty, 2)