import os

class Config:
    SECRET_KEY = 'super-secret-key'
    JWT_SECRET_KEY = 'jwt-super-secret-key'
    DB_URL = "postgresql://postgres:admin%402102@localhost:5432/postgres"