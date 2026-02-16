import json
from models import Category, Product


def seed_database(db):
    """Seed the database with categories and sample products."""

    categories_data = [
        {"name": "Necklaces", "slug": "necklaces"},
        {"name": "Earrings", "slug": "earrings"},
        {"name": "Bracelets", "slug": "bracelets"},
        {"name": "Rings", "slug": "rings"},
        {"name": "Anklets", "slug": "anklets"},
        {"name": "Hair Accessories", "slug": "hair-accessories"},
    ]

    categories = {}
    for cat_data in categories_data:
        cat = Category(**cat_data)
        db.add(cat)
        db.flush()
        categories[cat_data["slug"]] = cat.id

    products_data = [
        {
            "name": "Rose Petal Layered Necklace",
            "slug": "rose-petal-layered-necklace",
            "description": "A delicate multi-layered necklace featuring rose-gold plated petals cascading elegantly. Perfect for adding a touch of feminine grace to any outfit.",
            "price": 1299.0,
            "image_url": "https://picsum.photos/seed/jewel1/400/400",
            "images": json.dumps([
                "https://picsum.photos/seed/jewel1/400/400",
                "https://picsum.photos/seed/jewel1b/400/400",
                "https://picsum.photos/seed/jewel1c/400/400",
            ]),
            "category_id": categories["necklaces"],
            "stock": 35,
            "featured": True,
        },
        {
            "name": "Pearl Drop Pendant",
            "slug": "pearl-drop-pendant",
            "description": "A timeless pearl drop pendant on a fine rose-gold chain. This minimalist piece brings understated elegance to everyday wear.",
            "price": 899.0,
            "image_url": "https://picsum.photos/seed/jewel2/400/400",
            "images": json.dumps([
                "https://picsum.photos/seed/jewel2/400/400",
                "https://picsum.photos/seed/jewel2b/400/400",
                "https://picsum.photos/seed/jewel2c/400/400",
            ]),
            "category_id": categories["necklaces"],
            "stock": 50,
            "featured": False,
        },
        {
            "name": "Crystal Chandelier Earrings",
            "slug": "crystal-chandelier-earrings",
            "description": "Stunning chandelier-style earrings adorned with sparkling crystals. These statement pieces catch the light beautifully at every angle.",
            "price": 799.0,
            "image_url": "https://picsum.photos/seed/jewel3/400/400",
            "images": json.dumps([
                "https://picsum.photos/seed/jewel3/400/400",
                "https://picsum.photos/seed/jewel3b/400/400",
                "https://picsum.photos/seed/jewel3c/400/400",
            ]),
            "category_id": categories["earrings"],
            "stock": 45,
            "featured": True,
        },
        {
            "name": "Blush Stud Earrings",
            "slug": "blush-stud-earrings",
            "description": "Petite blush-pink crystal studs set in a rose-gold frame. A subtle everyday accessory that adds a hint of color and sparkle.",
            "price": 399.0,
            "image_url": "https://picsum.photos/seed/jewel4/400/400",
            "images": json.dumps([
                "https://picsum.photos/seed/jewel4/400/400",
                "https://picsum.photos/seed/jewel4b/400/400",
            ]),
            "category_id": categories["earrings"],
            "stock": 60,
            "featured": False,
        },
        {
            "name": "Charm Chain Bracelet",
            "slug": "charm-chain-bracelet",
            "description": "A dainty rose-gold chain bracelet adorned with tiny heart and star charms. Stackable and perfect for layering with other bracelets.",
            "price": 599.0,
            "image_url": "https://picsum.photos/seed/jewel5/400/400",
            "images": json.dumps([
                "https://picsum.photos/seed/jewel5/400/400",
                "https://picsum.photos/seed/jewel5b/400/400",
                "https://picsum.photos/seed/jewel5c/400/400",
            ]),
            "category_id": categories["bracelets"],
            "stock": 40,
            "featured": True,
        },
        {
            "name": "Twisted Cuff Bracelet",
            "slug": "twisted-cuff-bracelet",
            "description": "A sleek twisted cuff bracelet with a polished rose-gold finish. Its adjustable design ensures a comfortable fit for any wrist.",
            "price": 699.0,
            "image_url": "https://picsum.photos/seed/jewel6/400/400",
            "images": json.dumps([
                "https://picsum.photos/seed/jewel6/400/400",
                "https://picsum.photos/seed/jewel6b/400/400",
            ]),
            "category_id": categories["bracelets"],
            "stock": 30,
            "featured": False,
        },
        {
            "name": "Blossom Cocktail Ring",
            "slug": "blossom-cocktail-ring",
            "description": "A bold floral cocktail ring with layered petal details and a central crystal. A showstopping piece for special occasions.",
            "price": 499.0,
            "image_url": "https://picsum.photos/seed/jewel7/400/400",
            "images": json.dumps([
                "https://picsum.photos/seed/jewel7/400/400",
                "https://picsum.photos/seed/jewel7b/400/400",
                "https://picsum.photos/seed/jewel7c/400/400",
            ]),
            "category_id": categories["rings"],
            "stock": 55,
            "featured": True,
        },
        {
            "name": "Minimalist Band Ring",
            "slug": "minimalist-band-ring",
            "description": "A slim, polished rose-gold band with a subtle hammered texture. Elegant simplicity for daily wear or stacking.",
            "price": 299.0,
            "image_url": "https://picsum.photos/seed/jewel8/400/400",
            "images": json.dumps([
                "https://picsum.photos/seed/jewel8/400/400",
                "https://picsum.photos/seed/jewel8b/400/400",
            ]),
            "category_id": categories["rings"],
            "stock": 70,
            "featured": False,
        },
        {
            "name": "Starlight Anklet",
            "slug": "starlight-anklet",
            "description": "A delicate chain anklet with tiny star pendants that shimmer with every step. Perfect for summer and beach-day styling.",
            "price": 349.0,
            "image_url": "https://picsum.photos/seed/jewel9/400/400",
            "images": json.dumps([
                "https://picsum.photos/seed/jewel9/400/400",
                "https://picsum.photos/seed/jewel9b/400/400",
            ]),
            "category_id": categories["anklets"],
            "stock": 45,
            "featured": False,
        },
        {
            "name": "Crystal Vine Anklet",
            "slug": "crystal-vine-anklet",
            "description": "A graceful anklet featuring vine-inspired links set with tiny crystals. Adds a touch of sparkle to any look.",
            "price": 449.0,
            "image_url": "https://picsum.photos/seed/jewel10/400/400",
            "images": json.dumps([
                "https://picsum.photos/seed/jewel10/400/400",
                "https://picsum.photos/seed/jewel10b/400/400",
            ]),
            "category_id": categories["anklets"],
            "stock": 38,
            "featured": False,
        },
        {
            "name": "Pearl Blossom Hair Pin Set",
            "slug": "pearl-blossom-hair-pin-set",
            "description": "A set of three floral hair pins featuring faux pearls and crystal accents. Ideal for bridal styling or elegant updos.",
            "price": 549.0,
            "image_url": "https://picsum.photos/seed/jewel11/400/400",
            "images": json.dumps([
                "https://picsum.photos/seed/jewel11/400/400",
                "https://picsum.photos/seed/jewel11b/400/400",
                "https://picsum.photos/seed/jewel11c/400/400",
            ]),
            "category_id": categories["hair-accessories"],
            "stock": 25,
            "featured": False,
        },
        {
            "name": "Crystal Butterfly Hair Clip",
            "slug": "crystal-butterfly-hair-clip",
            "description": "A whimsical butterfly-shaped hair clip encrusted with sparkling crystals. Adds a magical, fairy-tale touch to your hairstyle.",
            "price": 399.0,
            "image_url": "https://picsum.photos/seed/jewel12/400/400",
            "images": json.dumps([
                "https://picsum.photos/seed/jewel12/400/400",
                "https://picsum.photos/seed/jewel12b/400/400",
            ]),
            "category_id": categories["hair-accessories"],
            "stock": 42,
            "featured": False,
        },
    ]

    for product_data in products_data:
        db.add(Product(**product_data))

    db.commit()
    print("Database seeded with categories and products!")
