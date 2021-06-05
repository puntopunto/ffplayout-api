from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute().parent.parent

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR.joinpath('dbs', 'player.sqlite3')),
    }
}
