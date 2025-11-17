#!/usr/bin/env python3
"""
Script de test pour le système d'embeddings EASA.
Teste toutes les fonctionnalités principales.
"""

import sys
from pathlib import Path
from easacompliance import EmbeddingsManager, EASAParser
from easacompliance.scripts.build_embeddings import build_embeddings_database


def test_build_small_database():
    """Test 1: Construction d'une petite base (ORO.FTL)"""
    print("\n" + "=" * 80)
    print("TEST 1: Construction d'une petite base (ORO.FTL)")
    print("=" * 80)
    
    XML_FILE = "Easy Access Rules for Air Operations - February 2025 - xml.xml"
    
    if not Path(XML_FILE).exists():
        print(f"❌ Fichier XML non trouvé: {XML_FILE}")
        return False
    
    try:
        manager = build_embeddings_database(
            xml_path=XML_FILE,
            db_path="test_easa_ftl.db",
            pattern=r"ORO\.FTL\.[0-9]+",
            batch_size=16
        )
        
        stats = manager.get_stats()
        print(f"\n✅ Test réussi:")
        print(f"   • Paragraphes: {stats['total_paragraphs']}")
        print(f"   • Embeddings: {stats['total_embeddings']}")
        print(f"   • Taille: {stats['db_size_mb']} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_simple():
    """Test 2: Recherche simple"""
    print("\n" + "=" * 80)
    print("TEST 2: Recherche simple")
    print("=" * 80)
    
    if not Path("test_easa_ftl.db").exists():
        print("❌ Base de données de test non trouvée")
        print("   Exécutez d'abord le Test 1")
        return False
    
    try:
        manager = EmbeddingsManager(db_path="test_easa_ftl.db")
        
        test_queries = [
            "flight time limitations",
            "rest requirements for crew",
            "operator responsibilities",
            "fatigue risk management"
        ]
        
        print("\n🔍 Test de recherche:")
        for query in test_queries:
            print(f"\n📝 Requête: '{query}'")
            results = manager.search(query, top_k=3)
            
            if results:
                print(f"   ✅ {len(results)} résultats:")
                for i, r in enumerate(results, 1):
                    print(f"   {i}. {r.reference} (score: {r.score:.3f})")
            else:
                print("   ⚠️  Aucun résultat")
        
        print("\n✅ Test réussi")
        return True
        
    except Exception as e:
        print(f"\n❌ Test échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_with_filters():
    """Test 3: Recherche avec filtres"""
    print("\n" + "=" * 80)
    print("TEST 3: Recherche avec filtres")
    print("=" * 80)
    
    if not Path("test_easa_ftl.db").exists():
        print("❌ Base de données de test non trouvée")
        return False
    
    try:
        manager = EmbeddingsManager(db_path="test_easa_ftl.db")
        
        query = "flight time"
        
        # Sans filtre
        print(f"\n🔍 Recherche: '{query}' (sans filtre)")
        results_all = manager.search(query, top_k=5)
        print(f"   ✅ {len(results_all)} résultats")
        
        # Avec filtre de catégorie
        print(f"\n🔍 Recherche: '{query}' (catégorie: ORO.FTL)")
        results_filtered = manager.search(query, top_k=5, category_filter="ORO.FTL")
        print(f"   ✅ {len(results_filtered)} résultats")
        
        # Avec score minimum
        print(f"\n🔍 Recherche: '{query}' (score min: 0.5)")
        results_min_score = manager.search(query, top_k=5, min_score=0.5)
        print(f"   ✅ {len(results_min_score)} résultats")
        
        for r in results_min_score:
            print(f"      • {r.reference}: {r.score:.3f}")
        
        print("\n✅ Test réussi")
        return True
        
    except Exception as e:
        print(f"\n❌ Test échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_manual_validation():
    """Test 4: Validation de manuel"""
    print("\n" + "=" * 80)
    print("TEST 4: Validation de manuel")
    print("=" * 80)
    
    if not Path("test_easa_ftl.db").exists():
        print("❌ Base de données de test non trouvée")
        return False
    
    try:
        manager = EmbeddingsManager(db_path="test_easa_ftl.db")
        
        # Texte de test (extrait fictif d'un manuel)
        manual_text = """
        Flight crew members shall not exceed the maximum flight duty period
        as specified in the operations manual. The operator shall establish
        procedures to ensure adequate rest periods are provided before and
        after flight operations. Fatigue risk management procedures shall
        be implemented to monitor crew member fatigue levels.
        """
        
        print(f"\n📄 Texte du manuel ({len(manual_text)} caractères)")
        print("\n🔍 Recherche des paragraphes pertinents...")
        
        results = manager.search(manual_text, top_k=5, min_score=0.3)
        
        if results:
            print(f"\n✅ {len(results)} paragraphes pertinents trouvés:\n")
            
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.reference} - {result.title}")
                print(f"   Score: {result.score:.3f} ({result.score * 100:.1f}%)")
                
                if result.score >= 0.7:
                    print("   ✅ TRÈS PERTINENT")
                elif result.score >= 0.5:
                    print("   ⚠️  PERTINENT")
                else:
                    print("   ℹ️  POTENTIELLEMENT PERTINENT")
                print()
        else:
            print("⚠️  Aucun paragraphe pertinent trouvé")
        
        print("✅ Test réussi")
        return True
        
    except Exception as e:
        print(f"\n❌ Test échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_statistics():
    """Test 5: Statistiques"""
    print("\n" + "=" * 80)
    print("TEST 5: Statistiques")
    print("=" * 80)
    
    if not Path("test_easa_ftl.db").exists():
        print("❌ Base de données de test non trouvée")
        return False
    
    try:
        manager = EmbeddingsManager(db_path="test_easa_ftl.db")
        
        stats = manager.get_stats()
        
        print("\n📊 Statistiques de la base:")
        print(f"   • Total paragraphes: {stats['total_paragraphs']}")
        print(f"   • Total embeddings: {stats['total_embeddings']}")
        print(f"   • Taille DB: {stats['db_size_mb']} MB")
        print(f"   • Modèle: {stats['model_name']}")
        print(f"   • Dimensions: {stats['embedding_dim']}")
        
        if stats['categories']:
            print(f"\n📁 Catégories:")
            for cat, count in sorted(stats['categories'].items()):
                print(f"   • {cat}: {count} paragraphes")
        
        print("\n✅ Test réussi")
        return True
        
    except Exception as e:
        print(f"\n❌ Test échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export():
    """Test 6: Export JSON"""
    print("\n" + "=" * 80)
    print("TEST 6: Export JSON")
    print("=" * 80)
    
    if not Path("test_easa_ftl.db").exists():
        print("❌ Base de données de test non trouvée")
        return False
    
    try:
        manager = EmbeddingsManager(db_path="test_easa_ftl.db")
        
        output_file = "test_export.json"
        manager.export_to_json(output_file, category_filter="ORO.FTL")
        
        if Path(output_file).exists():
            size = Path(output_file).stat().st_size / 1024
            print(f"\n✅ Export réussi: {output_file} ({size:.1f} KB)")
            
            # Vérifier le contenu
            import json
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            print(f"   • Paragraphes exportés: {len(data['paragraphs'])}")
            print(f"   • Métadonnées: {data['metadata']}")
        else:
            print("❌ Fichier d'export non créé")
            return False
        
        print("\n✅ Test réussi")
        return True
        
    except Exception as e:
        print(f"\n❌ Test échoué: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup():
    """Nettoyer les fichiers de test"""
    print("\n" + "=" * 80)
    print("NETTOYAGE")
    print("=" * 80)
    
    files_to_remove = [
        "test_easa_ftl.db",
        "test_export.json"
    ]
    
    for file in files_to_remove:
        if Path(file).exists():
            Path(file).unlink()
            print(f"✅ Supprimé: {file}")


def main():
    print("\n" + "🧪" * 40)
    print("TESTS DU SYSTÈME D'EMBEDDINGS EASA")
    print("🧪" * 40)
    
    # Vérifier les dépendances
    try:
        import sentence_transformers
        import numpy
        import tqdm
        print("\n✅ Toutes les dépendances sont installées")
    except ImportError as e:
        print(f"\n❌ Dépendance manquante: {e}")
        print("\nInstallez les dépendances:")
        print("  pip install sentence-transformers numpy tqdm")
        return
    
    # Exécuter les tests
    tests = [
        ("Construction de la base", test_build_small_database),
        ("Recherche simple", test_search_simple),
        ("Recherche avec filtres", test_search_with_filters),
        ("Validation de manuel", test_manual_validation),
        ("Statistiques", test_statistics),
        ("Export JSON", test_export)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except KeyboardInterrupt:
            print("\n\n⚠️  Tests interrompus par l'utilisateur")
            break
        except Exception as e:
            print(f"\n❌ Erreur inattendue dans '{name}': {e}")
            results.append((name, False))
    
    # Résumé
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 80)
    print(f"Résultat: {passed}/{total} tests réussis ({passed/total*100:.0f}%)")
    print("=" * 80)
    
    # Nettoyage
    if input("\nNettoyer les fichiers de test? (o/N): ").lower() == 'o':
        cleanup()
    
    print("\n✅ Tests terminés")


if __name__ == "__main__":
    main()

