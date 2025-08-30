## How FastAPI Is Evolving: Meaningful Updates with Pydantic v2

https://medium.com/algomart/how-fastapi-is-evolving-meaningful-updates-with-pydantic-v2-fc45a63a8130


A lot has changed in FastAPI and Pydantic 2.0. Enough that if you’re working with either and still writing models like it’s 2022, you’re going to start seeing weird behavior — or worse, things silently break.

This post isn’t fluff. It’s not trying to be a Pydantic commercial. It’s what I wish I had in front of me when I opened up an old API project last month and everything blew up on Python 3.11.

If you’re building real-world APIs and need clarity on what’s changed (plus how to fix your code fast), read on.

🔗 What’s Inside
-- Path parameters — same bones, fresh paint
-- Query params — updated and cleaner
-- Model validation — Pydantic 2 is different, period
-- Form inputs — still as useful as ever
-- Nested bodies — for your blog posts, product UIs, etc
-- More expressive query filters
-- Response models — clean output, no leaks
-- Dependencies — the right way to manage them
-- Background tasks — don’t hold up the response
-- Custom exceptions — for when your client asks, “why 500?”