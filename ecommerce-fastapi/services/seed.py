from __future__ import annotations

from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Category, Product


SAMPLE_CATEGORIES = [
    ("Everyday Carry", "everyday-carry", "Useful objects for the daily rhythm."),
    ("Desk & Studio", "desk-studio", "Thoughtful tools for work and making."),
    ("Home Objects", "home-objects", "Small details that make a space yours."),
    ("Outdoor", "outdoor", "Simple essentials for getting outside."),
    ("Audio", "audio", "Clear sound, considered design."),
]

SAMPLE_PRODUCTS = [
    ("Field Notes Pocket Journal", "field-notes-pocket-journal", "Everyday Carry", "A sturdy pocket notebook with lay-flat binding and archival paper. Made for quick ideas, lists, and the things worth remembering.", "14.00", 42, "journal.svg"),
    ("Arc Key Organizer", "arc-key-organizer", "Everyday Carry", "A quiet, compact way to keep everyday keys together. A smooth anodized shell keeps pockets light and organized.", "28.00", 24, "carry.svg"),
    ("Canvas Utility Pouch", "canvas-utility-pouch", "Everyday Carry", "A hard-wearing cotton-canvas pouch for cables, stationery, or the small things that usually disappear at the bottom of a bag.", "22.00", 31, "carry.svg"),
    ("Slim Card Wallet", "slim-card-wallet", "Everyday Carry", "A minimal wallet cut from durable recycled fabric. Holds the essentials without adding bulk.", "32.00", 18, "carry.svg"),
    ("Everyday Bottle", "everyday-bottle", "Everyday Carry", "Double-wall stainless steel keeps your drink at the right temperature. A reliable 500 ml companion for the commute.", "26.00", 36, "bottle.svg"),
    ("Brass Desk Tray", "brass-desk-tray", "Desk & Studio", "A solid brass catchall with a soft brushed finish. Gives keys, clips, and small tools a proper place to land.", "38.00", 11, "desk.svg"),
    ("Grid Desk Pad", "grid-desk-pad", "Desk & Studio", "A generous, smooth-writing surface with a subtle printed grid and a non-slip natural rubber base.", "34.00", 27, "desk.svg"),
    ("Ceramic Pen Cup", "ceramic-pen-cup", "Desk & Studio", "Hand-finished stoneware with a satin glaze. Keeps daily tools close and adds a little calm to the desk.", "24.00", 16, "desk.svg"),
    ("Fountain Pen No. 02", "fountain-pen-no-02", "Desk & Studio", "A balanced everyday fountain pen with a fine stainless nib and a comfortable matte body.", "46.00", 8, "desk.svg"),
    ("Clip Lamp", "clip-lamp", "Desk & Studio", "A compact adjustable light with a strong spring clip, warm LED, and a clean silhouette for small spaces.", "52.00", 13, "home.svg"),
    ("Stoneware Pour-Over", "stoneware-pour-over", "Home Objects", "A single-cup ceramic dripper with a clean ribbed interior for an even, reliable morning brew.", "30.00", 20, "home.svg"),
    ("Linen Table Runner", "linen-table-runner", "Home Objects", "Washed linen with a soft hand and relaxed drape. Woven in a neutral tone that works every day.", "44.00", 9, "home.svg"),
    ("Amber Glass Carafe", "amber-glass-carafe", "Home Objects", "A hand-blown glass carafe that catches the light beautifully. Comfortable to pour and made for the table.", "40.00", 14, "home.svg"),
    ("Wool Throw", "wool-throw", "Home Objects", "A generously sized woven throw with a softly textured finish. Warm, breathable, and easy to live with.", "78.00", 6, "home.svg"),
    ("Pocket Field Compass", "pocket-field-compass", "Outdoor", "A clear, dependable baseplate compass with a luminous dial and protective lanyard for trail days.", "36.00", 19, "outdoor.svg"),
    ("Trail Light", "trail-light", "Outdoor", "A rechargeable, weather-resistant light with a wide beam and an easy-to-find tactile switch.", "42.00", 22, "outdoor.svg"),
    ("Camp Mug", "camp-mug", "Outdoor", "A lightweight enamel mug with a rolled rim and a speckled finish. Built for camp coffee and everyday use.", "18.00", 45, "outdoor.svg"),
    ("Foldaway Sit Pad", "foldaway-sit-pad", "Outdoor", "A compact closed-cell foam pad that folds flat and keeps a little comfort in your pack.", "16.00", 28, "outdoor.svg"),
    ("Studio Headphones", "studio-headphones", "Audio", "Comfortable over-ear headphones with a balanced sound profile and a detachable braided cable.", "96.00", 7, "audio.svg"),
    ("Pocket Bluetooth Speaker", "pocket-bluetooth-speaker", "Audio", "Room-filling sound from a small, durable speaker. Rechargeable and ready to move between rooms.", "68.00", 12, "audio.svg"),
]


def seed_sample_data(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(Category)) == 0:
        categories = [Category(name=name, slug=slug, description=description) for name, slug, description in SAMPLE_CATEGORIES]
        db.add_all(categories)
        db.flush()

    category_ids = {category.name: category.id for category in db.scalars(select(Category)).all()}
    if db.scalar(select(func.count()).select_from(Product)) == 0:
        products = []
        for title, slug, category, description, price, stock, image in SAMPLE_PRODUCTS:
            products.append(
                Product(
                    title=title,
                    slug=slug,
                    category_id=category_ids[category],
                    description=description,
                    price=Decimal(price),
                    stock=stock,
                    image_url=f"/static/images/{image}",
                )
            )
        db.add_all(products)
    db.commit()

