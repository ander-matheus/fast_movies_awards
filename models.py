from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel


class MovieProducerLink(SQLModel, table=True):
    """
    Represents the many-to-many relationship between Producer Model and Movie Model.

    Attributes:
        producer_id (int): producer's id.
        movie_id (int): movie's id.
    """

    producer_id: int | None = Field(
        default=None, foreign_key="producer.id", primary_key=True
    )
    movie_id: int | None = Field(default=None, foreign_key="movie.id", primary_key=True)


class MovieStudioLink(SQLModel, table=True):
    """
    Represents the many-to-many relationship between Studio Model and Movie Model.

    Attributes:
        studio_id (int): studio's id.
        movie_id (int): movie's id.
    """

    studio_id: int | None = Field(
        default=None, foreign_key="studio.id", primary_key=True
    )
    movie_id: int | None = Field(default=None, foreign_key="movie.id", primary_key=True)


class Producer(SQLModel, table=True):
    """
    Represents a movie producer.

    Attributes:
        name (str): Name of the producer.
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    movies: list["Movie"] = Relationship(
        back_populates="producers", link_model=MovieProducerLink
    )


class Studio(SQLModel, table=True):
    """
    Represents a movie studio.

    Attributes:
        name (str): Name of the studio.
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    movies: list["Movie"] = Relationship(
        back_populates="studios", link_model=MovieStudioLink
    )


class MovieBase(SQLModel):
    title: str = Field(index=True)
    year: int = Field(default=None, index=True)
    winner: bool = Field(default=False, index=True)


class Movie(MovieBase, table=True):
    """
    Represents a movie registered in the system.

    Attributes:
        year (int): Release year of the movie.
        title (str): Title of the movie.
        producers (ManyToMany): Producers associated with the movie.
        studios (ManyToMany): Studios associated with the movie.
        winner (bool): Indicates if the movie is an award winner.
    """

    id: int | None = Field(default=None, primary_key=True)
    studios: list[Studio] = Relationship(
        back_populates="movies",
        link_model=MovieStudioLink,
    )
    producers: list[Producer] = Relationship(
        back_populates="movies",
        link_model=MovieProducerLink,
    )


class MovieRelations(MovieBase):
    """
    Representation for response movie with relations.
    """

    id: int
    studios: list[Studio] = []
    producers: list[Producer] = []


class WinnerProducer(BaseModel):
    """
    Representation for Winner Producer.
    """

    producer: str
    interval: int
    previousWin: int
    followingWin: int


class ProducerWinnerIntervalResponse(BaseModel):
    """
    Response representation for min and max producer winner interval.
    """

    min: list[WinnerProducer] = []
    max: list[WinnerProducer] = []
