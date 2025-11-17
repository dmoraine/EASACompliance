#!/usr/bin/env python3
"""
Script interactif pour rechercher dans la base d'embeddings EASA.
Permet de valider la compliance d'un manuel en trouvant les paragraphes pertinents.
"""

import argparse
import sys
from pathlib import Path

# Ajouter le répertoire racine au path pour les imports
_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_root))

# Import lazy de EmbeddingsManager (seulement quand nécessaire)
def _get_embeddings_manager():
    """Import lazy de EmbeddingsManager"""
    from easacompliance.embeddings import EmbeddingsManager
    return EmbeddingsManager


def interactive_search(manager):
    """Mode interactif de recherche"""
    print("\n" + "=" * 80)
    print("🔍 MODE RECHERCHE INTERACTIF")
    print("=" * 80)
    print("\nCommandes disponibles:")
    print("  - Tapez votre requête pour rechercher")
    print("  - 'stats' pour voir les statistiques")
    print("  - 'quit' ou 'exit' pour quitter")
    print("=" * 80 + "\n")
    
    while True:
        try:
            query = input("🔎 Requête: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Au revoir!")
                break
            
            if query.lower() == 'stats':
                stats = manager.get_stats()
                print("\n📊 Statistiques:")
                for key, value in stats.items():
                    if key == 'categories':
                        print(f"   {key}:")
                        for cat, count in sorted(value.items(), key=lambda x: x[1], reverse=True)[:10]:
                            print(f"      • {cat}: {count}")
                    else:
                        print(f"   {key}: {value}")
                print()
                continue
            
            # Recherche
            print(f"\n🔄 Recherche en cours...")
            results = manager.search(query, top_k=5)
            
            if not results:
                print("❌ Aucun résultat trouvé\n")
                continue
            
            print(f"\n✅ {len(results)} résultats trouvés:\n")
            print("-" * 80)
            
            for i, result in enumerate(results, 1):
                print(f"\n{i}. 📋 {result.reference} - {result.title}")
                print(f"   📊 Score de similarité: {result.score:.3f} ({result.score * 100:.1f}%)")
                print(f"   📁 Type: {result.paragraph_type}")
                
                # Afficher un extrait du contenu
                content_preview = result.content[:200].replace('\n', ' ')
                if len(result.content) > 200:
                    content_preview += "..."
                print(f"   📄 Extrait: {content_preview}")
                
                if result.metadata:
                    print(f"   ℹ️  Métadonnées: {result.metadata}")
                
                print("-" * 80)
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"\n❌ Erreur: {e}\n")


def batch_search(manager, queries_file: str, output_file: str):
    """Mode batch: recherche depuis un fichier"""
    import json
    
    print(f"\n📖 Lecture des requêtes depuis: {queries_file}")
    
    with open(queries_file, 'r', encoding='utf-8') as f:
        queries = [line.strip() for line in f if line.strip()]
    
    print(f"✅ {len(queries)} requêtes chargées")
    
    results_data = []
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] Recherche: '{query}'")
        results = manager.search(query, top_k=5)
        
        results_data.append({
            "query": query,
            "results": [
                {
                    "reference": r.reference,
                    "title": r.title,
                    "score": r.score,
                    "content": r.content,
                    "type": r.paragraph_type,
                    "metadata": r.metadata
                }
                for r in results
            ]
        })
        
        print(f"   ✅ {len(results)} résultats trouvés")
    
    # Sauvegarder les résultats
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "total_queries": len(queries),
                "model": manager.model_name
            },
            "results": results_data
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Résultats sauvegardés dans: {output_file}")


def validate_manual_compliance(
    manager,
    manual_text: str,
    top_k: int = 10,
    min_score: float = 0.3
):
    """
    Valide la compliance d'un manuel en trouvant les paragraphes EASA pertinents.
    
    Args:
        manager: Gestionnaire d'embeddings
        manual_text: Texte du manuel à valider
        top_k: Nombre de paragraphes à retourner
        min_score: Score minimum de pertinence
    """
    print("\n" + "=" * 80)
    print("📋 VALIDATION DE COMPLIANCE")
    print("=" * 80)
    
    print(f"\n📄 Texte du manuel ({len(manual_text)} caractères)")
    print(f"🔍 Recherche des {top_k} paragraphes les plus pertinents...")
    
    results = manager.search(manual_text, top_k=top_k, min_score=min_score)
    
    if not results:
        print("\n❌ Aucun paragraphe pertinent trouvé")
        print(f"   Essayez de réduire le min_score (actuellement: {min_score})")
        return
    
    print(f"\n✅ {len(results)} paragraphes pertinents trouvés:\n")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. 📋 {result.reference} - {result.title}")
        print(f"   📊 Pertinence: {result.score:.3f} ({result.score * 100:.1f}%)")
        print(f"   📁 Type: {result.paragraph_type}")
        
        # Évaluation de la compliance
        if result.score >= 0.7:
            status = "✅ TRÈS PERTINENT"
        elif result.score >= 0.5:
            status = "⚠️  PERTINENT"
        elif result.score >= 0.3:
            status = "ℹ️  POTENTIELLEMENT PERTINENT"
        else:
            status = "❓ PEU PERTINENT"
        
        print(f"   {status}")
        
        # Afficher un extrait
        content_preview = result.content[:300].replace('\n', ' ')
        if len(result.content) > 300:
            content_preview += "..."
        print(f"\n   📄 Contenu:")
        print(f"   {content_preview}")
        
        print("\n" + "-" * 80)
    
    # Résumé
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ")
    print("=" * 80)
    
    very_relevant = sum(1 for r in results if r.score >= 0.7)
    relevant = sum(1 for r in results if 0.5 <= r.score < 0.7)
    potentially = sum(1 for r in results if 0.3 <= r.score < 0.5)
    
    print(f"\n✅ Très pertinents (≥70%): {very_relevant}")
    print(f"⚠️  Pertinents (50-70%): {relevant}")
    print(f"ℹ️  Potentiellement pertinents (30-50%): {potentially}")
    
    # Catégories concernées
    categories = set(r.reference.rsplit('.', 1)[0] for r in results if '.' in r.reference)
    if categories:
        print(f"\n📁 Catégories concernées:")
        for cat in sorted(categories):
            count = sum(1 for r in results if r.reference.startswith(cat))
            print(f"   • {cat}: {count} paragraphes")


def main():
    parser = argparse.ArgumentParser(
        description="Rechercher dans la base d'embeddings EASA"
    )
    
    parser.add_argument(
        "--db",
        type=str,
        default="easa_embeddings.db",
        help="Chemin de la base de données SQLite"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="Modèle sentence-transformers utilisé"
    )
    
    parser.add_argument(
        "--query",
        type=str,
        help="Requête de recherche unique"
    )
    
    parser.add_argument(
        "--queries-file",
        type=str,
        help="Fichier contenant les requêtes (une par ligne)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="search_results.json",
        help="Fichier de sortie pour le mode batch"
    )
    
    parser.add_argument(
        "--manual",
        type=str,
        help="Fichier texte du manuel à valider"
    )
    
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Nombre de résultats à retourner"
    )
    
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Score minimum de similarité (0-1)"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Mode interactif"
    )
    
    args = parser.parse_args()
    
    # Vérifier que la base existe
    if not Path(args.db).exists():
        print(f"❌ Erreur: Base de données non trouvée: {args.db}")
        print(f"   Utilisez 'python build_embeddings.py' pour la créer")
        return
    
    # Initialiser le gestionnaire
    print(f"🔧 Chargement de la base: {args.db}")
    EmbeddingsManager = _get_embeddings_manager()
    manager = EmbeddingsManager(db_path=args.db, model_name=args.model)
    
    stats = manager.get_stats()
    print(f"✅ Base chargée: {stats['total_paragraphs']} paragraphes")
    
    # Mode validation de manuel
    if args.manual:
        if not Path(args.manual).exists():
            print(f"❌ Erreur: Fichier manuel non trouvé: {args.manual}")
            return
        
        with open(args.manual, 'r', encoding='utf-8') as f:
            manual_text = f.read()
        
        validate_manual_compliance(
            manager,
            manual_text,
            top_k=args.top_k,
            min_score=args.min_score
        )
        return
    
    # Mode batch
    if args.queries_file:
        if not Path(args.queries_file).exists():
            print(f"❌ Erreur: Fichier de requêtes non trouvé: {args.queries_file}")
            return
        
        batch_search(manager, args.queries_file, args.output)
        return
    
    # Mode requête unique
    if args.query:
        print(f"\n🔍 Recherche: '{args.query}'")
        results = manager.search(args.query, top_k=args.top_k, min_score=args.min_score)
        
        if not results:
            print("❌ Aucun résultat trouvé")
            return
        
        print(f"\n✅ {len(results)} résultats:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.reference} - {result.title}")
            print(f"   Score: {result.score:.3f}")
            print(f"   {result.content[:100]}...")
            print()
        return
    
    # Mode interactif par défaut
    if args.interactive or not any([args.query, args.queries_file, args.manual]):
        interactive_search(manager)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

