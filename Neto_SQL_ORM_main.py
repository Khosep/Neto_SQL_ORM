import configparser
import json
import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import exists
from Neto_SQL_ORM_models import drop_tables, create_tables, Publisher, Shop, Book, Stock, Sale

DB_name = 'neto_books_orm'

config = configparser.ConfigParser()
config.read('postgres.ini')
Postgres_password = config['Postgres']['password']


def insert_from_json(file_path):
    with open(file_path, encoding='utf-8') as file:
        data = json.load(file)
        for row in data:
            model = {'publisher': Publisher,
                     'shop': Shop,
                     'book': Book,
                     'stock': Stock,
                     'sale': Sale}[row.get('model')]
            session.add(model(id=row.get('pk'), **row.get('fields')))
        session.commit()


def get_shops_by_publisher(p_input):
    # is p_input id or not id
    id_bool = 1 if p_input.isdigit() else 0
    # is p_input (as id/name) in the database
    res_bool = session.query(exists().where(Publisher.id == p_input)).scalar() if id_bool else \
                session.query(exists().where(Publisher.name == p_input)).scalar()
    if res_bool:
        p_id, p_name = session.query(Publisher.id, Publisher.name).where(Publisher.id == p_input)[0] if id_bool else \
                       session.query(Publisher.id, Publisher.name).where(Publisher.name == p_input)[0]
        print(f"Издатель '{p_name}' (id = {p_id}):")
        q = session.query(Shop.name). \
            join(Stock.shop). \
            join(Stock.book). \
            join(Stock.shop). \
            join(Book.publisher). \
            where(sq.and_(Publisher.id == p_id, Stock.count > 0)). \
            distinct()
        # print(q)
        print(f'>>Книги издателя можно приобрести в {", ".join([i[0] for i in q.all()])}'
              if q.all() else f'>>На текущий момент в продаже нет книг издателя')
        return q
    else:
        print(f'>>Издатель отсутствует в базе данных')


# _______________________________________________________________________
if __name__ == '__main__':
    DSN = f'postgresql://postgres:{Postgres_password}@localhost:5432/{DB_name}'
    engine = sq.create_engine(DSN)

    drop_tables(engine)
    create_tables(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    insert_from_json('fixtures/tests_data.json')

    p_input = input('Введите имя издателя или его id: ')

    get_shops_by_publisher(p_input)
    session.close()


