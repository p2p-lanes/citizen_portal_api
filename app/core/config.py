import os
from enum import Enum

from dotenv import load_dotenv

load_dotenv()


class Environment(str, Enum):
    TEST = 'test'
    PRODUCTION = 'production'
    DEVELOP = 'develop'


class Settings:
    ENVIRONMENT: Environment = Environment(os.getenv('ENVIRONMENT') or Environment.TEST)
    DB_USERNAME: str = os.getenv('DB_USERNAME')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD')
    DB_HOST: str = os.getenv('DB_HOST')
    DB_PORT: str = os.getenv('DB_PORT')
    DB_NAME: str = os.getenv('DB_NAME')

    SQLALCHEMY_TEST_DATABASE_URL = 'sqlite:///:memory:'
    DATABASE_URL: str = (
        f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        if ENVIRONMENT != Environment.TEST
        else SQLALCHEMY_TEST_DATABASE_URL
    )

    POSTMARK_API_TOKEN: str = os.getenv('POSTMARK_API_TOKEN')
    EMAIL_FROM_ADDRESS: str = os.getenv('EMAIL_FROM_ADDRESS')
    EMAIL_FROM_NAME: str = os.getenv('EMAIL_FROM_NAME')
    EMAIL_REPLY_TO: str = os.getenv('EMAIL_REPLY_TO')

    SECRET_KEY: str = os.getenv('SECRET_KEY', '')
    BACKEND_URL: str = os.getenv('BACKEND_URL')
    FRONTEND_URL: str = os.getenv('FRONTEND_URL')
    SIMPLEFI_API_URL: str = os.getenv('SIMPLEFI_API_URL')
    NOCODB_URL: str = os.getenv('NOCODB_URL')
    NOCODB_TOKEN: str = os.getenv('NOCODB_TOKEN')
    NOCODB_WEBHOOK_SECRET: str = os.getenv('NOCODB_WEBHOOK_SECRET')
    COUPON_API_KEY: str = os.getenv('COUPON_API_KEY')
    ATTENDEES_API_KEY: str = os.getenv('ATTENDEES_API_KEY')
    FAST_CHECKOUT_API_KEY: str = os.getenv('GROUPS_API_KEY')


settings = Settings()
