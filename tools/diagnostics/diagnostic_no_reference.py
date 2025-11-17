#!/usr/bin/env python3
"""
Script de diagnostic pour afficher les topics sans référence
"""

import sys
from pathlib import Path
from collections import defaultdict

# Importer le parser
sys.path.insert(0, str(Path(__file__).parent.parent))
from easacompliance import EASAParser, TopicType

def show_topics_without_reference(xml_path: str):
    """
    Affiche des exemples de topics sans référence par type
    """
    print("=" * 80)
    print("🔍 TOPICS SANS RÉFÉRENCE")
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
        if not topic.reference:  # Seulement ceux sans référence
            type_key = topic.topic_type.value
            if len(examples[type_key]) < 10:  # Garder 10 exemples par type
                examples[type_key].append({
                    'title': topic.title,
                    'erules_id': topic.erules_id,
                    'content_preview': topic.content[:100] if topic.content else ""
                })
    
    # Afficher les exemples
    for type_value in sorted(examples.keys(), key=lambda x: len(examples[x]), reverse=True):
        print("=" * 80)
        print(f"Type: {type_value}")
        print(f"Nombre sans référence: {len(examples[type_value])}")
        print("=" * 80)
        print()
        
        for i, ex in enumerate(examples[type_value][:5], 1):
            print(f"{i}. Titre: '{ex['title']}'")
            print(f"   ERules ID: {ex['erules_id']}")
            if ex['content_preview']:
                print(f"   Contenu: {ex['content_preview']}...")
            print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnostic_no_reference.py <path-to-xml>")
        sys.exit(1)
    
    xml_path = sys.argv[1]
    
    if not Path(xml_path).exists():
        print(f"❌ Erreur: Le fichier '{xml_path}' n'existe pas")
        sys.exit(1)
    
    show_topics_without_reference(xml_path)

