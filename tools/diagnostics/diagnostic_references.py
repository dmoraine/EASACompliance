#!/usr/bin/env python3
"""
Script de diagnostic pour analyser les références par type de topic
"""

import sys
from pathlib import Path
from collections import defaultdict

# Importer le parser
sys.path.insert(0, str(Path(__file__).parent.parent))
from easacompliance import EASAParser, TopicType

def analyze_references_by_type(xml_path: str):
    """
    Analyse quels types de topics ont des références
    """
    print("=" * 80)
    print("🔍 ANALYSE DES RÉFÉRENCES PAR TYPE DE TOPIC")
    print("=" * 80)
    print()
    
    # Initialiser le parser
    print(f"📄 Chargement du fichier: {xml_path}")
    parser = EASAParser(xml_path)
    
    # Extraire tous les topics
    topics = parser.get_all_topics()
    print(f"✅ {len(topics)} topics extraits")
    print()
    
    # Analyser par type
    stats = defaultdict(lambda: {'total': 0, 'with_ref': 0, 'without_ref': 0, 'refs': []})
    
    for topic in topics:
        type_key = topic.topic_type.value
        stats[type_key]['total'] += 1
        
        if topic.reference:
            stats[type_key]['with_ref'] += 1
            # Garder quelques exemples
            if len(stats[type_key]['refs']) < 3:
                stats[type_key]['refs'].append((topic.reference, topic.title))
        else:
            stats[type_key]['without_ref'] += 1
    
    # Afficher les résultats
    print("📊 STATISTIQUES PAR TYPE")
    print("-" * 80)
    print()
    
    for type_value in sorted(stats.keys(), key=lambda x: stats[x]['total'], reverse=True):
        s = stats[type_value]
        total = s['total']
        with_ref = s['with_ref']
        without_ref = s['without_ref']
        pct_with = (with_ref / total) * 100 if total > 0 else 0
        
        print(f"Type: {type_value}")
        print(f"  Total: {total}")
        print(f"  Avec référence: {with_ref} ({pct_with:.1f}%)")
        print(f"  Sans référence: {without_ref} ({100-pct_with:.1f}%)")
        
        if s['refs']:
            print(f"  Exemples de références:")
            for ref, title in s['refs']:
                print(f"    • {ref}: {title[:60]}...")
        
        print()
    
    # Résumé
    print("=" * 80)
    print("📋 RÉSUMÉ")
    print("=" * 80)
    print()
    
    total_topics = len(topics)
    total_with_ref = sum(s['with_ref'] for s in stats.values())
    total_without_ref = sum(s['without_ref'] for s in stats.values())
    
    print(f"Total de topics: {total_topics}")
    print(f"Topics avec référence: {total_with_ref} ({(total_with_ref/total_topics)*100:.1f}%)")
    print(f"Topics sans référence: {total_without_ref} ({(total_without_ref/total_topics)*100:.1f}%)")
    print()
    
    if total_without_ref > 0:
        print("⚠️  ATTENTION: Des topics n'ont pas de référence !")
        print("   Le filtre 'if topic.reference' dans build_embeddings.py")
        print("   exclut ces topics de la base de données.")
        print()
        print("💡 Solution: Modifier le script pour inclure les topics sans référence")
        print("   ou utiliser un autre critère de filtrage.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnostic_references.py <path-to-xml>")
        sys.exit(1)
    
    xml_path = sys.argv[1]
    
    if not Path(xml_path).exists():
        print(f"❌ Erreur: Le fichier '{xml_path}' n'existe pas")
        sys.exit(1)
    
    analyze_references_by_type(xml_path)

