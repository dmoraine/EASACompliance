#!/usr/bin/env python3
"""
Script de comparaison entre deux bases d'embeddings
"""

import sqlite3
import json
from pathlib import Path
from collections import Counter
import sys

def compare_databases(db1_path: str, db2_path: str):
    """
    Compare deux bases de données d'embeddings
    """
    print("=" * 80)
    print("📊 COMPARAISON DE BASES D'EMBEDDINGS")
    print("=" * 80)
    print()
    
    # Charger les deux bases
    print(f"Base 1: {db1_path}")
    print(f"Base 2: {db2_path}")
    print()
    
    if not Path(db1_path).exists():
        print(f"❌ Base 1 introuvable: {db1_path}")
        return
    
    if not Path(db2_path).exists():
        print(f"❌ Base 2 introuvable: {db2_path}")
        return
    
    # Analyser chaque base
    stats1 = analyze_single_db(db1_path)
    stats2 = analyze_single_db(db2_path)
    
    # Afficher la comparaison
    print("=" * 80)
    print("📈 COMPARAISON PAR TYPE")
    print("=" * 80)
    print()
    
    # Collecter tous les types
    all_types = set(stats1['types'].keys()) | set(stats2['types'].keys())
    
    print(f"{'Type':<70} {'Base 1':>10} {'Base 2':>10} {'Diff':>10}")
    print("-" * 100)
    
    total_diff = 0
    for type_name in sorted(all_types):
        count1 = stats1['types'].get(type_name, 0)
        count2 = stats2['types'].get(type_name, 0)
        diff = count2 - count1
        total_diff += diff
        
        # Symbole pour indiquer le changement
        symbol = ""
        if diff > 0:
            symbol = "✅"
        elif diff < 0:
            symbol = "⚠️"
        else:
            symbol = "  "
        
        print(f"{symbol} {type_name:<65} {count1:>10} {count2:>10} {diff:>+10}")
    
    print("-" * 100)
    print(f"   {'TOTAL':<65} {stats1['total']:>10} {stats2['total']:>10} {total_diff:>+10}")
    
    # Statistiques générales
    print()
    print("=" * 80)
    print("📊 STATISTIQUES GÉNÉRALES")
    print("=" * 80)
    print()
    
    print(f"Total topics:")
    print(f"  Base 1: {stats1['total']}")
    print(f"  Base 2: {stats2['total']}")
    print(f"  Gain: {total_diff:+d} ({(total_diff/stats1['total']*100):+.1f}%)")
    print()
    
    print(f"Topics avec contenu:")
    print(f"  Base 1: {stats1['with_content']}")
    print(f"  Base 2: {stats2['with_content']}")
    print()
    
    print(f"Topics sans contenu:")
    print(f"  Base 1: {stats1['without_content']}")
    print(f"  Base 2: {stats2['without_content']}")
    print()
    
    # Taille des fichiers
    size1 = Path(db1_path).stat().st_size / (1024 * 1024)
    size2 = Path(db2_path).stat().st_size / (1024 * 1024)
    
    print(f"Taille des fichiers:")
    print(f"  Base 1: {size1:.1f} MB")
    print(f"  Base 2: {size2:.1f} MB")
    print(f"  Différence: {size2-size1:+.1f} MB")
    print()

def analyze_single_db(db_path: str) -> dict:
    """Analyse une base de données"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total
    cursor.execute("SELECT COUNT(*) FROM paragraphs")
    total = cursor.fetchone()[0]
    
    # Par type
    cursor.execute("SELECT metadata FROM paragraphs")
    rows = cursor.fetchall()
    
    types = Counter()
    with_content = 0
    without_content = 0
    
    for row in rows:
        try:
            metadata = json.loads(row[0])
            if 'topic_type' in metadata:
                types[metadata['topic_type']] += 1
        except:
            pass
    
    # Contenu
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN length(content) > 0 THEN 1 ELSE 0 END) as with_content,
            SUM(CASE WHEN length(content) = 0 THEN 1 ELSE 0 END) as without_content
        FROM paragraphs
    """)
    with_content, without_content = cursor.fetchone()
    
    conn.close()
    
    return {
        'total': total,
        'types': dict(types),
        'with_content': with_content,
        'without_content': without_content
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python diagnostic_compare.py <base1.db> <base2.db>")
        sys.exit(1)
    
    compare_databases(sys.argv[1], sys.argv[2])

