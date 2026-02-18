# Product Images

Each category folder should contain at least 10 high-quality jewelry product images.

## Folder Structure

```
products/
  necklaces/        - Necklace product images (10+ images)
  rings/            - Ring product images (10+ images)
  earrings/         - Earring product images (10+ images)
  bracelets/        - Bracelet product images (10+ images)
  anklets/          - Anklet product images (10+ images)
  hair-accessories/ - Hair accessory product images (10+ images)
```

## Image Guidelines

- Format: JPG or WebP (for web performance)
- Resolution: Minimum 800x800px, recommended 1200x1200px
- Aspect ratio: 1:1 (square) preferred
- Background: Clean white or transparent
- Naming: Use descriptive names like `gold-layered-necklace-01.jpg`

## Current Status

All folders are created and ready for images. Currently using placeholder URLs from picsum.photos in the database seed data.

## How to Add Images

1. Place your product images in the appropriate category folder
2. Update the product `image_url` in the backend seed data or admin panel
3. Reference as: `/products/necklaces/your-image.jpg`

## Placeholder URLs (Current)

These are used in `backend/seed.py` until real images are added:
- https://picsum.photos/seed/jewel1/400/400
- https://picsum.photos/seed/jewel2/400/400
- etc.
