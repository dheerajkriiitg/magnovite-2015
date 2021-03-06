"""
Django settings for magnovite project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import dj_database_url

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

ADMINS = (
    ('Ahmed Azaan', 'azaan@outlook.com'),
)

HELP_INCHARGE = (
    'azaan@outlook.com',
    'sandeep.kumar@it.christuniversity.in',
    'arjunjariwala1994@gmail.com',
)

ACCOMODATION_INCHARGE = (
    'azaan@outlook.com',
    'jons.cyriac@cse.christuniversity.in',
    'roshenanil@gmail.com',
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'zqnn4=p1jfl_$#2w+-y-ua92u*woge78$201+wy#mf0(yl+x6y')

ANALYTICS_SECRET = os.environ.get('DJANGO_ANALYTICS_SECRET', 'secret')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
if os.environ.get('PROD', False) != False:
    DEBUG = False

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['*']

# Custom user model
AUTH_USER_MODEL = 'main.MUser'

SITE_ID = 1

# should countdown timer be zero
TIMER_ZERO = os.environ.get('TIMER_ZERO', False)

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',

    # 3rd party
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.twitter',
    'allauth.socialaccount.providers.github',

    'app.main',
    'app.subscribe',
    'app.event',
    'app.quest',
    'app.dashboard',
    'app.message',
    'app.payment',
    'app.workshop',
    'app.internal',
)

if DEBUG:
    INSTALLED_APPS = INSTALLED_APPS + (
        'django_extensions',
        'debug_toolbar',
    )

    DEBUG_TOOLBAR_CONFIG = {
        'JQUERY_URL': '/static/js/lib/jquery-2.1.1.min.js',
    }

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    # default
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",

    # Required by allauth template tags
    "django.core.context_processors.request",

    # allauth specific context processors
    "allauth.account.context_processors.account",
    "allauth.socialaccount.context_processors.socialaccount",

    # my processors
    'app.main.context_processors.profile',
    'app.main.context_processors.access',
)

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",

    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

# allauth settings
SOCIALACCOUNT_AUTO_SIGNUP = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'email'
SOCIALACCOUNT_QUERY_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'none'

SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'SCOPE': ['email'],
        'AUTH_PARAMS': {
            'auth_type': 'https'
        },
        'METHOD': 'oauth2',
        'LOCALE_FUNC': lambda _: 'en_US',
    },
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {
            'access_type': 'online'
        }
    },
    'github': {
        'SCOPE': ['user']
    }
}

if not DEBUG:
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
SOCIALACCOUNT_ADAPTER = 'app.main.allauth.MSocialAccountAdapter'

# payment settings
PAYU_MERCHANT_ID = os.environ.get('PAYU_MERCHANT_ID', '')
PAYU_MERCHANT_KEY = os.environ.get('PAYU_MERCHANT_KEY', '')
PAYU_MERCHANT_SALT = os.environ.get('PAYU_MERCHANT_SALT', '')

PAYU_URL = 'https://secure.payu.in/_payment'
PAYU_SUCCESS_URL = 'https://magnovite.net/payment/success/'
PAYU_FAILURE_URL = 'https://magnovite.net/payment/failure/'
PAYU_NOTIFY_URL = 'https://magnovite.net/payment/notify/'

if DEBUG:
    PAYU_MERCHANT_KEY = 'JBZaLc'
    PAYU_MERCHANT_SALT = 'GQs7yium'

    PAYU_URL = 'https://test.payu.in/_payment'
    PAYU_SUCCESS_URL = 'http://localhost:8000/payment/success/'
    PAYU_FAILURE_URL = 'https://localhost:8000/payment/failure/'
    PAYU_NOTIFY_URL = 'https://localhost:8000/payment/notify/'


LOGIN_REDIRECT_URL = '/profile/'
LOGIN_URL = '/#login'

ROOT_URLCONF = 'app.magnovite.urls'

WSGI_APPLICATION = 'app.magnovite.wsgi.application'

ID_OFFSET = int(os.environ.get('ID_OFFSET', 1432))

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

if os.environ.get('DATABASE_URL', '') != '':
    DATABASES['default'] = dj_database_url.config()

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Calcutta'

USE_I18N = True
USE_L10N = True
USE_THOUSAND_SEPARATOR = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

# email settings
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'aeon10'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASS')
DEFAULT_FROM_EMAIL = 'official@magnovite.net'
SERVER_EMAIL = 'server@magnovite.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console':{
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'null': {
            'class': 'django.utils.log.NullHandler',
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django': {
            'handlers': ['console'],
        },
        'django.request': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'py.warnings': {
            'handlers': ['console'],
        },
    }
}

# Production settings
if not DEBUG:
    TEMPLATE_LOADERS = (
        ('django.template.loaders.cached.Loader', (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        )),
    )

    # https settings
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

if not DEBUG:
    exec(open('app/magnovite/settings_heroku.py').read(), globals())
