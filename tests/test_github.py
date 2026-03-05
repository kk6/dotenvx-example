import httpx
import pytest
from pytest_httpx import HTTPXMock

from app.github import create_github_client, fetch_github_profile


@pytest.mark.asyncio
async def test_fetch_github_profile_success(httpx_mock: HTTPXMock) -> None:
    # Arrange
    httpx_mock.add_response(
        url="https://api.github.com/users/octocat",
        json={
            "login": "octocat",
            "name": "The Octocat",
            "avatar_url": "https://avatars.githubusercontent.com/u/583231",
            "bio": "A mysterious cat who likes coding.",
            "public_repos": 8,
            "followers": 17000,
            "following": 9,
            "html_url": "https://github.com/octocat",
        },
    )

    # Act
    async with create_github_client() as client:
        data = await fetch_github_profile("octocat", client)

    # Assert
    assert data["login"] == "octocat"
    assert data["name"] == "The Octocat"
    assert data["public_repos"] == 8


@pytest.mark.asyncio
async def test_fetch_github_profile_not_found(httpx_mock: HTTPXMock) -> None:
    # Arrange
    httpx_mock.add_response(
        url="https://api.github.com/users/nonexistent-user-xyz",
        status_code=404,
        json={"message": "Not Found"},
    )

    # Act & Assert
    async with create_github_client() as client:
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await fetch_github_profile("nonexistent-user-xyz", client)

    assert exc_info.value.response.status_code == 404


@pytest.mark.asyncio
async def test_fetch_github_profile_uses_token(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token_12345")
    httpx_mock.add_response(
        url="https://api.github.com/users/octocat",
        json={"login": "octocat"},
    )

    # Act
    async with create_github_client() as client:
        await fetch_github_profile("octocat", client)

    # Assert — verify Authorization header was sent
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["Authorization"] == "Bearer ghp_test_token_12345"


@pytest.mark.asyncio
async def test_fetch_github_profile_no_token(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange — no token set
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    httpx_mock.add_response(
        url="https://api.github.com/users/octocat",
        json={"login": "octocat"},
    )

    # Act
    async with create_github_client() as client:
        await fetch_github_profile("octocat", client)

    # Assert — no Authorization header
    request = httpx_mock.get_request()
    assert request is not None
    assert "Authorization" not in request.headers
