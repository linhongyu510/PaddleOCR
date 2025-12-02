#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生成合成文本图像数据：每语言 N=20 张，每张≥50词/字符附近的段落长度，UTF-8。
使用 Noto 字体保证跨语言字形。
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import textwrap
import random
import json

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'benchmarks' / 'synthetic'
OUT.mkdir(parents=True, exist_ok=True)

LANG_SAMPLES = {
    'zh': [
        '傍晚下班后，我在地铁口看到一个卖花的小姑娘，手里捧着满满一束雏菊。',
        '她问：“哥哥，要不要买一朵？今天的花开得特别好。”我笑着点头。',
        '回到家时，锅里正咕嘟咕嘟地炖着汤，窗外雨点跳在阳台的绿萝上。',
        '我们围着餐桌聊起周末的计划——去郊外露营，带上咖啡和新买的帐篷。',
        '临睡前，她忽然问：“你有没有什么想实现的小愿望？”我说有，很多。'
    ],
    'ja': [
        '夕方、駅前のベンチで彼は紙コップのコーヒーを温めるように両手で包んだ。',
        '「ねえ、明日の朝市に行かない？」彼女は小さく笑ってうなずいた。',
        '帰り道、傘に当たる雨の音が静かなリズムになって、二人は同じ歩幅で歩いた。',
        '部屋に戻ると、窓の向こうで猫が伸びをしていて、湯気がやさしく灯りに揺れた。',
        '「願い事、ひとつだけ叶うなら？」彼は少し考えてから、そっと答えた。'
    ],
    'ko': [
        '퇴근길 편의점 앞에서 따뜻한 호빵을 사 들고, 나는 천천히 집 쪽으로 걸었다.',
        '“내일 아침 일찍 산책 갈래?” 그녀가 묻자, 나는 미소로 대답을 대신했다.',
        '비가 간간이 떨어지고, 가로등 아래 고양이는 꼬리를 말아 올린 채 앉아 있었다.',
        '집에 도착하니 전기포트가 보글거리며 물을 데우고, 창가 화분에 물방울이 매달렸다.',
        '“소원 하나만 빌 수 있다면?” 잠시 생각하다가, 나는 조용히 고개를 끄덕였다.'
    ],
    'th': [
        'หลังเลิกงานฉันแวะร้านข้าวแกงหน้าปากซอย กลิ่นต้มยำลอยออกมาต้อนรับเหมือนทุกวัน.',
        'พรุ่งนี้ไปตลาดเช้ากันไหม เธอยิ้มแล้วพยักหน้าเบา ๆ.',
        'ฝนโปรยลงเบา ๆ ตามทางเท้า แมวข้างบ้านขดตัวอยู่ใต้หลังคาอย่างสบายใจ.',
        'กลับถึงห้อง ไอน้ำจากหม้อต้มน้ำลอยขึ้นสะท้อนแสงไฟ สีเขียวของต้นไม้ริมหน้าต่างดูสดใส.',
        'ถ้าอธิษฐานได้ข้อเดียว เธอจะขออะไร ฉันนิ่งคิด ก่อนยิ้มรับอย่างเรียบง่าย.'
    ],
    'en': [
        'After work I stopped by the corner diner; the smell of tomato soup felt like an old song.',
        '“Shall we visit the morning market tomorrow?” she asked, and I nodded with a grin.',
        'Rain tapped gently on the umbrella, and the cat by the lamppost curled into a comma.',
        'Back home, the kettle hummed; steam drifted across the window where the pothos climbed.',
        '“If you had one wish,” she said. I paused, then answered softly in the quiet kitchen.'
    ],
    'vi': [
        'Chiều muộn tôi dừng lại trước quán cà phê góc phố, mùi bánh mì vừa nướng lan ra ấm áp.',
        'Mai mình ra chợ sớm nhé? cô ấy hỏi khẽ, tôi mỉm cười gật đầu.',
        'Mưa rơi lất phất trên ô, con mèo bên hiên cuộn mình nằm im.',
        'Về đến nhà, ấm đun nước khẽ kêu, hơi nước bay qua khung cửa sổ.',
        'Nếu chỉ có một điều ước, cô ấy nói, tôi ngẫm nghĩ rồi trả lời thật nhỏ.'
    ],
    'id': [
        'Sore hari aku singgah di warung sudut jalan; aroma sup tomat terasa seperti lagu lama.',
        'Besok ke pasar pagi, ya? katanya, dan aku mengangguk sambil tersenyum.',
        'Hujan mengetuk payung pelan, kucing di bawah lampu jalan meringkuk hangat.',
        'Sesampainya di rumah, ketel berdesis; uap melintas di jendela dapur.',
        'Jika punya satu harapan, dia berbisik; aku terdiam sejenak lalu menjawab pelan.'
    ]
}

def generate_variant(lang: str, idx: int, target_words: int = 50) -> str:
    rnd = random.Random(hash((lang, idx)) & 0xffffffff)
    bank = LANG_SAMPLES[lang]
    words: list[str] = []
    connectors = {
        'zh': ['然后', '后来', '不过', '于是', '同时'],
        'ja': ['そして', 'それから', 'しかし', 'つまり', '同時に'],
        'ko': ['그리고', '그러나', '그러면서', '한편', '이어서'],
        'th': ['แล้ว', 'จากนั้น', 'แต่ว่า', 'พร้อมกันนั้น', 'ในขณะเดียวกัน'],
        'en': ['Then', 'Afterwards', 'However', 'Meanwhile', 'Eventually'],
        'vi': ['Rồi', 'Sau đó', 'Tuy nhiên', 'Cùng lúc ấy'],
        'id': ['Lalu', 'Setelah itu', 'Namun', 'Sementara itu']
    }.get(lang, [''])
    k = min(len(bank), rnd.randint(5, 7))
    idxs = list(range(len(bank)))
    rnd.shuffle(idxs)
    idxs = idxs[:k]
    for j, ix in enumerate(idxs):
        base = bank[ix]
        # 不对泰语添加弯引号，避免字体回退；其他语言仅少量加引号
        if lang != 'th' and rnd.random() < 0.3:
            if lang == 'zh':
                base = f'“{base}”'
            elif lang == 'ja':
                base = f'「{base}」'
            elif lang == 'ko':
                base = f'“{base}”'
            else:
                base = f'"{base}"'
        if j > 0 and connectors:
            joiner = rnd.choice(connectors)
            words.append(joiner + ' ' + base)
        else:
            words.append(base)
        if len(' '.join(words).split()) >= target_words:
            break
    return ' '.join(words)

def get_font(lang: str, size: int = 28) -> ImageFont.FreeTypeFont:
    if lang == 'th':
        candidates = [
            str((OUT.parent / 'fonts' / 'NotoSansThai-Regular.ttf').resolve()),
            str((OUT.parent / 'fonts' / 'NotoSerifThai-Regular.ttf').resolve()),
            '/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf',
            '/usr/share/fonts/truetype/noto/NotoSansThaiLooped-Regular.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf'
        ]
    elif lang in ('zh', 'ja', 'ko'):
        candidates = [
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/noto/NotoSansSC-Regular.otf',
            '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf'
        ]
    else:
        candidates = [
            '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        ]
    for p in candidates:
        fp = Path(p)
        if fp.exists():
            try:
                return ImageFont.truetype(str(fp), size)
            except Exception:
                continue
    return ImageFont.load_default()

def render_paragraph(text: str, font: ImageFont.ImageFont, width: int = 1200) -> Image:
    margin = 32
    wrapper = textwrap.TextWrapper(width=36)
    lines = wrapper.wrap(text)
    line_h = font.getbbox('A')[3] - font.getbbox('A')[1] + 8
    height = margin * 2 + line_h * max(6, len(lines))
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = margin
    for line in lines:
        draw.text((margin, y), line, fill=(0, 0, 0), font=font)
        y += line_h
    return img

def main(n_per_lang: int = 20, langs: list[str] | None = None):
    manifest = []
    lang_items = LANG_SAMPLES.items() if not langs else [(l, LANG_SAMPLES[l]) for l in langs if l in LANG_SAMPLES]
    for lang, _ in lang_items:
        lang_dir = OUT / lang
        lang_dir.mkdir(parents=True, exist_ok=True)
        font = get_font(lang)
        for i in range(n_per_lang):
            text = generate_variant(lang, i, target_words=50)
            img = render_paragraph(text, font)
            path = lang_dir / f'{lang}_{i:02d}.png'
            img.save(path)
            manifest.append({'language': lang, 'path': str(path), 'tokens_est': len(text.split())})
    out = OUT / 'manifest.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print('✅ 合成数据已生成:', out)

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=20)
    ap.add_argument('--langs', type=str, default='')
    args = ap.parse_args()
    langs = [s for s in args.langs.split(',') if s] if args.langs else None
    main(n_per_lang=args.n, langs=langs)


