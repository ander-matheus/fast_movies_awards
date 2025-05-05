import csv
import logging
import os
import re

from sqlalchemy.exc import ProgrammingError
from sqlmodel import Session, select

from database import engine
from models import Movie, Producer, Studio

logger = logging.getLogger(__name__)


def get_or_create_studio(session: Session, name: str):
    statement = select(Studio).where(Studio.name == name)
    studio = session.exec(statement).first()
    if studio:
        return studio
    studio = Studio(name=name)
    session.add(studio)

    return studio


def get_or_create_producer(session: Session, name: str):
    statement = select(Producer).where(Producer.name == name)
    producer = session.exec(statement).first()
    if producer:
        return producer
    producer = Producer(name=name)
    session.add(producer)

    return producer


def split_names(names: str) -> list:
    names_list = re.split(r",\s*|\s+and\s+", names)
    names_list = [name.strip().replace("and", "") for name in names_list]
    return names_list


def load_csv_data():
    csv_path = os.path.join("movielist.csv")

    try:
        if os.path.exists(csv_path):
            with Session(engine) as session:
                with open(csv_path, newline="", encoding="utf-8") as csv_file:
                    reader = csv.DictReader(csv_file, delimiter=";")
                    for row in reader:
                        studios = []
                        studios_names_list = split_names(row["studios"])
                        for studio_name in studios_names_list:
                            studio = get_or_create_studio(
                                session=session, name=studio_name
                            )
                            studios.append(studio)

                        producers = []
                        producers_names_list = split_names(row["producers"])

                        for producer_name in producers_names_list:
                            producer = get_or_create_producer(
                                session=session, name=producer_name
                            )
                            producers.append(producer)

                        movie = Movie(
                            year=int(row["year"]),
                            title=row["title"],
                            winner=row["winner"] == "yes",
                            producers=producers,
                            studios=studios,
                        )

                        session.add(movie)
                    session.commit()

            logger.info("Filmes importados.")

    except ProgrammingError as e:
        logger.error(f"Erro ao importar os dados CSV para base: {e}.")
