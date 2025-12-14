import os
import subprocess
import shutil
from pathlib import Path
from PIL import Image

def create_icns(source_png):
    if not os.path.exists(source_png):
        print(f"❌ Bestand niet gevonden: {source_png}")
        return

    print("🎨 Bezig met voorbereiden van vierkant logo...")
    
    # 1. Open origineel en maak vierkant
    img = Image.open(source_png)
    
    # Bepaal nieuwe afmeting (grootste zijde)
    max_dim = max(img.size)
    square_size = (max_dim, max_dim)
    
    # Maak transparant vierkant canvas
    square_img = Image.new('RGBA', square_size, (0, 0, 0, 0))
    
    # Plak logo in het midden
    offset = ((max_dim - img.size[0]) // 2, (max_dim - img.size[1]) // 2)
    square_img.paste(img, offset)
    
    # Resize naar 1024x1024 voor de master
    master_icon = square_img.resize((1024, 1024), Image.LANCZOS)
    master_path = "icon_1024x1024.png"
    master_icon.save(master_path)

    # 2. Maak de .iconset map aan (vereist voor mac iconutil)
    iconset_dir = "MyIcon.iconset"
    if os.path.exists(iconset_dir):
        shutil.rmtree(iconset_dir)
    os.makedirs(iconset_dir)

    # 3. Genereer alle vereiste formaten via 'sips' (ingebouwde Mac tool)
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    
    print("🔨 Icoon varianten genereren...")
    for size in sizes:
        # Normaal
        subprocess.run([
            'sips', '-z', str(size), str(size), master_path, 
            '--out', f"{iconset_dir}/icon_{size}x{size}.png"
        ], stdout=subprocess.DEVNULL)
        
        # Retina (@2x)
        if size < 512: # @2x bestaat tot 512 (wat 1024 wordt)
            double = size * 2
            subprocess.run([
                'sips', '-z', str(double), str(double), master_path, 
                '--out', f"{iconset_dir}/icon_{size}x{size}@2x.png"
            ], stdout=subprocess.DEVNULL)

    # 4. Converteer iconset naar icns
    print("📦 Inpakken naar .icns...")
    subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', 'icon.icns'])

    # 5. Opruimen
    shutil.rmtree(iconset_dir)
    os.remove(master_path)
    print("✅ Klaar! Bestand 'icon.icns' is aangemaakt.")

if __name__ == "__main__":
    create_icns("logo-sfc.png")
    create_icns("dock-icon.png")