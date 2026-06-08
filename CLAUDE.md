# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

CS50P final project: a small CLI tool that authenticates with the Strava API via OAuth2, fetches the authenticated athlete's info, and (per `activities.csv`) pulls activity data. Managed with `uv`.

## Commands

- Run the app: `uv run python project.py` (or `python project.py` inside `.venv`)
- Run tests: `uv run python -m unittest strava-auth-tests.py`
- Run a single test: `uv run python -m unittest strava-auth-tests.TestStravaAuth.test_refresh_token`
- Install/sync deps: `uv sync`

Requires a `.env` file (loaded via `python-dotenv`) with `STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET`.

## Architecture

- **`strava_authenticate.py`** — `StravaAuth` class wraps an `OAuth2Session` (from `requests_oauthlib`) and owns the entire OAuth2 lifecycle: building the authorization URL, exchanging the redirect response for tokens, refreshing expired tokens, and persisting/loading tokens to/from `strava_tokens.json` (tokens are stamped with a `timestamp` on save so `is_token_expired()` can compute expiry against `expires_in`).
- **`project.py`** — entry point (`main()`). Constructs a `StravaAuth`, runs the interactive auth-or-refresh flow (prompts the user to paste the OAuth redirect URL when no valid token exists), then calls `get_athlete_info(strava)` to hit `GET /api/v3/athlete` and prints the result. `get_athlete_info` is a free function here that takes a `StravaAuth` instance — note this differs from `strava-auth-tests.py`, which mocks it as a method on `StravaAuth` (`self.auth.get_athlete_info()`); the test file is out of sync with the current `project.py`/`strava_authenticate.py` split and may need updating before it passes.
- **`main.py`** — unrelated `uv` scaffold stub ("Hello from strava-api!"), not the real entry point.
- **`strava_tokens.json`** — local token cache written by `StravaAuth.save_tokens`/loaded by `load_tokens`; gitignored (do not commit).
- **`activities.csv`** — exported/cached Strava activity data used elsewhere in the project (no code currently reads it from this directory's scripts).

## Notes

- Tokens expire roughly every 7 days; `StravaAuth.is_token_expired()` treats a token as expired if it will lapse within the next 5 minutes.
- The OAuth redirect URI is hardcoded to `https://localhost`; the interactive flow expects the user to paste the full redirected URL back into the prompt.
