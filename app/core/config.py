import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DB_USERNAME: str = os.getenv('DB_USERNAME')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD')
    DB_HOST: str = os.getenv('DB_HOST')
    DB_PORT: str = os.getenv('DB_PORT')
    DB_NAME: str = os.getenv('DB_NAME')

    DATABASE_URL: str = (
        f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )

    SECRET_KEY: str = os.getenv('SECRET_KEY')
    MAILCHIMP_KEY: str = os.getenv('MAILCHIMP_KEY')
    FRONTEND_URL: str = os.getenv('FRONTEND_URL')


settings = Settings()
