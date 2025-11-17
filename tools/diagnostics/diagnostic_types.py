#!/usr/bin/env python3
"""
Script de diagnostic pour analyser les valeurs de TypeOfContent dans le XML EASA
"""

import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import sys

def analyze_type_of_content(xml_path: str):
    """
    Analyse tous les TypeOfContent présents dans le XML
    """
    print("=" * 80)
    print("🔍 ANALYSE DES TYPE OF CONTENT DANS LE XML EASA")
    print("=" * 80)
    print()
    
    # Parser le XML
    print(f"📄 Chargement du fichier: {xml_path}")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Namespace EASA
    ns = {'easa': 'http://www.easa.europa.eu/erules-export'}
    
    # Trouver tous les éléments <topic>
    topics = root.findall('.//easa:topic', ns)
    print(f"✅ {len(topics)} topics trouvés")
    print()
    
    # Collecter tous les TypeOfContent
    type_values = []
    topics_with_type = 0
    topics_without_type = 0
    
    for topic in topics:
        type_of_content = topic.get('TypeOfContent', '')
        if type_of_content:
            type_values.append(type_of_content)
            topics_with_type += 1
        else:
            topics_without_type += 1
    
    # Statistiques
    print("📊 STATISTIQUES GÉNÉRALES")
    print("-" * 80)
    print(f"Topics avec TypeOfContent: {topics_with_type}")
    print(f"Topics sans TypeOfContent: {topics_without_type}")
    print()
    
    # Compter les occurrences
    type_counter = Counter(type_values)
    
    print("📋 VALEURS DE TypeOfContent TROUVÉES")
    print("-" * 80)
    print(f"Nombre de valeurs distinctes: {len(type_counter)}")
    print()
    
    # Afficher toutes les valeurs avec leur count
    for type_value, count in type_counter.most_common():
        # Afficher la valeur avec caractères spéciaux visibles
        repr_value = repr(type_value)
        print(f"  [{count:5d}] {repr_value}")
    
    print()
    print("=" * 80)
    print("💡 COMPARAISON AVEC LES VALEURS ATTENDUES")
    print("=" * 80)
    print()
    
    # Valeurs attendues dans le parser
    expected = {
        'IR (Implementing rule);': 'TopicType.IR',
        'AMC to IR (Acceptable means of compliance to implementing rule);': 'TopicType.AMC',
        'GM to IR (Guidance material to implementing rule);': 'TopicType.GM_IR',
        'CS (Certification specification);': 'TopicType.CS',
        'GM to CS (Guidance material to certification specification);': 'TopicType.GM_CS',
        'Easy access rules;': 'TopicType.EASY_ACCESS',
    }
    
    print("Valeurs attendues par le parser:")
    for expected_value, enum_name in expected.items():
        count = type_counter.get(expected_value, 0)
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {enum_name}")
        print(f"      Attendu: {repr(expected_value)}")
        print(f"      Trouvé: {count} occurrences")
    
    print()
    print("=" * 80)
    print("🔧 VALEURS NON RECONNUES")
    print("=" * 80)
    print()
    
    # Trouver les valeurs qui ne matchent pas
    unrecognized = []
    for type_value, count in type_counter.items():
        if type_value not in expected:
            unrecognized.append((type_value, count))
    
    if unrecognized:
        print(f"⚠️  {len(unrecognized)} valeur(s) non reconnue(s):")
        for type_value, count in unrecognized:
            print(f"  [{count:5d}] {repr(type_value)}")
    else:
        print("✅ Toutes les valeurs sont reconnues")
    
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnostic_types.py <path-to-xml>")
        sys.exit(1)
    
    xml_path = sys.argv[1]
    
    if not Path(xml_path).exists():
        print(f"❌ Erreur: Le fichier '{xml_path}' n'existe pas")
        sys.exit(1)
    
    analyze_type_of_content(xml_path)

