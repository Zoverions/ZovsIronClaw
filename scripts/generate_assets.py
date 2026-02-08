import os
import math
import io
from PIL import Image, ImageDraw, ImageOps
import icnsutil

# Define paths
ICONS_DIR = "apps/desktop/src-tauri/icons"
HEADER_IMAGE = "README-header.png"

# Ensure icons directory exists
os.makedirs(ICONS_DIR, exist_ok=True)

# Define sizes
SIZES = {
    "32x32.png": 32,
    "128x128.png": 128,
    "128x128@2x.png": 256,
    "icon.png": 512,
}

# Gradient Colors
COLOR_TOP_LEFT = (128, 0, 128)  # Purple
COLOR_BOTTOM_RIGHT = (0, 0, 0)  # Black
CLAW_COLOR = (0, 255, 255)      # Cyan

def create_base_icon(size):
    # Create image with alpha
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw gradient background (simple linear interpolation)
    for y in range(size):
        for x in range(size):
            # Calculate interpolation factor based on distance from top-left
            factor = (x + y) / (2 * size)
            r = int(COLOR_TOP_LEFT[0] * (1 - factor) + COLOR_BOTTOM_RIGHT[0] * factor)
            g = int(COLOR_TOP_LEFT[1] * (1 - factor) + COLOR_BOTTOM_RIGHT[1] * factor)
            b = int(COLOR_TOP_LEFT[2] * (1 - factor) + COLOR_BOTTOM_RIGHT[2] * factor)
            img.putpixel((x, y), (r, g, b, 255))

    # Draw Claw Marks (3 diagonal lines)
    # Line width proportional to size
    width = max(1, int(size * 0.05))

    # Coordinates for claw marks
    # Mark 1 (Left)
    draw.line([(size * 0.2, size * 0.2), (size * 0.4, size * 0.8)], fill=CLAW_COLOR, width=width)
    # Mark 2 (Center)
    draw.line([(size * 0.4, size * 0.15), (size * 0.6, size * 0.85)], fill=CLAW_COLOR, width=int(width * 1.2))
    # Mark 3 (Right)
    draw.line([(size * 0.6, size * 0.2), (size * 0.8, size * 0.8)], fill=CLAW_COLOR, width=width)

    return img

def generate_icons():
    print("Generating icons...")

    base_512 = create_base_icon(512)
    base_256 = create_base_icon(256)
    base_128 = create_base_icon(128)
    base_32 = create_base_icon(32)
    base_16 = create_base_icon(16)

    # Save PNGs
    for filename, size in SIZES.items():
        if size == 512:
            img = base_512
        elif size == 256:
            img = base_256
        elif size == 128:
            img = base_128
        elif size == 32:
            img = base_32
        else:
            img = base_512.resize((size, size), resample=Image.LANCZOS)

        path = os.path.join(ICONS_DIR, filename)
        img.save(path)
        print(f"Saved {path}")

    # Save ICO (Windows) - includes multiple sizes
    ico_path = os.path.join(ICONS_DIR, "icon.ico")
    base_256.save(ico_path, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"Saved {ico_path}")

    # Save ICNS (Mac) - Using icnsutil
    # Create temporary pngs for required sizes
    # icnsutil expects specific sizes: 16, 32, 64, 128, 256, 512, 1024
    # We can create an icns file manually or use Pillow to save as icns if supported (Pillow supports write since 9.1.0?)
    # Pillow supports saving ICNS format. Let's try Pillow first.
    try:
        icns_path = os.path.join(ICONS_DIR, "icon.icns")
        # Pillow requires append_images for other sizes
        # Base image is largest (512 or 1024 if we had it, but 512 is fine)
        # We need to provide (size, size) tuple for `sizes` argument or append images?
        # Actually Pillow's IcnsImagePlugin saves from multiple images.
        # save(fp, format='ICNS', append_images=[...])

        # We prepare list of images from large to small? Or just a list.
        # Usually: 16, 32, 48, 128, 256, 512.
        icns_images = [base_512, base_256, base_128, base_32, base_16]
        # Sort might not matter, but Pillow usually handles it.
        # But wait, base_512.save(path, format='ICNS', append_images=icns_images[1:])
        base_512.save(icns_path, format='ICNS', append_images=[base_256, base_128, base_32, base_16])
        print(f"Saved {icns_path} using Pillow")
    except Exception as e:
        print(f"Failed to save ICNS with Pillow: {e}")
        # Fallback to icnsutil if needed, but Pillow usually works for ICNS now.
        # If Pillow fails, we can try icnsutil.
        try:
            print("Trying icnsutil...")
            img = icnsutil.IcnsFile()

            def get_png_bytes(image):
                with io.BytesIO() as bio:
                    image.save(bio, format="PNG")
                    return bio.getvalue()

            img.add_media('ic09', data=get_png_bytes(base_512), width=512, height=512) # 512x512
            img.add_media('ic08', data=get_png_bytes(base_256), width=256, height=256) # 256x256
            img.add_media('ic07', data=get_png_bytes(base_128), width=128, height=128) # 128x128
            img.add_media('icp5', data=get_png_bytes(base_32), width=32, height=32)   # 32x32
            img.add_media('icp4', data=get_png_bytes(base_16), width=16, height=16)   # 16x16

            with open(icns_path, "wb") as f:
                img.write(f)
            print(f"Saved {icns_path} using icnsutil")
        except Exception as e2:
            print(f"Failed with icnsutil: {e2}")

def optimize_header():
    print("Optimizing header image...")
    if not os.path.exists(HEADER_IMAGE):
        print(f"Header image {HEADER_IMAGE} not found.")
        return

    try:
        img = Image.open(HEADER_IMAGE)
        original_size = os.path.getsize(HEADER_IMAGE)
        print(f"Original size: {original_size / 1024 / 1024:.2f} MB")

        # Optimize: Convert to P mode (palette) if appropriate or just optimize quality
        # PNG optimization in Pillow: optimize=True
        # If it's huge, maybe resize if it's too large dimensions?
        # Or reduce colors (quantize).

        # Try optimize=True first
        img.save(HEADER_IMAGE, optimize=True, quality=85)

        new_size = os.path.getsize(HEADER_IMAGE)
        print(f"New size: {new_size / 1024 / 1024:.2f} MB")

        if new_size >= original_size:
            print("Optimization didn't reduce size. Trying quantization.")
            img = img.quantize(colors=256, method=2) # method 2 is fast octree
            img.save(HEADER_IMAGE, optimize=True)
            new_size_q = os.path.getsize(HEADER_IMAGE)
            print(f"Quantized size: {new_size_q / 1024 / 1024:.2f} MB")

    except Exception as e:
        print(f"Failed to optimize header: {e}")

if __name__ == "__main__":
    generate_icons()
    optimize_header()
