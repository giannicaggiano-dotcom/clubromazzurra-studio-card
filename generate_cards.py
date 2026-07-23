from pathlib import Path
import argparse
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps
from config import *

BASE_DIR = Path(__file__).resolve().parent


def get_font(path, size):
    return ImageFont.truetype(path, size=size)


def fit_font(draw, text, font_path, max_width, start_size, min_size=24):
    size = start_size
    while size >= min_size:
        f = get_font(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=f)
        if bbox[2] - bbox[0] <= max_width:
            return f
        size -= 2
    return get_font(font_path, min_size)


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        (0, 0, size[0] - 1, size[1] - 1),
        radius=radius,
        fill=255
    )
    return mask


def clear_area(draw, box):
    """
    Copre solo le aree variabili da riscrivere.
    Questa funzione NON deve richiamare sé stessa.
    """
    draw.rounded_rectangle(box, radius=8, fill=BLACK)


def paste_photo(card, photo_path):
    left, top, right, bottom = PHOTO_BOX
    width = right - left
    height = bottom - top

    draw = ImageDraw.Draw(card)

    # Pulisco il riquadro foto, mantenendo cornice e grafica generale
    draw.rounded_rectangle(
        PHOTO_BOX,
        radius=PHOTO_RADIUS,
        fill=BLACK,
        outline=GOLD,
        width=4
    )

    if not photo_path.exists():
        draw.rounded_rectangle(
            (left + 8, top + 8, right - 8, bottom - 8),
            radius=PHOTO_RADIUS - 6,
            fill=(16, 16, 16)
        )

        f = get_font(FONT_BOLD, 32)
        msg = "FOTO\nMANCANTE"
        bbox = draw.multiline_textbbox(
            (0, 0),
            msg,
            font=f,
            spacing=8,
            align="center"
        )

        x = left + (width - (bbox[2] - bbox[0])) / 2
        y = top + (height - (bbox[3] - bbox[1])) / 2

        draw.multiline_text(
            (x, y),
            msg,
            font=f,
            fill=(180, 180, 180),
            spacing=8,
            align="center"
        )
        return

    img = Image.open(photo_path).convert("RGB")

    img = ImageOps.fit(
        img,
        (width - 12, height - 12),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.35)
    )

    mask = rounded_mask(img.size, PHOTO_RADIUS - 8)
    card.paste(img, (left + 6, top + 6), mask)

    draw.rounded_rectangle(
        PHOTO_BOX,
        radius=PHOTO_RADIUS,
        outline=GOLD,
        width=4
    )


def normalizza_numero_tessera(valore):
    numero = str(valore).strip()

    if numero == "":
        return ""

    if numero.isdigit():
        return numero.zfill(7)

    return numero


def draw_member_data(card, row):
    draw = ImageDraw.Draw(card)

    nome = str(row.get("nome", "")).strip()
    cognome = str(row.get("cognome", "")).strip()
    full_name = f"{nome} {cognome}".strip()

    qualifica = str(row.get("qualifica", "Socio")).strip()
    numero = normalizza_numero_tessera(row.get("numero_tessera", ""))
    data = str(row.get("data_iscrizione", "")).strip()
    validita = str(row.get("validita", "")).strip()

    # Pulisco SOLO nome e qualifica.
    # Il master nuovo è già pulito nei campi numero, data e validità.
    clear_area(draw, NAME_CLEAR_BOX)
    clear_area(draw, ROLE_CLEAR_BOX)

    name_font = fit_font(
        draw,
        full_name,
        FONT_BOLD,
        NAME_CLEAR_BOX[2] - NAME_CLEAR_BOX[0] - 20,
        58,
        34
    )

    role_font = fit_font(
        draw,
        qualifica,
        FONT_BOLD,
        ROLE_CLEAR_BOX[2] - ROLE_CLEAR_BOX[0] - 20,
        42,
        26
    )

    number_font = get_font(FONT_BOLD, 34)
    date_font = get_font(FONT_BOLD, 34)
    validity_font = get_font(FONT_BOLD, 34)

    draw.text(
        NAME_POS,
        full_name,
        font=name_font,
        fill=WHITE,
        stroke_width=1,
        stroke_fill=(80, 80, 80)
    )

    draw.text(
        ROLE_POS,
        qualifica,
        font=role_font,
        fill=GOLD,
        stroke_width=1,
        stroke_fill=(45, 35, 0)
    )

    # Valori scritti sotto le etichette già presenti nel master
    draw.text((650, 560), numero, font=number_font, fill=WHITE)

    if data:
        draw.text((650, 680), data, font=date_font, fill=WHITE)

    if validita:
        draw.text((650, 800), validita.upper(), font=validity_font, fill=WHITE)


def render_one(template, row, photos_dir, output_dir):
    card = template.copy()

    foto = str(row.get("foto", "")).strip()
    photo_path = photos_dir / foto if foto else Path("__missing__")

    paste_photo(card, photo_path)
    draw_member_data(card, row)

    numero = normalizza_numero_tessera(row.get("numero_tessera", ""))
    cognome = str(row.get("cognome", "")).strip().replace(" ", "_")
    nome = str(row.get("nome", "")).strip().replace(" ", "_")

    out = output_dir / f"tessera_{numero}_{cognome}_{nome}.png"
    card.save(out, quality=95)

    return out


def make_pdf(png_files, pdf_path):
    images = [Image.open(p).convert("RGB") for p in png_files]

    if images:
        images[0].save(
            pdf_path,
            save_all=True,
            append_images=images[1:]
        )


def main():
    parser = argparse.ArgumentParser(
        description="Genera tessere Club Napoli Romazzurra da CSV."
    )

    parser.add_argument("--csv", default="soci.csv")
    parser.add_argument("--template", default="tessera_master.png")
    parser.add_argument("--photos", default="photos")
    parser.add_argument("--output", default="output")
    parser.add_argument("--pdf", action="store_true")

    args = parser.parse_args()

    template_path = BASE_DIR / args.template
    csv_path = BASE_DIR / args.csv
    photos_dir = BASE_DIR / args.photos
    output_dir = BASE_DIR / args.output

    template = Image.open(template_path).convert("RGB")

    if template.size != CANVAS_SIZE:
        raise ValueError(
            f"Template atteso {CANVAS_SIZE}, trovato {template.size}. "
            "Aggiorna config.py."
        )

    df = pd.read_csv(csv_path, dtype=str).fillna("")

    required = {"nome", "cognome", "numero_tessera", "qualifica", "foto"}
missing = required - set(df.columns)

if missing:
    raise ValueError(
        "Colonne mancanti nel CSV: " + ", ".join(sorted(missing))
    )

output_dir.mkdir(exist_ok=True)

generated = [
    render_one(template, row, photos_dir, output_dir)
    for _, row in df.iterrows()
]

if args.pdf:
    make_pdf(generated, output_dir / "tessere_soci.pdf")

print(f"Generate {len(generated)} tessere in {output_dir}")


if __name__ == "__main__":
    main()
