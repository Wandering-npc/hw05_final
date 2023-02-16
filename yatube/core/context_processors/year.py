from datetime import date


def year(request):
    """Добавляет переменную с текущим годом."""
    year_now = date.today().year
    return {
        'year': year_now
    }
