import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    dt_now = datetime.date.today().year
    return {
        'year': dt_now
    }
