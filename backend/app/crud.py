from typing import Optional

from sqlalchemy.orm import Session

from . import models

DEFAULT_COLUMNS = ["Backlog", "Discovery", "In Progress", "Review", "Done"]


# --- User ---

def get_user_by_google_id(db: Session, google_id: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.google_id == google_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_oauth_user(
    db: Session,
    google_id: str,
    email: str,
    display_name: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> models.User:
    user = models.User(
        google_id=google_id,
        email=email,
        display_name=display_name,
        avatar_url=avatar_url,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# --- Board ---

def get_board_for_user(db: Session, user_id: int) -> Optional[models.Board]:
    board = db.query(models.Board).filter(models.Board.user_id == user_id).first()
    if not board:
        return None
    board.columns.sort(key=lambda col: col.position)
    for col in board.columns:
        col.cards.sort(key=lambda card: card.position)
    return board


def create_board(db: Session, user_id: int, name: str) -> models.Board:
    board = models.Board(user_id=user_id, name=name)
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


def create_user_default_board(db: Session, user_id: int) -> models.Board:
    """Create the default board + columns for a newly registered user."""
    board = create_board(db, user_id, "My Project")
    for idx, title in enumerate(DEFAULT_COLUMNS):
        create_column(db, board.id, title, position=idx)
    db.refresh(board)
    return board


# --- Columns ---

def create_column(db: Session, board_id: int, title: str, position: int) -> models.KanbanColumn:
    column = models.KanbanColumn(board_id=board_id, title=title, position=position)
    db.add(column)
    db.commit()
    db.refresh(column)
    return column


def get_column(db: Session, column_id: int) -> Optional[models.KanbanColumn]:
    return db.query(models.KanbanColumn).filter(models.KanbanColumn.id == column_id).first()


def rename_column(db: Session, column_id: int, title: str) -> Optional[models.KanbanColumn]:
    column = get_column(db, column_id)
    if not column:
        return None
    column.title = title
    db.commit()
    db.refresh(column)
    return column


# --- Cards ---

def get_card(db: Session, card_id: int) -> Optional[models.Card]:
    return db.query(models.Card).filter(models.Card.id == card_id).first()


def create_card(
    db: Session, column_id: int, title: str, description: Optional[str] = None
) -> models.Card:
    max_pos = (
        db.query(models.Card)
        .filter(models.Card.column_id == column_id)
        .order_by(models.Card.position.desc())
        .first()
    )
    position = max_pos.position + 1 if max_pos else 0
    card = models.Card(column_id=column_id, title=title, description=description, position=position)
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def update_card(
    db: Session,
    card_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[models.Card]:
    card = get_card(db, card_id)
    if not card:
        return None
    if title is not None:
        card.title = title
    if description is not None:
        card.description = description
    db.commit()
    db.refresh(card)
    return card


def delete_card(db: Session, card_id: int) -> bool:
    card = get_card(db, card_id)
    if not card:
        return False
    column_id = card.column_id
    position = card.position
    db.delete(card)
    db.commit()
    # Shift remaining cards in the column to fill the gap
    cards = (
        db.query(models.Card)
        .filter(models.Card.column_id == column_id, models.Card.position > position)
        .order_by(models.Card.position)
        .all()
    )
    for c in cards:
        c.position -= 1
    db.commit()
    return True


def move_card(
    db: Session, card_id: int, target_column_id: int, target_position: int
) -> Optional[models.Card]:
    card = get_card(db, card_id)
    if not card:
        return None
    target_column = get_column(db, target_column_id)
    if not target_column:
        return None

    source_column_id = card.column_id
    source_position = card.position

    if source_column_id == target_column_id:
        if target_position == source_position:
            return card
        cards = (
            db.query(models.Card)
            .filter(models.Card.column_id == source_column_id)
            .order_by(models.Card.position)
            .all()
        )
        cards = [c for c in cards if c.id != card.id]
        target_position = max(0, min(target_position, len(cards)))
        cards.insert(target_position, card)
        for idx, c in enumerate(cards):
            c.position = idx
        db.commit()
        db.refresh(card)
        return card

    # Moving between columns
    source_cards = (
        db.query(models.Card)
        .filter(models.Card.column_id == source_column_id, models.Card.position > source_position)
        .order_by(models.Card.position)
        .all()
    )
    for c in source_cards:
        c.position -= 1

    target_cards = (
        db.query(models.Card)
        .filter(
            models.Card.column_id == target_column_id,
            models.Card.position >= target_position,
        )
        .order_by(models.Card.position)
        .all()
    )
    for c in target_cards:
        c.position += 1

    card.column_id = target_column_id
    card.position = target_position
    db.commit()
    db.refresh(card)
    return card


def seed_default_data(db: Session) -> None:
    """No-op: schema is created via create_all; users/boards are created on first OAuth login."""
    pass
