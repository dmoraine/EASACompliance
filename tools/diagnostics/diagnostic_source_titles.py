#!/usr/bin/env python3
"""
Script de diagnostic pour afficher des exemples de source-title par type
"""

import sys
from pathlib import Path
from collections import defaultdict

# Importer le parser
sys.path.insert(0, str(Path(__file__).parent.parent))
from easacompliance import EASAParser, TopicType

def show_source_title_examples(xml_path: str):
    """
    Affiche des exemples de source-title pour chaque type de topic
    """
    print("=" * 80)
    print("🔍 EXEMPLES DE SOURCE-TITLE PAR TYPE")
    print("=" * 80)
    print()
    
    # Initialiser le parser
    print(f"📄 Chargement du fichier: {xml_path}")
    parser = EASAParser(xml_path)
    
    # Extraire tous les topics
    topics = parser.get_all_topics()
    print(f"✅ {len(topics)} topics extraits")
    print()
    
    # Regrouper par type
    examples = defaultdict(list)
    
    for topic in topics:
        type_key = topic.topic_type.value
        if len(examples[type_key]) < 10:  # Garder 10 exemples par type
            # Récupérer le source-title original depuis le XML
            source_title = f"{topic.reference} {topic.title}".strip() if topic.reference else topic.title
            examples[type_key].append({
                'source_title': source_title,
                'reference': topic.reference,
                'title': topic.title,
                'erules_id': topic.erules_id
            })
    
    # Afficher les exemples
    for type_value in sorted(examples.keys(), key=lambda x: len(examples[x]), reverse=True):
        print("=" * 80)
        print(f"Type: {type_value}")
        print("=" * 80)
        print()
        
        for i, ex in enumerate(examples[type_value][:5], 1):
            print(f"{i}. Source Title: '{ex['source_title']}'")
            print(f"   Reference extraite: '{ex['reference']}'")
            print(f"   Titre extrait: '{ex['title']}'")
            print(f"   ERules ID: {ex['erules_id']}")
            print()
    
    print("=" * 80)
    print("💡 ANALYSE")
    print("=" * 80)
    print()
    print("Si les références sont vides pour AMC/GM, cela signifie que le")
    print("pattern de regex ne correspond pas au format de leurs source-title.")
    print()
    print("La regex actuelle est :")
    print("  r'^([A-Z]{2,4}[\.\-\s][A-Z]{2,4}\.[0-9]+(?:\.[0-9]+)?)'")
    print()
    print("Cette regex capture des patterns comme :")
    print("  - ORO.FTL.110")
    print("  - CS-FTL.1.100 ou CS FTL.1.100")
    print()
    print("Mais ne capture PAS des patterns comme :")
    print("  - AMC1 ORO.FTL.110")
    print("  - GM1 ORO.FTL.110")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnostic_source_titles.py <path-to-xml>")
        sys.exit(1)
    
    xml_path = sys.argv[1]
    
    if not Path(xml_path).exists():
        print(f"❌ Erreur: Le fichier '{xml_path}' n'existe pas")
        sys.exit(1)
    
    show_source_title_examples(xml_path)

