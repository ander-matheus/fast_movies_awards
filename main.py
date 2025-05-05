from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import contains_eager
from sqlmodel import select

from database import SessionDep, create_db_and_tables, drop_db_and_tables
from migrations import load_csv_data
from models import Movie, MovieRelations, Producer, ProducerWinnerIntervalResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    load_csv_data()
    yield
    drop_db_and_tables()


app = FastAPI(
    title="Golden Raspberry Awards API",
    summary="API RESTful para possibilitar a leitura da lista de indicados e "
    "vencedores da categoria Pior Filme do Golden Raspberry Awards.",
    lifespan=lifespan,
    root_path="/api/v1",
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("/docs")


@app.get("/movies", response_model=list[MovieRelations])
async def read_movies(
    session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100
) -> list[Movie]:
    query = select(Movie).offset(offset).limit(limit)
    movies = session.exec(query).all()
    return movies


@app.get("/movies/{movie_id}", response_model=MovieRelations)
async def read_movie(movie_id: int, session: SessionDep) -> MovieRelations:
    movie = session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@app.get("/awards-interval-by-producer", response_model=ProducerWinnerIntervalResponse)
async def awards_interval_by_producer(
    session: SessionDep,
) -> ProducerWinnerIntervalResponse:
    statement = (
        select(Producer)
        .join(Movie.producers)
        .where(Movie.winner == True)  # NOQA
        .options(contains_eager(Producer.movies))
        .distinct()
    )
    results = session.exec(statement).unique().all()

    producer_wins = {}
    for producer in results:
        years = sorted({m.year for m in producer.movies if m.winner})
        producer_wins[producer.name] = years

    # Calculate intervals
    intervals = []
    for producer_name, years in producer_wins.items():
        years.sort()
        for i in range(1, len(years)):
            interval = years[i] - years[i - 1]
            intervals.append(
                {
                    "producer": producer_name,
                    "interval": interval,
                    "previousWin": years[i - 1],
                    "followingWin": years[i],
                }
            )

    if not intervals:
        return {min: [], max: []}

    # get min and max interval
    min_interval = min(interval["interval"] for interval in intervals)
    max_interval = max(interval["interval"] for interval in intervals)

    # filter by min and max interval
    min_intervals = [
        interval for interval in intervals if interval["interval"] == min_interval
    ]

    max_intervals = [
        interval for interval in intervals if interval["interval"] == max_interval
    ]

    return {"min": min_intervals, "max": max_intervals}
