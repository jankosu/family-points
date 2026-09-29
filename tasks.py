"""Definicje zadań i dzieci - oddzielone od logiki serwera."""
from datetime import date

# Każdy wpis: (id, tytuł, punkty, pora_dnia)
WEEKDAY_COMMON_START = [
    ('wake', 'Wstanie, ubranie się, pościelenie łóżka', 1, 'Rano'),
    ('morning_hygiene', 'Umycie zębów, śniadanie, tabletka/uczesanie włosów', 1, 'Rano'),
    ('shoes', 'Zdjęcie butów/kurtki i odłożenie na miejsce', 1, 'Po szkole'),
    ('lunchbox', 'Rozpakowanie śniadaniówki i bidonu, wyjęcie resztek, opłukanie', 1, 'Po szkole'),
]
WEEKDAY_COMMON_END = [
    ('homework', 'Odrobienie lekcji', 2, 'Do 18'),
    ('reading_math', 'Czytanie/matematyka 15 min', 2, 'Do 18'),
    ('desk', 'Posprzątanie na biurku/stole', 1, 'Wieczorem'),
    ('bath', 'Kąpiel, umycie zębów', 1, 'Wieczorem'),
    ('clothes', 'Przygotowanie ubrań', 1, 'Wieczorem'),
    ('backpack', 'Spakowanie plecaka na kolejny dzień', 1, 'Wieczorem'),
]
TUESDAY_EXTRA = [('english', 'Angielski', 2, 'Po szkole')]
OTHER_WEEKDAY_EXTRA = [('pets_dishwasher', 'Karmienie psów / zapakowanie zmywarki', 2, 'Po szkole')]

WEEKDAY_TUE = WEEKDAY_COMMON_START + TUESDAY_EXTRA + WEEKDAY_COMMON_END
WEEKDAY_OTHER = WEEKDAY_COMMON_START + OTHER_WEEKDAY_EXTRA + WEEKDAY_COMMON_END

WEEKEND_MORNING = [
    ('wake', 'Wstanie, ubranie się, pościelenie łóżka', 1, 'Rano'),
    ('morning_hygiene', 'Umycie zębów, śniadanie, uczesanie włosów', 1, 'Rano'),
]
WEEKEND_EVENING = [
    ('desk', 'Posprzątanie na biurku/stole', 1, 'Wieczorem'),
    ('bath', 'Kąpiel, umycie zębów', 1, 'Wieczorem'),
    ('clothes', 'Przygotowanie ubrań', 1, 'Wieczorem'),
    ('backpack', 'Spakowanie plecaka na kolejny dzień', 1, 'Wieczorem'),
]
SATURDAY = WEEKEND_MORNING + [
    ('pool', 'Wyjście na basen', 3, 'W ciągu dnia'),
    ('toys', 'Pozbieranie zabawek', 1, 'W ciągu dnia'),
    ('clothes_pickup', 'Pozbieranie ciuchów', 1, 'W ciągu dnia'),
    ('trash', 'Pozbieranie śmieci', 1, 'W ciągu dnia'),
    ('vacuum_sweep', 'Odkurzenie/pozamiatanie', 1, 'W ciągu dnia'),
    ('dust', 'Wytarcie kurzy', 1, 'W ciągu dnia'),
    ('reading_math', '15 min czytania/matematyki', 2, 'W ciągu dnia'),
] + WEEKEND_EVENING
SUNDAY = WEEKEND_MORNING + [
    ('reading_math', '15 min czytania/matematyki', 2, 'W ciągu dnia'),
    ('bathroom', 'Umycie łazienki', 2, 'W ciągu dnia'),
    ('cars', 'Posprzątanie w autach', 2, 'W ciągu dnia'),
    ('fridge', 'Posprzątanie lodówki', 2, 'W ciągu dnia'),
    ('vacuum_mop', 'Odkurzenie domu i umycie podłogi', 2, 'W ciągu dnia'),
    ('toys', 'Pozbieranie zabawek', 1, 'W ciągu dnia'),
    ('clothes_pickup', 'Pozbieranie ciuchów', 1, 'W ciągu dnia'),
    ('trash', 'Pozbieranie śmieci', 1, 'W ciągu dnia'),
    ('vacuum_sweep', 'Odkurzenie/pozamiatanie', 1, 'W ciągu dnia'),
    ('dust', 'Wytarcie kurzy', 1, 'W ciągu dnia'),
] + WEEKEND_EVENING

EXTRA = [
    ('table', 'Pomoc przy stole', 2, 'Dodatkowe'),
    ('plants', 'Podlanie roślin', 1, 'Dodatkowe'),
    ('readmore', 'Dodatkowe 15 min czytania', 2, 'Dodatkowe'),
    ('laundry', 'Pomoc przy praniu', 2, 'Dodatkowe'),
    ('vacuum', 'Odkurzanie wyznaczonej strefy', 4, 'Dodatkowe'),
    ('meal', 'Pomoc przy posiłku', 3, 'Dodatkowe'),
    ('feed_pets', 'Karmienie zwierząt', 3, 'Dodatkowe'),
]

KIDS = [
    {'id': 'kuba', 'name': 'Jędrzej', 'emoji': '🚲'},
    {'id': 'zosia', 'name': 'Władzia', 'emoji': '🐉'},
]


def base_for(d: date):
    wd = d.weekday()  # Mon=0 ... Sun=6
    if wd == 5:
        return SATURDAY
    if wd == 6:
        return SUNDAY
    if wd == 1:
        return WEEKDAY_TUE
    return WEEKDAY_OTHER


def all_task_defs():
    """Zwraca dict: id -> (tytuł, punkty) ze wszystkich możliwych zadań (do historii/punktacji)."""
    out = {}
    for arr in (WEEKDAY_TUE, WEEKDAY_OTHER, SATURDAY, SUNDAY, EXTRA):
        for x in arr:
            out.setdefault(x[0], (x[1], x[2]))
    return out
