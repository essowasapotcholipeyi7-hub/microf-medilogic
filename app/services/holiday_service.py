from datetime import timedelta
from app.models.holiday import Holiday

class HolidayService:
    
    @staticmethod
    def adjust_for_holidays(date, tenant_id, db):
        """Ajuste une date si elle tombe un jour férié"""
        # Récupérer tous les jours fériés pour cette année
        year = date.year
        holidays = Holiday.query.filter_by(
            tenant_id=tenant_id,
            is_active=True
        ).all()
        
        holiday_dates = []
        for holiday in holidays:
            holiday_date = holiday.get_date_for_year(year)
            if holiday_date:
                holiday_dates.append(holiday_date)
            
            # Vérifier aussi l'année suivante si on est en fin d'année
            if date.month == 12:
                next_year_date = holiday.get_date_for_year(year + 1)
                if next_year_date:
                    holiday_dates.append(next_year_date)
        
        # Si la date tombe un jour férié, reporter au jour suivant
        adjusted_date = date
        while adjusted_date in holiday_dates or adjusted_date.weekday() >= 5:  # Samedi ou Dimanche
            adjusted_date += timedelta(days=1)
            # Vérifier si le nouveau jour est aussi férié
            while adjusted_date in holiday_dates:
                adjusted_date += timedelta(days=1)
        
        return adjusted_date
    
    @staticmethod
    def adjust_schedule(schedule, tenant_id, db):
        """Ajuste tout un échéancier pour éviter les jours fériés"""
        adjusted_schedule = []
        for payment in schedule:
            original_date = payment['due_date']
            adjusted_date = HolidayService.adjust_for_holidays(original_date, tenant_id, db)
            payment['original_due_date'] = original_date
            payment['due_date'] = adjusted_date
            adjusted_schedule.append(payment)
        return adjusted_schedule