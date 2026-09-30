"""Account deletion shared by the mobile API and future account-management flows."""

from sqlalchemy import text

from db import SCHEMA


def delete_user_data(db, user_id: int) -> bool:
    """Permanently delete an account and all user-owned records in one transaction."""
    user = db.execute(
        text(f"SELECT id FROM {SCHEMA}.chat_users WHERE id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not user:
        return False

    db.execute(
        text(
            f"DELETE FROM {SCHEMA}.chat_messages "
            f"WHERE session_id IN (SELECT id FROM {SCHEMA}.chat_sessions WHERE user_id = :uid)"
        ),
        {"uid": user_id},
    )
    db.execute(
        text(f"DELETE FROM {SCHEMA}.chat_sessions WHERE user_id = :uid"),
        {"uid": user_id},
    )

    # Explicit deletion also supports older deployed databases created before
    # the chat user foreign keys used ON DELETE CASCADE.
    for table in ("user_profiles",):
        db.execute(
            text(f"DELETE FROM {SCHEMA}.{table} WHERE user_id = :uid"),
            {"uid": user_id},
        )

    db.execute(
        text(f"DELETE FROM {SCHEMA}.chat_users WHERE id = :uid"),
        {"uid": user_id},
    )
    db.commit()
    return True
