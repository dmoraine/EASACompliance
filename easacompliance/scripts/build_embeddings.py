#!/usr/bin/env python3
"""
Script pour construire la base d'embeddings avec le Parser v2 (structure EASA)

Ce script utilise le nouveau parser basé sur la structure officielle EASA
pour construire une base d'embeddings complète avec tous les topics.
"""
import argparse
import sys
from pathlib import Path

# Ajouter le répertoire racine au path pour les imports
_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_root))

# Imports absolus depuis le package (le path est déjà configuré)
from easacompliance.parser import EASAParser, Topic, TopicType
# EmbeddingsManager sera importé seulement quand nécessaire (lazy import)
from tqdm import tqdm


def topic_to_paragraph_adapter(topic: Topic):
    """
    Adapte un Topic (v2) en format compatible avec Paragraph (v1) pour EmbeddingsManager.
    
    Cette fonction permet d'utiliser le nouveau parser v2 avec le système d'embeddings existant.
    """
    # Créer un objet compatible avec Paragraph
    class ParagraphAdapter:
        def __init__(self, topic: Topic):
            # Utiliser la référence si disponible, sinon générer un identifiant
            if topic.reference:
                self.reference = topic.reference
            elif topic.title:
                # Utiliser le titre comme référence (tronqué à 60 caractères)
                self.reference = topic.title[:60]
            else:
                # Dernier recours: utiliser l'ERules ID
                self.reference = f"ERULES-{topic.erules_id[-8:]}" if topic.erules_id else "UNKNOWN"
            
            self.title = topic.title
            self.content = topic.content
            self.paragraph_type = topic.topic_type  # Déjà un Enum
            self.topic_type = topic.topic_type  # Alias pour compatibilité avec embeddings.py
            self.metadata = {
                'erules_id': topic.erules_id,
                'category': self._extract_category(topic.reference) if topic.reference else "No-Category",
                'topic_type': topic.topic_type.value,
                'domain': topic.domain,
                'regulatory_subject': topic.regulatory_subject,
                'regulatory_source': topic.regulatory_source,
                'applicability_date': topic.applicability_date,
                'entry_into_force_date': topic.entry_into_force_date,
                'icao_reference': topic.icao_reference,
            }
        
        def _extract_category(self, reference: str) -> str:
            """Extrait la catégorie d'une référence (ex: ORO.FTL de ORO.FTL.110)"""
            if not reference:
                return "Unknown"
            parts = reference.split('.')
            if len(parts) >= 2:
                return f"{parts[0]}.{parts[1]}"
            # Pour les références style "AMC1 ORO.FTL.110"
            if ' ' in reference:
                ref_part = reference.split(' ')[-1]  # Prendre la dernière partie
                parts = ref_part.split('.')
                if len(parts) >= 2:
                    return f"{parts[0]}.{parts[1]}"
            return reference
        
        def get_full_text(self) -> str:
            """Retourne le texte complet pour l'embedding"""
            parts = []
            
            # Référence et titre
            if self.reference:
                parts.append(f"{self.reference} {self.title}".strip())
            
            # Contenu
            if self.content:
                parts.append(self.content)
            
            # Contexte réglementaire
            context_parts = []
            if self.metadata.get('regulatory_subject'):
                context_parts.append(f"Subject: {self.metadata['regulatory_subject']}")
            if self.metadata.get('domain'):
                context_parts.append(f"Domain: {self.metadata['domain']}")
            
            if context_parts:
                parts.append(" | ".join(context_parts))
            
            return "\n\n".join(parts)
    
    return ParagraphAdapter(topic)


def _get_embeddings_manager():
    """Import lazy de EmbeddingsManager"""
    from easacompliance.embeddings import EmbeddingsManager
    return EmbeddingsManager

def build_embeddings_database(
    xml_path: str,
    db_path: str = "easa_embeddings_v2.db",
    model_name: str = "all-MiniLM-L6-v2",
    pattern: str = None,
    topic_type_filter: list = None,
    batch_size: int = 32,
    regulatory_subject: str = None
):
    """
    Construit la base d'embeddings en utilisant le Parser v2.
    
    Args:
        xml_path: Chemin vers le fichier XML EASA
        db_path: Chemin vers la base SQLite
        model_name: Nom du modèle sentence-transformers
        pattern: Pattern regex pour filtrer les topics
        topic_type_filter: Liste de TopicType à inclure (ex: [TopicType.IR])
        batch_size: Taille des batches pour l'embedding
        regulatory_subject: Filtre par sujet réglementaire (ex: "Part-ORO")
    
    Returns:
        EmbeddingsManager configuré
    """
    print("=" * 80)
    print("🚀 CONSTRUCTION DE LA BASE D'EMBEDDINGS (Parser v2)")
    print("=" * 80)
    print()
    
    # Initialiser le parser
    parser = EASAParser(xml_path)
    
    # Extraire les topics
    print(f"\n📋 Extraction de la table des matières...")
    if pattern:
        print(f"   Pattern: {pattern}")
    if topic_type_filter:
        types_str = ", ".join([t.name for t in topic_type_filter])
        print(f"   Types: {types_str}")
    if regulatory_subject:
        print(f"   Sujet réglementaire: {regulatory_subject}")
    
    topics = parser.get_all_topics(
        pattern=pattern,
        topic_type_filter=topic_type_filter,
        regulatory_subject_filter=regulatory_subject,
        show_progress=False
    )
    
    print(f"✅ {len(topics)} topics à traiter")
    
    if len(topics) == 0:
        print("\n⚠️  ATTENTION: Aucun topic trouvé avec ces filtres!")
        
        # Afficher les catégories disponibles
        all_topics = parser.get_all_topics()
        stats = parser.get_statistics()
        
        print("\n📋 Catégories disponibles dans le document:")
        for category, count in list(stats['by_category'].items())[:20]:
            print(f"   • {category}: {count} topics")
        
        print("\n📋 Types de contenu disponibles:")
        for content_type, count in stats['by_type'].items():
            print(f"   • {content_type}: {count}")
        
        print("\n💡 Suggestion: Essayez sans filtre ou utilisez une catégorie de la liste ci-dessus")
        return None
    
    # Initialiser le gestionnaire d'embeddings
    print(f"\n🔧 Initialisation du gestionnaire d'embeddings...")
    print(f"🔧 Chargement du modèle: {model_name}")
    EmbeddingsManager = _get_embeddings_manager()
    manager = EmbeddingsManager(db_path=db_path, model_name=model_name)
    print(f"✅ Modèle chargé: {manager.embedding_dim} dimensions")
    print(f"✅ Base de données initialisée: {db_path}")
    
    # Convertir les topics en format compatible avec EmbeddingsManager
    print(f"\n📦 Conversion des topics...")
    paragraphs = []
    skipped_empty = 0
    
    for topic in tqdm(topics, desc="Conversion"):
        # Filtrer uniquement les topics complètement vides (pas de référence, pas de titre, pas de contenu)
        if not topic.reference and not topic.title and not topic.content:
            skipped_empty += 1
            continue
        
        adapter = topic_to_paragraph_adapter(topic)
        paragraphs.append(adapter)
    
    print(f"✅ {len(paragraphs)} topics convertis")
    if skipped_empty > 0:
        print(f"⏭️  {skipped_empty} topics vides ignorés")
    
    # Ajouter à la base de données par batch
    print(f"\n💾 Ajout à la base de données...")
    manager.add_paragraphs_batch(paragraphs, batch_size=batch_size)
    print(f"✅ {len(paragraphs)} topics ajoutés")
    
    # Afficher les statistiques
    print(f"\n📊 Statistiques:")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    
    return manager


def main():
    parser = argparse.ArgumentParser(
        description="Construire la base d'embeddings EASA (Parser v2)"
    )
    parser.add_argument(
        "--xml",
        help="Chemin vers un fichier XML EASA (mode fichier unique)"
    )
    parser.add_argument(
        "--dir",
        help="Répertoire contenant les fichiers XML EASA à parser (défaut: easy_access si --xml non fourni)"
    )
    parser.add_argument(
        "--db",
        default="easa_embeddings_v2.db",
        help="Chemin vers la base SQLite (défaut: easa_embeddings_v2.db)"
    )
    parser.add_argument(
        "--model",
        default="all-MiniLM-L6-v2",
        help="Modèle sentence-transformers (défaut: all-MiniLM-L6-v2)"
    )
    parser.add_argument(
        "--pattern",
        help="Pattern regex pour filtrer les topics (ex: 'ORO\\.FTL\\.')"
    )
    parser.add_argument(
        "--category",
        help="Catégorie à extraire (ex: 'ORO.FTL', 'CS FTL')"
    )
    parser.add_argument(
        "--types",
        nargs='+',
        choices=['IR', 'AMC', 'GM_IR', 'CS', 'GM_CS', 'ALL'],
        default=['ALL'],
        help="Types de topics à inclure (défaut: ALL)"
    )
    parser.add_argument(
        "--subject",
        help="Sujet réglementaire (ex: 'Part-ORO', 'Part-CAT')"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Taille des batches pour l'embedding (défaut: 32)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Vider la base de données existante avant de construire"
    )
    
    args = parser.parse_args()
    
    # Si --xml n'est pas fourni, utiliser le mode répertoire
    # Si --dir n'est pas fourni non plus, utiliser "easy_access" par défaut
    if args.xml is None:
        if args.dir is None:
            args.dir = "easy_access"
        dir_path = Path(args.dir)
        if not dir_path.exists():
            print(f"❌ Erreur: Le répertoire '{args.dir}' n'existe pas")
            return
        
        if not dir_path.is_dir():
            print(f"❌ Erreur: '{args.dir}' n'est pas un répertoire")
            return
        
        # Trouver tous les fichiers XML dans le répertoire
        xml_files = sorted(dir_path.glob("*.xml"))
        if not xml_files:
            print(f"❌ Erreur: Aucun fichier XML trouvé dans '{args.dir}'")
            return
        
        print("=" * 80)
        print("🚀 PARSING DE TOUS LES FICHIERS XML DANS LE RÉPERTOIRE")
        print("=" * 80)
        print(f"📁 Répertoire: {dir_path.absolute()}")
        print(f"📄 Fichiers trouvés: {len(xml_files)}")
        print()
        
        # Afficher la liste des fichiers
        for i, xml_file in enumerate(xml_files, 1):
            print(f"   {i}. {xml_file.name}")
        print()
        
        # Vider la base si demandé (seulement avant le premier fichier)
        if args.clear and Path(args.db).exists():
            print(f"🗑️  Suppression de la base existante: {args.db}")
            EmbeddingsManager = _get_embeddings_manager()
            manager = EmbeddingsManager(db_path=args.db, model_name=args.model)
            manager.clear_database()
            print()
        
        # Construire le pattern si une catégorie est spécifiée
        pattern = args.pattern
        if args.category and not pattern:
            category = args.category.strip()
            pattern = category.replace(" ", r"[\s.\-]") + r"\."
        
        # Construire le filtre de types
        topic_type_filter = None
        if 'ALL' not in args.types:
            type_map = {
                'IR': TopicType.IR,
                'AMC': TopicType.AMC,
                'GM_IR': TopicType.GM_IR,
                'CS': TopicType.CS,
                'GM_CS': TopicType.GM_CS,
            }
            topic_type_filter = [type_map[t] for t in args.types if t in type_map]
        
        # Parser chaque fichier
        successful_files = 0
        failed_files = []
        
        # Obtenir le nombre initial de topics dans la base
        EmbeddingsManager = _get_embeddings_manager()
        initial_manager = EmbeddingsManager(db_path=args.db, model_name=args.model)
        initial_stats = initial_manager.get_stats()
        topics_before = initial_stats.get('total_paragraphs', 0)
        
        for i, xml_file in enumerate(xml_files, 1):
            print("\n" + "=" * 80)
            print(f"📄 FICHIER {i}/{len(xml_files)}: {xml_file.name}")
            print("=" * 80)
            print()
            
            # Obtenir le nombre de topics avant ce fichier
            manager_before = EmbeddingsManager(db_path=args.db, model_name=args.model)
            stats_before = manager_before.get_stats()
            topics_before_file = stats_before.get('total_paragraphs', 0)
            
            try:
                manager = build_embeddings_database(
                    xml_path=str(xml_file),
                    db_path=args.db,
                    model_name=args.model,
                    pattern=pattern,
                    topic_type_filter=topic_type_filter,
                    batch_size=args.batch_size,
                    regulatory_subject=args.subject
                )
                
                if manager is not None:
                    stats_after = manager.get_stats()
                    topics_after_file = stats_after.get('total_paragraphs', 0)
                    topics_added = topics_after_file - topics_before_file
                    successful_files += 1
                    print(f"\n✅ Fichier traité avec succès: {topics_added} topics ajoutés (total: {topics_after_file})")
                else:
                    failed_files.append(xml_file.name)
                    print(f"\n⚠️  Aucun topic trouvé dans ce fichier")
                    
            except Exception as e:
                failed_files.append(xml_file.name)
                print(f"\n❌ Erreur lors du traitement de {xml_file.name}: {e}")
                import traceback
                traceback.print_exc()
        
        # Résumé final
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ FINAL")
        print("=" * 80)
        print()
        print(f"✅ Fichiers traités avec succès: {successful_files}/{len(xml_files)}")
        if failed_files:
            print(f"⚠️  Fichiers en échec: {len(failed_files)}")
            for failed_file in failed_files:
                print(f"   • {failed_file}")
        print()
        
        # Afficher les statistiques finales de la base
        EmbeddingsManager = _get_embeddings_manager()
        final_manager = EmbeddingsManager(db_path=args.db, model_name=args.model)
        final_stats = final_manager.get_stats()
        
        print(f"✅ Base de données: {args.db}")
        print(f"✅ Taille: {final_stats.get('db_size_mb', 0):.2f} MB")
        print(f"✅ Modèle: {final_stats.get('model_name', 'unknown')}")
        print(f"✅ Dimensions: {final_stats.get('embedding_dim', 0)}")
        print(f"✅ Total topics: {final_stats.get('total_paragraphs', 0)}")
        print(f"✅ Total embeddings: {final_stats.get('total_embeddings', 0)}")
        
        if 'categories' in final_stats:
            print(f"\n📋 Top 20 catégories:")
            for cat, count in sorted(final_stats['categories'].items(), key=lambda x: -x[1])[:20]:
                print(f"   • {cat}: {count} topics")
        
        print("\n" + "=" * 80)
        print("✅ TERMINÉ")
        print("=" * 80)
        return
    
    # Mode fichier unique: comportement original
    xml_path = Path(args.xml)
    if not xml_path.exists():
        print(f"❌ Erreur: Le fichier '{args.xml}' n'existe pas")
        return
    
    # Construire le pattern si une catégorie est spécifiée
    pattern = args.pattern
    if args.category and not pattern:
        # Créer un pattern flexible qui accepte différents séparateurs
        category = args.category.strip()
        # Remplacer l'espace par une classe de caractères qui accepte espace/point/tiret
        pattern = category.replace(" ", r"[\s.\-]") + r"\."
        
        print(f"📋 Catégorie: '{args.category}'")
        print(f"📋 Pattern généré: {pattern}")
        print("   (accepte espaces, points, et tirets comme séparateurs)")
    
    # Construire le filtre de types
    topic_type_filter = None
    if 'ALL' not in args.types:
        type_map = {
            'IR': TopicType.IR,
            'AMC': TopicType.AMC,
            'GM_IR': TopicType.GM_IR,
            'CS': TopicType.CS,
            'GM_CS': TopicType.GM_CS,
        }
        topic_type_filter = [type_map[t] for t in args.types if t in type_map]
    
    # Vider la base si demandé
    if args.clear and Path(args.db).exists():
        print(f"🗑️  Suppression de la base existante: {args.db}")
        EmbeddingsManager = _get_embeddings_manager()
        manager = EmbeddingsManager(db_path=args.db, model_name=args.model)
        manager.clear_database()
    
    # Construire la base
    manager = build_embeddings_database(
        xml_path=args.xml,
        db_path=args.db,
        model_name=args.model,
        pattern=pattern,
        topic_type_filter=topic_type_filter,
        batch_size=args.batch_size,
        regulatory_subject=args.subject
    )
    
    # Vérifier si la construction a réussi
    if manager is None:
        print("\n❌ Construction de la base annulée (aucun topic trouvé)")
        return
    
    # Afficher les statistiques finales
    print("\n" + "=" * 80)
    print("📊 STATISTIQUES FINALES")
    print("=" * 80)
    print()
    
    stats = manager.get_stats()
    print(f"✅ Base de données: {args.db}")
    print(f"✅ Taille: {stats.get('db_size_mb', 0):.2f} MB")
    print(f"✅ Modèle: {stats.get('model_name', 'unknown')}")
    print(f"✅ Dimensions: {stats.get('embedding_dim', 0)}")
    print(f"✅ Topics: {stats.get('total_paragraphs', 0)}")
    print(f"✅ Embeddings: {stats.get('total_embeddings', 0)}")
    
    if 'categories' in stats:
        print(f"\n📋 Catégories indexées:")
        for cat, count in sorted(stats['categories'].items(), key=lambda x: -x[1])[:20]:
            print(f"   • {cat}: {count} topics")
    
    # Tests de recherche
    print("\n" + "=" * 80)
    print("🔍 TEST DE RECHERCHE")
    print("=" * 80)
    print()
    
    test_queries = [
        "flight time limitations",
        "rest requirements for crew",
        "operator responsibilities"
    ]
    
    for query in test_queries:
        print(f"📝 Requête: '{query}'")
        results = manager.search(query, top_k=3, min_score=0.0)
        print("   Résultats:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.reference} (score: {result.score:.3f})")
            print(f"      {result.title}")
        print()
    
    print("=" * 80)
    print("✅ TERMINÉ")
    print("=" * 80)


if __name__ == "__main__":
    main()

