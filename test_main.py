import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from database import get_session
from main import app
from models import Movie, MovieProducerLink, MovieStudioLink, Producer, Studio


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        producer1 = Producer(name="Test Producer")
        producer2 = Producer(name="Test Producer 2")
        studio1 = Studio(name="Test Studio")
        studio2 = Studio(name="Test Studio 2")

        session.add_all([producer1, producer2, studio1, studio2])
        session.commit()

        movies = []
        for i in range(15):
            movie = Movie(
                title=f"Movie {i}",
                year=2000 + i,
                winner=(i in [0, 2, 6, 9]),
            )
            session.add(movie)
            session.commit()
            session.refresh(movie)

            if i % 2 == 0:
                session.add(
                    MovieProducerLink(movie_id=movie.id, producer_id=producer1.id)
                )
                session.add(MovieStudioLink(movie_id=movie.id, studio_id=studio1.id))
            else:
                session.add(
                    MovieProducerLink(movie_id=movie.id, producer_id=producer2.id)
                )
                session.add(MovieStudioLink(movie_id=movie.id, studio_id=studio2.id))
            session.commit()
            movies.append(movie)
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_list_movies(client: TestClient):
    response = client.get("/movies")
    assert response.status_code == 200


def test_awards_interval_endpoint(client: TestClient):
    response = client.get("/awards-interval-by-producer/")
    assert response.status_code == 200
    data = response.json()

    assert data["min"][0]["interval"] == 2
    assert data["max"][0]["interval"] == 4

    assert all(
        field in data["min"][0]
        for field in ["producer", "interval", "previousWin", "followingWin"]
    )
    assert all(
        field in data["max"][0]
        for field in ["producer", "interval", "previousWin", "followingWin"]
    )


def test_detail_view_relations(client: TestClient, session: Session):
    movie = session.exec(select(Movie)).first()
    response = client.get(f"/movies/{movie.id}")
    assert response.status_code == 200
    data = response.json()
    assert "studios" in data
    assert "producers" in data
    assert len(data["studios"]) > 0
    assert len(data["producers"]) > 0


def test_invalid_http_methods(client: TestClient, session: Session):
    movie = session.exec(select(Movie)).first()
    response = client.post(f"/movies/{movie.id}", json={})
    assert response.status_code == 405

    response = client.put(f"/movies/{movie.id}", json={})
    assert response.status_code == 405
