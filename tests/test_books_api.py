from httpx import AsyncClient

BOOK_HOBBIT = {
    "title": "O Hobbit",
    "author": "J.R.R. Tolkien",
    "published_date": "1937-09-21",
    "summary": "Aventura na Terra Média",
}

BOOK_1984 = {
    "title": "1984",
    "author": "George Orwell",
    "published_date": "1949-06-08",
}


class TestCreateBook:
    async def test_creates_book_with_summary(self, client: AsyncClient) -> None:
        response = await client.post("/books", json=BOOK_HOBBIT)
        assert response.status_code == 201

        body = response.json()
        assert body["id"] is not None
        assert body["title"] == "O Hobbit"
        assert body["summary"] == "Aventura na Terra Média"
        assert body["summary_source"] == "user"

    async def test_creates_book_without_summary(self, client: AsyncClient) -> None:
        response = await client.post("/books", json=BOOK_1984)
        assert response.status_code == 201
        assert response.json()["summary"] is None

    async def test_missing_title_returns_422_problem_details(self, client: AsyncClient) -> None:
        response = await client.post(
            "/books",
            json={"author": "Tolkien", "published_date": "1937-09-21"},
        )
        assert response.status_code == 422
        assert response.headers["content-type"].startswith("application/problem+json")

        body = response.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert "title" in body["detail"]
        assert body["status"] == 422


class TestListBooks:
    async def test_returns_empty_list_initially(self, client: AsyncClient) -> None:
        response = await client.get("/books")
        assert response.status_code == 200
        body = response.json()
        assert body == {"items": [], "total": 0, "skip": 0, "limit": 20}

    async def test_returns_created_books(self, client: AsyncClient) -> None:
        await client.post("/books", json=BOOK_HOBBIT)
        await client.post("/books", json=BOOK_1984)

        response = await client.get("/books")
        assert response.status_code == 200

        body = response.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    async def test_filters_by_title_case_insensitive(self, client: AsyncClient) -> None:
        await client.post("/books", json=BOOK_HOBBIT)
        await client.post("/books", json=BOOK_1984)

        response = await client.get("/books", params={"title": "hobbit"})
        assert response.status_code == 200

        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["title"] == "O Hobbit"

    async def test_filters_by_author_partial(self, client: AsyncClient) -> None:
        await client.post("/books", json=BOOK_HOBBIT)
        await client.post("/books", json=BOOK_1984)

        response = await client.get("/books", params={"author": "orwell"})
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["author"] == "George Orwell"

    async def test_pagination(self, client: AsyncClient) -> None:
        for i in range(5):
            await client.post(
                "/books",
                json={
                    "title": f"Book {i}",
                    "author": "Author",
                    "published_date": "2000-01-01",
                },
            )

        response = await client.get("/books", params={"skip": 2, "limit": 2})
        body = response.json()
        assert body["total"] == 5
        assert len(body["items"]) == 2
        assert body["skip"] == 2
        assert body["limit"] == 2

    async def test_limit_upper_bound_enforced(self, client: AsyncClient) -> None:
        response = await client.get("/books", params={"limit": 999})
        assert response.status_code == 422


class TestGetBook:
    async def test_returns_book_by_id(self, client: AsyncClient) -> None:
        created = (await client.post("/books", json=BOOK_HOBBIT)).json()

        response = await client.get(f"/books/{created['id']}")
        assert response.status_code == 200
        assert response.json()["title"] == "O Hobbit"

    async def test_missing_id_returns_404_problem_details(self, client: AsyncClient) -> None:
        response = await client.get("/books/999")
        assert response.status_code == 404
        assert response.headers["content-type"].startswith("application/problem+json")

        body = response.json()
        assert body["code"] == "BOOK_NOT_FOUND"
        assert body["status"] == 404
        assert "999" in body["detail"]


class TestUpdateBook:
    async def test_updates_book(self, client: AsyncClient) -> None:
        created = (await client.post("/books", json=BOOK_HOBBIT)).json()

        response = await client.put(
            f"/books/{created['id']}",
            json={"summary": "Updated summary"},
        )
        assert response.status_code == 200
        assert response.json()["summary"] == "Updated summary"
        assert response.json()["title"] == "O Hobbit"

    async def test_missing_id_returns_404_problem_details(self, client: AsyncClient) -> None:
        response = await client.put("/books/999", json={"title": "Ghost"})
        assert response.status_code == 404

        body = response.json()
        assert body["code"] == "BOOK_NOT_FOUND"


class TestDeleteBook:
    async def test_deletes_book(self, client: AsyncClient) -> None:
        created = (await client.post("/books", json=BOOK_HOBBIT)).json()

        response = await client.delete(f"/books/{created['id']}")
        assert response.status_code == 204

        get_response = await client.get(f"/books/{created['id']}")
        assert get_response.status_code == 404

    async def test_missing_id_returns_404_problem_details(self, client: AsyncClient) -> None:
        response = await client.delete("/books/999")
        assert response.status_code == 404

        body = response.json()
        assert body["code"] == "BOOK_NOT_FOUND"
