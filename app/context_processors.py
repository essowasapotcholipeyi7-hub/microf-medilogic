from datetime import datetime

def inject_global_data():
    citations = [
        "Le succès, c'est tomber sept fois et se relever huit fois.",
        "La meilleure façon de prédire l'avenir est de le créer.",
        "Petit à petit, l'oiseau fait son nid.",
        "L'union fait la force.",
        "Chaque grand voyage commence par un premier pas.",
        "La patience est l'art d'espérer.",
        "Ce n'est pas parce que les choses sont difficiles que nous n'osons pas, c'est parce que nous n'osons pas qu'elles sont difficiles."
    ]
    
    return {
        'current_year': datetime.now().year,
        'current_time': datetime.now().strftime('%H:%M'),
        'citations': citations,
        'today_citation': citations[datetime.now().day % len(citations)]
    }