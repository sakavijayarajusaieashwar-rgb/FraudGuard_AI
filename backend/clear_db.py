from app.database import Base, engine

print('Dropping and recreating all tables...')
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print('Done.')
