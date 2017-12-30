from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from baropi.config import cfg


def make_session():
    # print(' +++ connected session to %s' % __dbconn__)
    return scoped_session(
        sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
    )


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from . import models as m
    print(" +++ registering models", m)
    Base.metadata.create_all(bind=engine) # shit


def format_conn_str(cfg):
    conf = cfg.db.connection
    return '{0}://{1}:{2}@{3}:{4}/baropi'.format(
        conf.dialect,
        conf.user,
        conf.pw,
        conf.host,
        conf.port
    )


conn = format_conn_str(cfg)
print(' +++ creating db engine')
engine = create_engine(
    conn, convert_unicode=True
)
db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)
Base = declarative_base()
Base.query = db_session.query_property()
