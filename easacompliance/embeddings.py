"""
EASA Embeddings Manager
=======================

Module pour générer et gérer les embeddings des paragraphes EASA.
Utilise sentence-transformers pour les embeddings et sqlite-vec pour le stockage.

Author: Didier
Date: 2025
"""

import sqlite3
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from tqdm import tqdm

# Import relatif ou absolu selon le contexte
try:
    from .parser import Topic, TopicType, EASAParser
except ImportError:
    # Fallback pour import direct
    from easacompliance.parser import Topic, TopicType, EASAParser

# Import lazy de sentence_transformers (seulement quand nécessaire)
_SentenceTransformer = None

def _get_sentence_transformer():
    """Import lazy de SentenceTransformer"""
    global _SentenceTransformer
    if _SentenceTransformer is None:
        try:
            from sentence_transformers import SentenceTransformer
            _SentenceTransformer = SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers n'est pas installé. "
                "Installez-le avec: pip install sentence-transformers"
            )
    return _SentenceTransformer


@dataclass
class SearchResult:
    """Résultat d'une recherche sémantique"""
    reference: str
    title: str
    content: str
    score: float  # Similarité (1 = identique, 0 = très différent)
    metadata: Dict[str, Any]
    paragraph_type: str
    
    def __repr__(self) -> str:
        return f"SearchResult(ref={self.reference}, score={self.score:.3f})"


class EmbeddingsManager:
    """
    Gestionnaire d'embeddings pour les paragraphes EASA.
    
    Utilise:
    - sentence-transformers pour générer les embeddings
    - sqlite-vec pour le stockage et la recherche vectorielle
    """
    
    def __init__(
        self,
        db_path: str = "easa_embeddings.db",
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialise le gestionnaire d'embeddings.
        
        Args:
            db_path: Chemin vers la base de données SQLite
            model_name: Nom du modèle sentence-transformers à utiliser
                       Options recommandées:
                       - 'all-MiniLM-L6-v2': Rapide, 384 dimensions (défaut)
                       - 'all-mpnet-base-v2': Plus précis, 768 dimensions
                       - 'paraphrase-multilingual-MiniLM-L12-v2': Multilingue
        """
        self.db_path = Path(db_path)
        self.model_name = model_name
        
        print(f"🔧 Chargement du modèle: {model_name}")
        SentenceTransformer = _get_sentence_transformer()
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✅ Modèle chargé: {self.embedding_dim} dimensions")
        
        # Initialiser la base de données
        self._init_database()
    
    def _init_database(self):
        """Initialise la base de données SQLite avec sqlite-vec"""
        conn = sqlite3.connect(str(self.db_path))
        
        # Créer la table principale pour les paragraphes
        conn.execute("""
            CREATE TABLE IF NOT EXISTS paragraphs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                full_text TEXT NOT NULL,
                paragraph_type TEXT NOT NULL,
                category TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Créer la table pour les embeddings
        # Note: sqlite-vec utilise une extension, on stocke les embeddings en BLOB
        conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY,
                paragraph_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                model_name TEXT NOT NULL,
                FOREIGN KEY (paragraph_id) REFERENCES paragraphs(id)
            )
        """)
        
        # Index pour accélérer les recherches
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_reference 
            ON paragraphs(reference)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_category 
            ON paragraphs(category)
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_paragraph_id 
            ON embeddings(paragraph_id)
        """)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Base de données initialisée: {self.db_path}")
    
    def add_paragraph(
        self,
        paragraph: Topic,
        generate_embedding: bool = True
    ) -> int:
        """
        Ajoute un paragraphe à la base de données.
        
        Args:
            paragraph: Objet Topic à ajouter
            generate_embedding: Si True, génère l'embedding automatiquement
            
        Returns:
            ID du paragraphe dans la base de données
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Extraire la catégorie
        category = paragraph.reference.rsplit('.', 1)[0] if '.' in paragraph.reference else None
        
        # Préparer les données
        full_text = paragraph.get_full_text()
        metadata_json = json.dumps(paragraph.metadata)
        
        try:
            # Insérer le paragraphe
            cursor.execute("""
                INSERT INTO paragraphs (reference, title, content, full_text, paragraph_type, category, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                paragraph.reference,
                paragraph.title,
                paragraph.content,
                full_text,
                    paragraph.topic_type.value,
                category,
                metadata_json
            ))
            
            paragraph_id = cursor.lastrowid
            
            # Générer et stocker l'embedding
            if generate_embedding:
                embedding = self.model.encode(full_text, convert_to_numpy=True)
                embedding_blob = embedding.astype(np.float32).tobytes()
                
                cursor.execute("""
                    INSERT INTO embeddings (paragraph_id, embedding, model_name)
                    VALUES (?, ?, ?)
                """, (paragraph_id, embedding_blob, self.model_name))
            
            conn.commit()
            return paragraph_id
            
        except sqlite3.IntegrityError:
            # Le paragraphe existe déjà
            cursor.execute(
                "SELECT id FROM paragraphs WHERE reference = ?",
                (paragraph.reference,)
            )
            paragraph_id = cursor.fetchone()[0]
            return paragraph_id
            
        finally:
            conn.close()
    
    def add_paragraphs_batch(
        self,
        paragraphs: List[Topic],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> int:
        """
        Ajoute plusieurs paragraphes en batch (optimisé).
        
        Args:
            paragraphs: Liste de paragraphes à ajouter
            batch_size: Taille des batches pour l'encodage
            show_progress: Afficher la barre de progression
            
        Returns:
            Nombre de paragraphes ajoutés
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        added_count = 0
        iterator = tqdm(paragraphs, desc="Ajout des paragraphes") if show_progress else paragraphs
        
        # Préparer tous les textes pour l'encodage batch
        texts = [p.get_full_text() for p in paragraphs]
        
        # Générer tous les embeddings en batch (beaucoup plus rapide)
        print(f"🔄 Génération des embeddings pour {len(texts)} paragraphes...")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        
        # Insérer les paragraphes et embeddings
        for paragraph, embedding in zip(iterator, embeddings):
            try:
                # Extraire la catégorie
                category = None
                if paragraph.reference:
                    parts = paragraph.reference.split('.')
                    if len(parts) >= 2:
                        category = f"{parts[0]}.{parts[1]}"
                    else:
                        category = paragraph.reference
                
                full_text = paragraph.get_full_text()
                metadata_json = json.dumps(paragraph.metadata)
                
                # Insérer le paragraphe
                cursor.execute("""
                    INSERT INTO paragraphs (reference, title, content, full_text, paragraph_type, category, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    paragraph.reference,
                    paragraph.title,
                    paragraph.content,
                    full_text,
                    paragraph.topic_type.value,
                    category,
                    metadata_json
                ))
                
                paragraph_id = cursor.lastrowid
                
                # Insérer l'embedding
                embedding_blob = embedding.astype(np.float32).tobytes()
                cursor.execute("""
                    INSERT INTO embeddings (paragraph_id, embedding, model_name)
                    VALUES (?, ?, ?)
                """, (paragraph_id, embedding_blob, self.model_name))
                
                added_count += 1
                
            except sqlite3.IntegrityError:
                # Paragraphe déjà existant, on passe
                continue
        
        conn.commit()
        conn.close()
        
        return added_count
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """
        Recherche sémantique de paragraphes similaires à la requête.
        
        Args:
            query: Texte de la requête
            top_k: Nombre de résultats à retourner
            category_filter: Filtrer par catégorie (ex: "ORO.FTL")
            min_score: Score minimum de similarité (0-1)
            
        Returns:
            Liste de SearchResult triée par similarité décroissante
        """
        # Générer l'embedding de la requête
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Récupérer tous les embeddings (avec filtre optionnel)
        if category_filter:
            cursor.execute("""
                SELECT p.id, p.reference, p.title, p.content, p.paragraph_type, 
                       p.category, p.metadata, e.embedding
                FROM paragraphs p
                JOIN embeddings e ON p.id = e.paragraph_id
                WHERE p.category = ?
            """, (category_filter,))
        else:
            cursor.execute("""
                SELECT p.id, p.reference, p.title, p.content, p.paragraph_type,
                       p.category, p.metadata, e.embedding
                FROM paragraphs p
                JOIN embeddings e ON p.id = e.paragraph_id
            """)
        
        results = []
        for row in cursor.fetchall():
            pid, reference, title, content, ptype, category, metadata_json, embedding_blob = row
            
            # Reconstruire l'embedding
            embedding = np.frombuffer(embedding_blob, dtype=np.float32)
            
            # Calculer la similarité cosinus
            similarity = self._cosine_similarity(query_embedding, embedding)
            
            # Filtrer par score minimum
            if similarity < min_score:
                continue
            
            # Créer le résultat
            metadata = json.loads(metadata_json) if metadata_json else {}
            result = SearchResult(
                reference=reference,
                title=title,
                content=content,
                score=float(similarity),
                metadata=metadata,
                paragraph_type=ptype
            )
            results.append(result)
        
        conn.close()
        
        # Trier par score décroissant et limiter
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calcule la similarité cosinus entre deux vecteurs"""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la base de données"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Nombre total de paragraphes
        cursor.execute("SELECT COUNT(*) FROM paragraphs")
        total_paragraphs = cursor.fetchone()[0]
        
        # Nombre d'embeddings
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        total_embeddings = cursor.fetchone()[0]
        
        # Paragraphes par catégorie
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM paragraphs
            GROUP BY category
            ORDER BY count DESC
        """)
        by_category = dict(cursor.fetchall())
        
        # Taille de la base de données
        db_size = self.db_path.stat().st_size / (1024 * 1024)  # MB
        
        conn.close()
        
        return {
            "total_paragraphs": total_paragraphs,
            "total_embeddings": total_embeddings,
            "categories": by_category,
            "db_size_mb": round(db_size, 2),
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim
        }
    
    def clear_database(self):
        """Vide complètement la base de données"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("DELETE FROM embeddings")
        conn.execute("DELETE FROM paragraphs")
        conn.commit()
        conn.close()
        print("✅ Base de données vidée")
    
    def export_to_json(self, output_path: str, category_filter: Optional[str] = None):
        """
        Exporte les paragraphes en JSON (sans les embeddings).
        
        Args:
            output_path: Chemin du fichier JSON de sortie
            category_filter: Filtrer par catégorie (optionnel)
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if category_filter:
            cursor.execute("""
                SELECT reference, title, content, paragraph_type, category, metadata
                FROM paragraphs
                WHERE category = ?
            """, (category_filter,))
        else:
            cursor.execute("""
                SELECT reference, title, content, paragraph_type, category, metadata
                FROM paragraphs
            """)
        
        paragraphs = []
        for row in cursor.fetchall():
            reference, title, content, ptype, category, metadata_json = row
            paragraphs.append({
                "reference": reference,
                "title": title,
                "content": content,
                "type": ptype,
                "category": category,
                "metadata": json.loads(metadata_json) if metadata_json else {}
            })
        
        conn.close()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "total": len(paragraphs),
                    "category_filter": category_filter,
                    "model": self.model_name
                },
                "paragraphs": paragraphs
            }, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {len(paragraphs)} paragraphes exportés vers: {output_path}")


def build_embeddings_database(
    xml_path: str,
    db_path: str = "easa_embeddings.db",
    model_name: str = "all-MiniLM-L6-v2",
    pattern: Optional[str] = None,
    batch_size: int = 32
) -> EmbeddingsManager:
    """
    Fonction utilitaire pour construire la base d'embeddings depuis un fichier XML.
    
    Args:
        xml_path: Chemin vers le fichier XML EASA
        db_path: Chemin de la base de données
        model_name: Modèle sentence-transformers à utiliser
        pattern: Pattern regex pour filtrer les paragraphes (optionnel)
        batch_size: Taille des batches pour l'encodage
        
    Returns:
        Instance de EmbeddingsManager
    """
    print("=" * 80)
    print("🚀 CONSTRUCTION DE LA BASE D'EMBEDDINGS")
    print("=" * 80)
    
    # Initialiser le parser
    print(f"\n📖 Chargement du document XML...")
    parser = EASAParser(xml_path)
    
    # Obtenir la table des matières
    print(f"\n📋 Extraction de la table des matières...")
    if pattern:
        print(f"   Pattern: {pattern}")
    toc = parser.get_table_of_contents(pattern=pattern)
    print(f"✅ {len(toc)} paragraphes à traiter")
    
    # Vérifier si des paragraphes ont été trouvés
    if len(toc) == 0:
        print("\n⚠️  ATTENTION: Aucun paragraphe trouvé avec ce pattern!")
        if pattern:
            print(f"   Pattern utilisé: {pattern}")
        print("\n📋 Catégories disponibles dans le document:")
        categories = parser.get_categories()
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"   • {cat}: {count} paragraphes")
        print("\n💡 Suggestion: Utilisez --category avec une catégorie de la liste ci-dessus")
        print("   Exemple: --category 'ORO.FTL' ou --category 'ORO.GEN'")
        return None
    
    # Initialiser le gestionnaire d'embeddings
    print(f"\n🔧 Initialisation du gestionnaire d'embeddings...")
    manager = EmbeddingsManager(db_path=db_path, model_name=model_name)
    
    # Extraire tous les paragraphes
    print(f"\n📦 Extraction des paragraphes...")
    paragraphs = []
    for item in tqdm(toc, desc="Extraction"):
        paragraph = parser.extract_paragraph(item['reference'])
        if paragraph:
            paragraphs.append(paragraph)
    
    print(f"✅ {len(paragraphs)} paragraphes extraits")
    
    # Ajouter à la base de données
    print(f"\n💾 Ajout à la base de données...")
    added = manager.add_paragraphs_batch(paragraphs, batch_size=batch_size)
    print(f"✅ {added} paragraphes ajoutés")
    
    # Afficher les statistiques
    print(f"\n📊 Statistiques:")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    
    print("\n" + "=" * 80)
    print("✅ BASE D'EMBEDDINGS CONSTRUITE AVEC SUCCÈS")
    print("=" * 80)
    
    return manager


if __name__ == "__main__":
    # Exemple d'utilisation
    XML_FILE = "Easy Access Rules for Air Operations - February 2025 - xml.xml"
    
    # Construire la base d'embeddings pour ORO.FTL
    manager = build_embeddings_database(
        xml_path=XML_FILE,
        db_path="easa_embeddings.db",
        pattern=r"ORO\.FTL\.[0-9]+",  # Seulement ORO.FTL pour commencer
        batch_size=32
    )
    
    # Tester une recherche
    print("\n🔍 Test de recherche:")
    results = manager.search("flight time limitations and rest requirements", top_k=3)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.reference} - {result.title}")
        print(f"   Score: {result.score:.3f}")
        print(f"   Extrait: {result.content[:100]}...")

