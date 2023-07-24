from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

import os
if not os.path.exists('data'):
    os.makedirs('data')

Base = declarative_base()

class Trend(Base):
    __tablename__ = 'trends'

    id = Column(Integer, primary_key=True, autoincrement=True)
    trend_name = Column(String)
    title = Column(String)
    article_id = Column(Integer)

    def __repr__(self):
        return f'Trend(id={self.id}, trend_name={self.trend_name})'

engine = create_engine('sqlite:///data/trends.db')
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)