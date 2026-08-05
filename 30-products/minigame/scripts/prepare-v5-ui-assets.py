from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'asset-handoff-hermes-2026-07-12' / 'ui-v5-full' / 'source-gpt-image'
OUTPUT = ROOT / 'games' / 'find-anomaly' / 'elevator-console' / 'assets' / 'abnormal_elevator_visual_assets' / 'mobile_cctv_states'

SCENES = {
    'v5_00_protocol_start': ('00_protocol-start-source.png', (150, 270, 900, 900)),
    'v5_01_quick': ('01_quick-source.png', (60, 260, 980, 930)),
    'v5_02_investigation': ('02_investigation-source.png', (55, 325, 975, 980)),
    'v5_03_identity': ('03_identity-source.png', (90, 250, 930, 850)),
    'v5_04_classification': ('04_classification-source.png', (85, 220, 940, 820)),
    'v5_05_high_risk': ('05_high-risk-source.png', (90, 225, 935, 970)),
    'v5_06_protocol_query': ('06_protocol-query-source.png', (90, 220, 935, 950)),
    'v5_07_debrief': ('07_debrief-source.png', (95, 165, 925, 610)),
}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, (filename, crop) in SCENES.items():
        source = Image.open(SOURCE / filename).convert('RGB').crop(crop)
        scene = ImageOps.fit(source, (720, 420), Image.Resampling.LANCZOS)
        scene = ImageEnhance.Contrast(ImageEnhance.Color(scene).enhance(0.45)).enhance(1.14)
        destination = OUTPUT / f'{name}_mobile.png'
        scene.save(destination, optimize=True)
        print(f'[v5-assets] {destination.relative_to(ROOT)} {scene.size}')


if __name__ == '__main__':
    main()
