from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Boolean, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum as PyEnum, auto

import os
if not os.path.exists('data'):
    os.makedirs('data')

Base = declarative_base()

class ArticleStatus(PyEnum):
    PUBLISHED = auto()
    UNPUBLISHED = auto()
    NULL = None

class Trend(Base):
    __tablename__ = 'trends'

    id = Column(Integer, primary_key=True, autoincrement=True)
    trend_name = Column(String)
    title = Column(String)
    article_id = Column(Integer)
    article = Column(String)
    article_wordpress_updated = Column(Boolean)
    timestamp=Column(String)
    article_tags = Column(String)
    article_tags_added = Column(Boolean)

    def __repr__(self):
        return f'Trend(id={self.id}, trend_name={self.trend_name}, title={self.title}, article_id={self.article_id}, article={self.article}, article_wordpress_updated={self.article_wordpress_updated})'

engine = create_engine('sqlite:///data/trends.db')
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)