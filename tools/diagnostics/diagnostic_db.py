#!/usr/bin/env python3
"""
Script de diagnostic pour analyser les types de topics dans la base d'embeddings
"""

import sqlite3
import json
from pathlib import Path
from collections import Counter
import sys

def analyze_db_types(db_path: str):
    """
    Analyse les types de topics stockés dans la base de données
    """
    print("=" * 80)
    print("🔍 ANALYSE DES TYPES DANS LA BASE D'EMBEDDINGS")
    print("=" * 80)
    print()
    
    # Vérifier que la base existe
    if not Path(db_path).exists():
        print(f"❌ Erreur: La base '{db_path}' n'existe pas")
        return
    
    # Connexion à la base
    print(f"📄 Chargement de la base: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Compter le total
    cursor.execute("SELECT COUNT(*) FROM paragraphs")
    total = cursor.fetchone()[0]
    print(f"✅ {total} entrées dans la base")
    print()
    
    # Récupérer tous les métadonnées
    cursor.execute("SELECT metadata FROM paragraphs")
    rows = cursor.fetchall()
    
    # Analyser les types
    topic_types = []
    paragraph_types = []
    
    for row in rows:
        try:
            metadata = json.loads(row[0])
            
            # Type depuis paragraph_type (legacy)
            if 'paragraph_type' in metadata:
                paragraph_types.append(metadata['paragraph_type'])
            
            # Type depuis topic_type (nouveau)
            if 'topic_type' in metadata:
                topic_types.append(metadata['topic_type'])
        except:
            pass
    
    # Statistiques
    print("📊 STATISTIQUES PAR TYPE")
    print("-" * 80)
    
    if topic_types:
        print(f"\n📋 Types de topics (champ 'topic_type'): {len(topic_types)} entrées")
        type_counter = Counter(topic_types)
        for type_value, count in type_counter.most_common():
            percentage = (count / len(topic_types)) * 100
            print(f"  [{count:5d}] ({percentage:5.1f}%) {type_value}")
    
    if paragraph_types:
        print(f"\n📋 Types de paragraphes (champ 'paragraph_type'): {len(paragraph_types)} entrées")
        type_counter = Counter(paragraph_types)
        for type_value, count in type_counter.most_common():
            percentage = (count / len(paragraph_types)) * 100
            print(f"  [{count:5d}] ({percentage:5.1f}%) {type_value}")
    
    # Échantillon de métadonnées
    print()
    print("=" * 80)
    print("📝 ÉCHANTILLON DE MÉTADONNÉES")
    print("=" * 80)
    print()
    
    cursor.execute("SELECT reference, metadata FROM paragraphs LIMIT 5")
    samples = cursor.fetchall()
    
    for i, (reference, metadata_json) in enumerate(samples, 1):
        metadata = json.loads(metadata_json)
        print(f"{i}. Référence: {reference}")
        print(f"   Métadonnées:")
        for key in ['topic_type', 'category', 'domain', 'regulatory_subject']:
            if key in metadata:
                print(f"   - {key}: {metadata[key]}")
        print()
    
    # Vérifier la présence de contenu
    print("=" * 80)
    print("📊 STATISTIQUES DE CONTENU")
    print("=" * 80)
    print()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN length(content) > 0 THEN 1 ELSE 0 END) as with_content,
            SUM(CASE WHEN length(content) = 0 THEN 1 ELSE 0 END) as without_content
        FROM paragraphs
    """)
    total, with_content, without_content = cursor.fetchone()
    
    print(f"Total: {total}")
    print(f"Avec contenu: {with_content} ({(with_content/total)*100:.1f}%)")
    print(f"Sans contenu: {without_content} ({(without_content/total)*100:.1f}%)")
    
    conn.close()
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnostic_db.py <path-to-db>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    analyze_db_types(db_path)

