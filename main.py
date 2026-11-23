from datetime import date
from enum import Enum
from typing import List, Optional

import strawberry
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter


@strawberry.enum
class ReadingStatus(Enum):
    WANT_TO_READ = "WANT_TO_READ"
    READING = "READING"
    FINISHED = "FINISHED"


@strawberry.type
class Author:
    id: strawberry.ID
    name: str
    country: Optional[str] = None

    @strawberry.field
    def books(self) -> List["Book"]:
        return [b for b in BOOKS if b.author_id == self.id]

    @strawberry.field
    def book_count(self) -> int:
        return len([b for b in BOOKS if b.author_id == self.id])


@strawberry.type
class Book:
    id: strawberry.ID
    title: str
    year: int
    pages: int
    status: ReadingStatus
    author_id: strawberry.Private[strawberry.ID]
    rating: Optional[int] = None

    @strawberry.field
    def author(self) -> Author:
        return next(a for a in AUTHORS if a.id == self.author_id)


@strawberry.type
class Stats:
    total_books: int
    finished_books: int
    average_rating: Optional[float]
    total_pages_read: int


@strawberry.input
class AuthorInput:
    name: str
    country: Optional[str] = None


@strawberry.input
class BookInput:
    title: str
    year: int
    pages: int
    author_id: strawberry.ID


# dados em memória
AUTHORS = [
    Author(id="1", name="Machado de Assis", country="Brasil"),
    Author(id="2", name="George Orwell", country="Reino Unido"),
    Author(id="3", name="Clarice Lispector", country="Brasil"),
]

BOOKS = [
    Book(id="1", title="Dom Casmurro", year=1899, pages=256, status=ReadingStatus.FINISHED, author_id="1", rating=5),
    Book(id="2", title="Memórias Póstumas de Brás Cubas", year=1881, pages=368, status=ReadingStatus.FINISHED, author_id="1", rating=4),
    Book(id="3", title="1984", year=1949, pages=416, status=ReadingStatus.READING, author_id="2"),
    Book(id="4", title="A Revolução dos Bichos", year=1945, pages=152, status=ReadingStatus.WANT_TO_READ, author_id="2"),
    Book(id="5", title="A Hora da Estrela", year=1977, pages=88, status=ReadingStatus.FINISHED, author_id="3", rating=5),
    Book(id="6", title="Perto do Coração Selvagem", year=1943, pages=192, status=ReadingStatus.WANT_TO_READ, author_id="3"),
]

next_ids = {"author": 4, "book": 7}


def find_book(id):
    for b in BOOKS:
        if b.id == str(id):
            return b
    raise ValueError(f"Livro {id} não encontrado")


@strawberry.type
class Query:
    @strawberry.field
    def books(self, status: Optional[ReadingStatus] = None, search: Optional[str] = None) -> List[Book]:
        result = BOOKS
        if status is not None:
            result = [b for b in result if b.status == status]
        if search:
            result = [b for b in result if search.lower() in b.title.lower()]
        return result

    @strawberry.field
    def book(self, id: strawberry.ID) -> Optional[Book]:
        return next((b for b in BOOKS if b.id == str(id)), None)

    @strawberry.field
    def authors(self) -> List[Author]:
        return AUTHORS

    @strawberry.field
    def stats(self) -> Stats:
        finished = [b for b in BOOKS if b.status == ReadingStatus.FINISHED]
        rated = [b.rating for b in BOOKS if b.rating is not None]
        return Stats(
            total_books=len(BOOKS),
            finished_books=len(finished),
            average_rating=sum(rated) / len(rated) if rated else None,
            total_pages_read=sum(b.pages for b in finished),
        )


@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_author(self, input: AuthorInput) -> Author:
        if not input.name.strip():
            raise ValueError("O nome do autor não pode ser vazio")
        author = Author(id=str(next_ids["author"]), name=input.name.strip(), country=input.country)
        next_ids["author"] += 1
        AUTHORS.append(author)
        return author

    @strawberry.mutation
    def add_book(self, input: BookInput) -> Book:
        if not input.title.strip():
            raise ValueError("O título não pode ser vazio")
        if input.year > date.today().year:
            raise ValueError("O ano não pode ser maior que o ano atual")
        if input.pages < 1:
            raise ValueError("O número de páginas deve ser pelo menos 1")
        if not any(a.id == str(input.author_id) for a in AUTHORS):
            raise ValueError(f"Autor {input.author_id} não existe")
        book = Book(
            id=str(next_ids["book"]),
            title=input.title.strip(),
            year=input.year,
            pages=input.pages,
            status=ReadingStatus.WANT_TO_READ,
            author_id=str(input.author_id),
        )
        next_ids["book"] += 1
        BOOKS.append(book)
        return book

    @strawberry.mutation
    def update_book_status(self, id: strawberry.ID, status: ReadingStatus) -> Book:
        book = find_book(id)
        book.status = status
        if status != ReadingStatus.FINISHED:
            book.rating = None  # só livro lido tem nota
        return book

    @strawberry.mutation
    def rate_book(self, id: strawberry.ID, rating: int) -> Book:
        if rating < 1 or rating > 5:
            raise ValueError("A nota deve estar entre 1 e 5")
        book = find_book(id)
        if book.status != ReadingStatus.FINISHED:
            raise ValueError("Só é possível avaliar livros que já foram lidos (FINISHED)")
        book.rating = rating
        return book

    @strawberry.mutation
    def delete_book(self, id: strawberry.ID) -> bool:
        book = find_book(id)
        BOOKS.remove(book)
        return True


schema = strawberry.Schema(query=Query, mutation=Mutation)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(GraphQLRouter(schema), prefix="/graphql")
