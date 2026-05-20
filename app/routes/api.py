from app.services.eligibility_service import EligibilityService

@bp.route('/client-summary/<client_id>')
@login_required
def client_summary(client_id):
    summary = EligibilityService.get_client_summary(client_id)
    if summary:
        return {
            'monthly_income': summary['monthly_income'],
            'savings_balance': summary['savings_balance'],
            'active_loans_count': summary['active_loans_count'],
            'completed_loans_count': summary['completed_loans_count'],
            'max_loan_amount': summary['max_loan_amount']
        }
    return {'error': 'Client non trouvé'}, 404