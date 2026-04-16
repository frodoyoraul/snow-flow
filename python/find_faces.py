#!/usr/bin/env python3
"""
Buscador de Rostros en Fotos - Script Python
Encuentra a una persona en miles de fotos usando reconocimiento facial.

Uso:
    python find_faces.py --reference CARPETA_REFERENCIA --search CARPETA_BUSQUEDA --output CARPETA_SALIDA

Ejemplo:
    python find_faces.py --reference fotos_mama --search google_photos --output coincidencias
"""

import argparse
import hashlib
import os
import pickle
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

try:
    import face_recognition
except ImportError:
    print("Error: la libreria face_recognition no esta instalada.")
    print("Ejecuta: pip install face_recognition")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: la libreria Pillow no esta instalada.")
    print("Ejecuta: pip install Pillow")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif', '.heic'}
MAX_DIMENSION = 1000
CACHE_FILENAME = '.face_encodings_cache.pkl'


def find_images(folder):
    """Encuentra todas las imagenes en una carpeta y subcarpetas."""
    images = []
    for root, _, files in os.walk(folder):
        for f in files:
            if Path(f).suffix.lower() in IMAGE_EXTENSIONS:
                images.append(os.path.join(root, f))
    return sorted(images)


def load_and_resize(image_path, max_dim=MAX_DIMENSION):
    """Carga una imagen y la redimensiona si es muy grande (mejora velocidad)."""
    try:
        img = Image.open(image_path)
        img = img.convert('RGB')
        w, h = img.size
        if max(w, h) > max_dim:
            scale = max_dim / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        import numpy as np
        return np.array(img)
    except Exception:
        return None


def file_hash(path):
    """Hash rapido basado en ruta + tamano + fecha de modificacion."""
    stat = os.stat(path)
    key = f"{path}|{stat.st_size}|{stat.st_mtime}"
    return hashlib.md5(key.encode()).hexdigest()


def load_cache(cache_path):
    """Carga cache de encodings desde disco."""
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            pass
    return {}


def save_cache(cache_path, cache):
    """Guarda cache de encodings a disco."""
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(cache, f)
    except Exception:
        pass


def encode_single_image(args):
    """Procesa una sola imagen y retorna sus encodings. Para uso con multiprocessing."""
    image_path, max_dim, model = args
    try:
        img_array = load_and_resize(image_path, max_dim)
        if img_array is None:
            return image_path, None, None

        locations = face_recognition.face_locations(img_array, model=model)
        if not locations:
            return image_path, [], file_hash(image_path)

        encodings = face_recognition.face_encodings(img_array, locations)
        return image_path, encodings, file_hash(image_path)
    except Exception as e:
        return image_path, None, None


def get_reference_encodings(reference_folder, model):
    """Extrae encodings de las fotos de referencia."""
    images = find_images(reference_folder)
    if not images:
        print(f"Error: no se encontraron imagenes en '{reference_folder}'")
        sys.exit(1)

    print(f"\nProcesando {len(images)} fotos de referencia...")
    all_encodings = []

    for img_path in images:
        img_array = load_and_resize(img_path)
        if img_array is None:
            print(f"  Advertencia: no se pudo cargar '{os.path.basename(img_path)}'")
            continue

        encodings = face_recognition.face_encodings(img_array)
        if encodings:
            all_encodings.extend(encodings)
            print(f"  {os.path.basename(img_path)}: {len(encodings)} rostro(s) detectado(s)")
        else:
            print(f"  {os.path.basename(img_path)}: ningun rostro detectado")

    if not all_encodings:
        print("\nError: no se detecto ningun rostro en las fotos de referencia.")
        print("Usa fotos donde el rostro sea claramente visible y este bien iluminado.")
        sys.exit(1)

    print(f"\nTotal: {len(all_encodings)} encoding(s) de referencia extraidos")
    return all_encodings


def search_photos(search_folder, reference_encodings, tolerance, model, workers, output_folder):
    """Busca coincidencias en la carpeta de busqueda."""
    all_images = find_images(search_folder)
    if not all_images:
        print(f"Error: no se encontraron imagenes en '{search_folder}'")
        sys.exit(1)

    print(f"\nBuscando en {len(all_images)} fotos (tolerancia: {tolerance}, modelo: {model}, workers: {workers})...")

    # Cargar cache
    cache_path = os.path.join(search_folder, CACHE_FILENAME)
    cache = load_cache(cache_path)
    cache_hits = 0

    os.makedirs(output_folder, exist_ok=True)
    matches = []
    errors = 0
    no_face = 0
    processed = 0

    # Preparar tareas (excluir las que ya estan en cache)
    tasks_to_process = []
    cached_results = {}

    for img_path in all_images:
        fh = file_hash(img_path)
        if fh in cache:
            cached_results[img_path] = cache[fh]
            cache_hits += 1
        else:
            tasks_to_process.append((img_path, MAX_DIMENSION, model))

    if cache_hits > 0:
        print(f"  {cache_hits} fotos encontradas en cache (se omiten del procesamiento)")

    # Procesar fotos en cache
    for img_path, encodings in cached_results.items():
        if encodings:
            results = face_recognition.compare_faces(reference_encodings, encodings[0], tolerance=tolerance)
            if True in results:
                distances = face_recognition.face_distance(reference_encodings, encodings[0])
                best_distance = min(distances)
                matches.append((img_path, best_distance))
        else:
            no_face += 1

    # Procesar nuevas fotos con multiprocessing
    new_cache_entries = {}

    if tasks_to_process:
        iterator = range(len(tasks_to_process))
        if tqdm:
            pbar = tqdm(total=len(tasks_to_process), desc="  Analizando", unit="foto")
        else:
            pbar = None

        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(encode_single_image, task): task[0] for task in tasks_to_process}

            for future in as_completed(futures):
                img_path = futures[future]
                try:
                    _, encodings, fh = future.result()

                    if encodings is None:
                        errors += 1
                    elif len(encodings) == 0:
                        no_face += 1
                        if fh:
                            new_cache_entries[fh] = []
                    else:
                        if fh:
                            new_cache_entries[fh] = encodings

                        for enc in encodings:
                            results = face_recognition.compare_faces(reference_encodings, enc, tolerance=tolerance)
                            if True in results:
                                distances = face_recognition.face_distance(reference_encodings, enc)
                                best_distance = min(distances)
                                matches.append((img_path, best_distance))
                                break
                except Exception:
                    errors += 1

                processed += 1
                if pbar:
                    pbar.update(1)
                elif processed % 100 == 0:
                    print(f"  Procesadas: {processed}/{len(tasks_to_process)}")

        if pbar:
            pbar.close()

    # Actualizar cache
    if new_cache_entries:
        cache.update(new_cache_entries)
        save_cache(cache_path, cache)
        print(f"  Cache actualizado con {len(new_cache_entries)} nuevas entradas")

    # Copiar coincidencias a carpeta de salida
    matches.sort(key=lambda x: x[1])
    used_names = {}

    for img_path, distance in matches:
        name = os.path.basename(img_path)
        if name in used_names:
            used_names[name] += 1
            base, ext = os.path.splitext(name)
            name = f"{base}_{used_names[name]}{ext}"
        else:
            used_names[name] = 1

        dest = os.path.join(output_folder, name)
        shutil.copy2(img_path, dest)

    return matches, errors, no_face


def main():
    parser = argparse.ArgumentParser(
        description='Buscador de Rostros en Fotos - Encuentra a una persona en miles de fotos'
    )
    parser.add_argument(
        '--reference', '-r', required=True,
        help='Carpeta con fotos de referencia de la persona a buscar'
    )
    parser.add_argument(
        '--search', '-s', required=True,
        help='Carpeta con las fotos donde buscar (puede tener subcarpetas)'
    )
    parser.add_argument(
        '--output', '-o', default='coincidencias',
        help='Carpeta donde guardar las coincidencias (default: coincidencias)'
    )
    parser.add_argument(
        '--tolerance', '-t', type=float, default=0.6,
        help='Tolerancia de coincidencia (0.0-1.0, menor=mas estricto, default: 0.6)'
    )
    parser.add_argument(
        '--model', '-m', choices=['hog', 'cnn'], default='hog',
        help='Modelo de deteccion: hog (rapido, CPU) o cnn (preciso, GPU). Default: hog'
    )
    parser.add_argument(
        '--workers', '-w', type=int, default=None,
        help='Numero de procesos paralelos (default: numero de CPUs)'
    )

    args = parser.parse_args()

    if not os.path.isdir(args.reference):
        print(f"Error: la carpeta '{args.reference}' no existe")
        sys.exit(1)
    if not os.path.isdir(args.search):
        print(f"Error: la carpeta '{args.search}' no existe")
        sys.exit(1)

    workers = args.workers or os.cpu_count() or 4

    print("=" * 60)
    print("  BUSCADOR DE ROSTROS EN FOTOS")
    print("=" * 60)

    # 1. Procesar referencia
    ref_encodings = get_reference_encodings(args.reference, args.model)

    # 2. Buscar coincidencias
    matches, errors, no_face = search_photos(
        args.search, ref_encodings, args.tolerance, args.model, workers, args.output
    )

    # 3. Resumen
    print("\n" + "=" * 60)
    print("  RESULTADOS")
    print("=" * 60)
    print(f"  Coincidencias encontradas:  {len(matches)}")
    print(f"  Fotos sin rostros:          {no_face}")
    print(f"  Errores:                    {errors}")
    print(f"  Guardadas en:               {os.path.abspath(args.output)}")

    if matches:
        print(f"\n  Mejores coincidencias:")
        for path, dist in matches[:10]:
            similarity = round((1 - dist) * 100)
            print(f"    {similarity}% - {os.path.basename(path)}")
        if len(matches) > 10:
            print(f"    ... y {len(matches) - 10} mas")

    print()


if __name__ == '__main__':
    main()
