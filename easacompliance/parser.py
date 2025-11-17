"""
EASA Parser v2 - Structure-based Parser

Ce parser utilise la structure hiérarchique officielle EASA du XML 
(document/toc/topic) au lieu de parser les paragraphes Word bruts.

Avantages:
- Accès à 3357 topics (vs ~400 paragraphes dans v1)
- Métadonnées complètes (TypeOfContent, dates, références réglementaires)
- Structure hiérarchique préservée
- Support natif des AMC, GM, CS, IR

Basé sur le schéma EASA eRules XML Export Schema 1.0.0
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from pathlib import Path
import re
from tqdm import tqdm


class TopicType(Enum):
    """Type de contenu réglementaire"""
    IR = "IR (Implementing rule);"  # Règles de mise en œuvre
    AMC = "AMC to IR (Acceptable means of compliance to implementing rule);"  # Moyens acceptables de conformité
    GM_IR = "GM to IR (Guidance material to implementing rule);"  # Matériel d'orientation
    CS = "CS (Certification specification);"  # Spécifications de certification
    GM_CS = "GM to CS (Guidance material to certification specification);"
    EASY_ACCESS = "Easy access rules;"
    OTHER = "Other"
    
    @classmethod
    def from_string(cls, value: str) -> 'TopicType':
        """Convertir une chaîne en TopicType"""
        for topic_type in cls:
            if topic_type.value == value:
                return topic_type
        return cls.OTHER


@dataclass
class Topic:
    """
    Représente un topic EASA (paragraphe réglementaire) avec ses métadonnées.
    
    Correspond à un élément <topic> dans la structure XML EASA.
    """
    # Identification
    reference: str  # Ex: "ORO.FTL.110"
    title: str  # Ex: "Operator responsibilities"
    erules_id: str  # Identifiant unique EASA
    sdt_id: str  # Référence vers le contenu dans document.xml
    
    # Contenu
    content: str = ""  # Texte complet du topic
    
    # Métadonnées réglementaires
    topic_type: TopicType = TopicType.OTHER
    domain: str = ""  # Ex: "Air operations"
    regulatory_subject: str = ""  # Ex: "Part-ORO"
    regulatory_source: str = ""  # Ex: "Regulation (EU) No 83/2014"
    
    # Dates
    applicability_date: str = ""
    entry_into_force_date: str = ""
    amended_by: str = ""
    
    # Autres métadonnées
    icao_reference: str = ""
    keywords: str = ""
    
    # Hiérarchie (pour usage futur si on veut reconstruire l'arbre)
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    
    def get_full_text(self) -> str:
        """Retourne le texte complet pour l'embedding"""
        parts = []
        
        # Référence et titre
        if self.reference:
            parts.append(f"{self.reference} {self.title}".strip())
        
        # Contenu
        if self.content:
            parts.append(self.content)
        
        # Contexte réglementaire (pour améliorer les embeddings)
        context_parts = []
        if self.regulatory_subject:
            context_parts.append(f"Subject: {self.regulatory_subject}")
        if self.domain:
            context_parts.append(f"Domain: {self.domain}")
        
        if context_parts:
            parts.append(" | ".join(context_parts))
        
        return "\n\n".join(parts)
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Retourne les métadonnées sous forme de dictionnaire"""
        return {
            'erules_id': self.erules_id,
            'sdt_id': self.sdt_id,
            'topic_type': self.topic_type.value,
            'domain': self.domain,
            'regulatory_subject': self.regulatory_subject,
            'regulatory_source': self.regulatory_source,
            'applicability_date': self.applicability_date,
            'entry_into_force_date': self.entry_into_force_date,
            'amended_by': self.amended_by,
            'icao_reference': self.icao_reference,
            'keywords': self.keywords,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le topic en dictionnaire pour export JSON"""
        return {
            "reference": self.reference,
            "title": self.title,
            "erules_id": self.erules_id,
            "sdt_id": self.sdt_id,
            "content": self.content,
            "topic_type": self.topic_type.value,
            "domain": self.domain,
            "regulatory_subject": self.regulatory_subject,
            "regulatory_source": self.regulatory_source,
            "applicability_date": self.applicability_date,
            "entry_into_force_date": self.entry_into_force_date,
            "amended_by": self.amended_by,
            "icao_reference": self.icao_reference,
            "keywords": self.keywords,
        }


class EASAParser:
    """
    Parser pour les documents EASA XML basé sur la structure officielle.
    
    Utilise la hiérarchie document/toc/topic du schéma EASA eRules XML Export.
    """
    
    # Namespaces XML
    NS_PKG = '{http://schemas.microsoft.com/office/2006/xmlPackage}'
    NS_ER = '{http://www.easa.europa.eu/erules-export}'
    NS_W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    
    # Pattern pour extraire la référence principale (ORO.FTL.110, CS-FTL.1, CS FTL.1.100, etc.)
    # Accepte espace, point ou tiret comme séparateur
    REF_PATTERN = re.compile(r'^([A-Z]{2,4}[\.\-\s][A-Z]{2,4}\.[0-9]+(?:\.[0-9]+)?)')
    
    def __init__(self, xml_path: str):
        """
        Initialise le parser.
        
        Args:
            xml_path: Chemin vers le fichier XML EASA
        """
        self.xml_path = Path(xml_path)
        if not self.xml_path.exists():
            raise FileNotFoundError(f"File not found: {xml_path}")
        
        print(f"📖 Chargement du document XML...")
        self.tree = ET.parse(str(self.xml_path))
        self.root = self.tree.getroot()
        
        # Caches pour performances
        self._toc_element = None
        self._document_element = None
        self._document_element_easa = None
        self._sdt_content_index: Dict[str, str] = {}  # sdt_id -> contenu texte
        
        # Extraire et cacher les éléments principaux
        self._extract_main_elements()
        
        # Indexer tous les SDT en une seule passe (optimisation cruciale)
        print(f"🔍 Indexation des contenus SDT...")
        self._build_sdt_index()
        
        print(f"✅ Parser initialisé (structure EASA v2) - {len(self._sdt_content_index)} contenus indexés")
    
    def _extract_main_elements(self):
        """Extrait et cache les éléments principaux du XML"""
        for part in self.root.findall(f'{self.NS_PKG}part'):
            name = part.get(f'{self.NS_PKG}name', '')
            xmldata = part.find(f'{self.NS_PKG}xmlData')
            
            if xmldata is None:
                continue
            
            # TOC (Table of Contents) - Structure EASA
            # Chercher dans tous les customXml/itemN.xml (le numéro varie selon le document)
            if '/customXml/item' in name and name.endswith('.xml'):
                doc = xmldata.find(f'{self.NS_ER}document')
                if doc is not None:
                    toc = doc.find(f'{self.NS_ER}toc')
                    if toc is not None:
                        self._toc_element = toc
                        self._document_element_easa = doc  # Garder aussi le document EASA
                        print(f"   📄 Document EASA trouvé dans: {name}")
            
            # Document principal Word
            elif '/word/document.xml' in name:
                self._document_element = xmldata
    
    def _build_sdt_index(self):
        """
        Construit un index de tous les SDT en une seule passe.
        
        Ceci est une optimisation cruciale : au lieu de faire 3357 recherches récursives
        (une par topic), on fait UNE seule passe pour indexer tous les SDT.
        
        Complexité : O(n) au lieu de O(n²)
        """
        if self._document_element is None:
            return
        
        def index_sdts_recursive(element):
            """Parcours récursif pour indexer tous les SDT"""
            for child in element:
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                
                if tag == 'sdt':
                    # Extraire l'ID
                    sdtpr = child.find(f'{self.NS_W}sdtPr')
                    if sdtpr is not None:
                        id_elem = sdtpr.find(f'{self.NS_W}id')
                        if id_elem is not None:
                            sdt_id = id_elem.get(f'{self.NS_W}val', '')
                            if sdt_id:
                                # Extraire et indexer le contenu
                                content = self._extract_text_from_sdt(child)
                                if content:
                                    self._sdt_content_index[sdt_id] = content
                
                # Récursion
                index_sdts_recursive(child)
        
        index_sdts_recursive(self._document_element)
    
    def _extract_reference_and_title(self, source_title: str) -> tuple[str, str]:
        """
        Extrait la référence et le titre d'un source-title.
        
        Gère plusieurs formats :
        - IR: "ORO.FTL.110 Operator responsibilities"
        - AMC: "AMC1 ORO.FTL.110 Operator responsibilities"
        - GM: "GM1 ORO.FTL.110(a) Operator responsibilities"
        - Article: "Article 2 - Definitions"
        
        Args:
            source_title: Le titre complet du topic
        
        Returns:
            (reference, title) tuple
        """
        if not source_title:
            return "", ""
        
        # Cas 1: Format AMC/GM (ex: "AMC1 ORO.FTL.110 Title")
        # Pattern: AMC[numéro] ou GM[numéro] suivi d'une référence
        amc_gm_pattern = re.compile(
            r'^((?:AMC|GM)\d+)\s+'  # AMC1 ou GM1 etc.
            r'([A-Z]{2,4}[\.\-\s][A-Z]{2,4}\.[0-9]+(?:\.[0-9]+)?(?:\([a-z0-9;]+\))?)'  # Référence avec possibilité de (a), (1), etc.
        )
        match = amc_gm_pattern.match(source_title)
        if match:
            prefix = match.group(1)  # AMC1, GM1, etc.
            ref = match.group(2)  # ORO.FTL.110(a)
            # La référence complète inclut le préfixe
            full_ref = f"{prefix} {ref}"
            title = source_title[len(full_ref):].strip()
            return full_ref, title
        
        # Cas 2: Format standard IR (ex: "ORO.FTL.110 Title")
        match = self.REF_PATTERN.match(source_title)
        if match:
            ref = match.group(1)
            title = source_title[len(ref):].strip()
            return ref, title
        
        # Cas 3: Format Article (ex: "AMC1 Article 2(1)(d) Definitions")
        # On garde le préfixe AMC/GM + Article comme référence
        article_pattern = re.compile(
            r'^((?:AMC|GM)\d+\s+Article\s+[\d\w\(\)\.\;]+)'  # AMC1 Article 2(1)(d)
        )
        match = article_pattern.match(source_title)
        if match:
            ref = match.group(1)
            title = source_title[len(ref):].strip()
            return ref, title
        
        # Cas 4: Article sans préfixe (ex: "Article 2 - Definitions")
        article_simple_pattern = re.compile(r'^(Article\s+[\d\w\.]+)')
        match = article_simple_pattern.match(source_title)
        if match:
            ref = match.group(1)
            title = source_title[len(ref):].strip()
            # Retirer le tiret initial du titre si présent
            title = title.lstrip('- ')
            return ref, title
        
        # Cas 5: Aucun pattern ne correspond
        return "", source_title
    
    def _find_sdt_content(self, sdt_id: str) -> str:
        """
        Trouve et extrait le contenu d'un SDT (Structured Document Tag) par son ID.
        
        OPTIMISÉ : Lookup O(1) dans l'index pré-construit au lieu de recherche récursive.
        
        Args:
            sdt_id: L'identifiant du SDT
        
        Returns:
            Le texte complet du SDT
        """
        return self._sdt_content_index.get(sdt_id, "")
    
    def _extract_text_from_sdt(self, sdt_element: ET.Element) -> str:
        """
        Extrait le texte d'un élément SDT.
        
        Args:
            sdt_element: L'élément XML SDT
        
        Returns:
            Le texte complet
        """
        sdtcontent = sdt_element.find(f'{self.NS_W}sdtContent')
        if sdtcontent is None:
            return ""
        
        # Extraire tout le texte des paragraphes
        paragraphs = []
        for p in sdtcontent.findall(f'.//{self.NS_W}p'):
            texts = p.findall(f'.//{self.NS_W}t')
            para_text = ''.join([t.text or '' for t in texts])
            if para_text.strip():
                paragraphs.append(para_text.strip())
        
        return "\n".join(paragraphs)
    
    def _parse_topic_element(self, topic_element: ET.Element) -> Topic:
        """
        Parse un élément <topic> XML en objet Topic.
        
        Args:
            topic_element: L'élément XML <topic>
        
        Returns:
            Un objet Topic
        """
        # Extraire les attributs
        source_title = topic_element.get('source-title', '')
        reference, title = self._extract_reference_and_title(source_title)
        
        erules_id = topic_element.get('ERulesId', '')
        sdt_id = topic_element.get('sdt-id', '')
        
        # Type de contenu
        topic_type_str = topic_element.get('TypeOfContent', '')
        topic_type = TopicType.from_string(topic_type_str)
        
        # Métadonnées
        domain = topic_element.get('Domain', '')
        regulatory_subject = topic_element.get('RegulatorySubject', '')
        regulatory_source = topic_element.get('RegulatorySource', '')
        
        applicability_date = topic_element.get('ApplicabilityDate', '')
        entry_into_force_date = topic_element.get('EntryIntoForceDate', '')
        amended_by = topic_element.get('AmendedBy', '')
        
        icao_reference = topic_element.get('ICAOReference', '')
        keywords = topic_element.get('Keywords', '')
        
        # Extraire le contenu via sdt-id
        content = ""
        if sdt_id:
            content = self._find_sdt_content(sdt_id)
        
        return Topic(
            reference=reference,
            title=title,
            erules_id=erules_id,
            sdt_id=sdt_id,
            content=content,
            topic_type=topic_type,
            domain=domain,
            regulatory_subject=regulatory_subject,
            regulatory_source=regulatory_source,
            applicability_date=applicability_date,
            entry_into_force_date=entry_into_force_date,
            amended_by=amended_by,
            icao_reference=icao_reference,
            keywords=keywords,
        )
    
    def get_all_topics(self, 
                       pattern: Optional[str] = None,
                       topic_type_filter: Optional[List[TopicType]] = None,
                       regulatory_subject_filter: Optional[str] = None,
                       show_progress: bool = False) -> List[Topic]:
        """
        Récupère tous les topics du document.
        
        Args:
            pattern: Regex pour filtrer par référence (ex: r'ORO\\.FTL\\.')
            topic_type_filter: Liste de types à inclure (ex: [TopicType.IR])
            regulatory_subject_filter: Filtre par sujet (ex: "Part-ORO")
            show_progress: Afficher une barre de progression
        
        Returns:
            Liste de topics
        """
        if self._toc_element is None:
            return []
        
        topics = []
        regex_pattern = re.compile(pattern) if pattern else None
        
        # Compter d'abord le nombre total d'éléments pour la barre de progression
        def count_elements(element):
            count = 1
            for child in element:
                count += count_elements(child)
            return count
        
        total_elements = count_elements(self._toc_element) if show_progress else 0
        pbar = tqdm(total=total_elements, desc="Extraction des topics", disable=not show_progress)
        
        def collect_topics(element):
            """Collecte récursive des topics"""
            if show_progress:
                pbar.update(1)
            
            tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
            
            if tag == 'topic':
                topic = self._parse_topic_element(element)
                
                # Appliquer les filtres
                if regex_pattern and not regex_pattern.match(topic.reference):
                    pass  # Skip
                elif topic_type_filter and topic.topic_type not in topic_type_filter:
                    pass  # Skip
                elif regulatory_subject_filter and regulatory_subject_filter not in topic.regulatory_subject:
                    pass  # Skip
                else:
                    topics.append(topic)
            
            # Récursion
            for child in element:
                collect_topics(child)
        
        collect_topics(self._toc_element)
        
        if show_progress:
            pbar.close()
        
        return topics
    
    def get_topic_by_reference(self, reference: str) -> Optional[Topic]:
        """
        Récupère un topic par sa référence exacte.
        
        Args:
            reference: Ex: "ORO.FTL.110"
        
        Returns:
            Le topic ou None si non trouvé
        """
        if self._toc_element is None:
            return None
        
        def find_topic(element) -> Optional[ET.Element]:
            """Recherche récursive du topic"""
            tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
            
            if tag == 'topic':
                source_title = element.get('source-title', '')
                ref, _ = self._extract_reference_and_title(source_title)
                if ref == reference:
                    return element
            
            for child in element:
                result = find_topic(child)
                if result is not None:
                    return result
            
            return None
        
        topic_element = find_topic(self._toc_element)
        if topic_element is not None:
            return self._parse_topic_element(topic_element)
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur le document.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        all_topics = self.get_all_topics()
        
        # Compter par type
        type_counts = {}
        for topic in all_topics:
            type_key = topic.topic_type.value
            type_counts[type_key] = type_counts.get(type_key, 0) + 1
        
        # Compter par sujet réglementaire
        subject_counts = {}
        for topic in all_topics:
            subject = topic.regulatory_subject or "Unknown"
            subject_counts[subject] = subject_counts.get(subject, 0) + 1
        
        # Compter par catégorie (première partie de la référence)
        category_counts = {}
        for topic in all_topics:
            if topic.reference:
                # Extraire catégorie (ex: "ORO.FTL" de "ORO.FTL.110")
                parts = topic.reference.split('.')
                if len(parts) >= 2:
                    category = f"{parts[0]}.{parts[1]}"
                    category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_topics": len(all_topics),
            "by_type": type_counts,
            "by_subject": subject_counts,
            "by_category": dict(sorted(category_counts.items(), key=lambda x: -x[1])[:20]),
        }


if __name__ == "__main__":
    # Test du parser
    parser = EASAParserV2("Easy Access Rules for Air Operations - February 2025 - xml.xml")
    
    print("\n" + "="*80)
    print("📊 STATISTIQUES DU DOCUMENT")
    print("="*80 + "\n")
    
    stats = parser.get_statistics()
    print(f"Total topics: {stats['total_topics']}")
    
    print("\nRépartition par type:")
    for topic_type, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
        print(f"  • {topic_type}: {count}")
    
    print("\nTop 10 catégories:")
    for category, count in list(stats['by_category'].items())[:10]:
        print(f"  • {category}: {count}")
    
    print("\n" + "="*80)
    print("🔍 TEST: Extraction de ORO.FTL.110")
    print("="*80 + "\n")
    
    topic = parser.get_topic_by_reference("ORO.FTL.110")
    if topic:
        print(f"Référence: {topic.reference}")
        print(f"Titre: {topic.title}")
        print(f"Type: {topic.topic_type.value}")
        print(f"Domaine: {topic.domain}")
        print(f"Sujet: {topic.regulatory_subject}")
        print(f"Source: {topic.regulatory_source}")
        print(f"Date d'applicabilité: {topic.applicability_date}")
        print(f"\nContenu ({len(topic.content)} caractères):")
        print(topic.content[:500] + "..." if len(topic.content) > 500 else topic.content)
    else:
        print("❌ Topic non trouvé")
    
    print("\n" + "="*80)
    print("🔍 TEST: Recherche de tous les CS FTL")
    print("="*80 + "\n")
    
    cs_ftl_topics = parser.get_all_topics(pattern=r'^CS FTL\.')
    print(f"Nombre de topics CS FTL trouvés: {len(cs_ftl_topics)}")
    
    for topic in cs_ftl_topics[:5]:
        print(f"  • {topic.reference} {topic.title}")
        print(f"    Type: {topic.topic_type.value}")

