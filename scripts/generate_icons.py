"""Rebuild original simple geometric icons; no third-party artwork is used."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
for filename, color in [('app.ico', '#3273a8'), ('file.ico', '#3b8767')]:
    image = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    drawing = ImageDraw.Draw(image)
    drawing.rounded_rectangle((12, 20, 116, 112), radius=12, fill=color)
    drawing.rectangle((23, 10, 65, 30), fill=color)
    drawing.rounded_rectangle((28, 43, 99, 91), radius=6, fill='#f4f7fa')
    for y in (55, 68, 81):
        drawing.line((39, y, 87, y), fill=color, width=4)
    for directory in [root/'resources', root/'src/windows/icons']:
        directory.mkdir(parents=True, exist_ok=True)
        image.save(directory/filename, sizes=[(16,16),(32,32),(48,48),(128,128)])
