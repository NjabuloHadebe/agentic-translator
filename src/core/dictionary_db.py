# src/core/dictionary_db.py
import chromadb
from chromadb.config import Settings
import uuid
from typing import List, Dict, Optional
import os

class DictionaryDatabase:
    """Store dictionary terms in ChromaDB"""
    
    def __init__(self, persist_path: str = "./data/dictionary_db"):
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(persist_path), exist_ok=True)
        
        settings = Settings(anonymized_telemetry=False)
        
        self.client = chromadb.PersistentClient(
            path=persist_path,
            settings=settings
        )
        
        self.collection = self.client.get_or_create_collection(
            name="dictionary",
            metadata={"description": "English to isiZulu dictionary terms"}
        )
        
        # Initialize with your dictionary if empty
        if self.collection.count() == 0:
            self._initialize_with_your_data()
        else:
            print(f"📚 Dictionary loaded from {persist_path}")
    
    def _initialize_with_your_data(self):
        """Load your 274 terms from the hard-coded dictionary"""
        print("📚 Loading dictionary into ChromaDB...")
        
        # Copy ALL 274 terms from your original dictionary
        dictionary_terms = {
            # =============== ABBREVIATIONS & HONORIFICS ===============
            'dr': 'udkt',
            'dr.': 'udkt',
            'doctor': 'udokotela',
            'prof': 'uslz',
            'prof.': 'uslz',
            'professor': 'usolwazi',
            'mr': 'mnu',
            'mr.': 'mnu',
            'mister': 'mnumzane',
            'mrs': 'nkz',
            'mrs.': 'nkz',
            'miss': 'nkz',
            'ms': 'nkz',
            'ms.': 'nkz',
            
            # =============== TITLE ABBREVIATIONS ===============
            'dept': 'umnyango',
            'dept.': 'umnyango',
            'department': 'umnyango',
            'dir': 'umqondisi',
            'dir.': 'umqondisi',
            'director': 'umqondisi',
            'chair': 'usihlalo',
            'chairperson': 'usihlalo',
            'coord': 'umxhumanisi',
            'coord.': 'umxhumanisi',
            'coordinator': 'umxhumanisi',
            
            # =============== ORGANIZATION ABBREVIATIONS ===============
            'ukzn': 'i-ukzn',
            'ulpd': 'i-ulpd',
            'ulpdo': 'i-ulpdo',
            'kznplc': 'i-kznplc',
            'iso': 'i-iso',
            
            # =============== TIME ABBREVIATIONS ===============
            'h': 'h',
            'hr': 'ihora',
            'hrs': 'amahora',
            'hrs.': 'amahora',
            'min': 'imizuzu',
            'mins': 'imizuzu',
            'min.': 'imizuzu',
            'am': 'ekuseni',
            'pm': 'ntambama',
            
            # =============== PROGRAMME SPECIFIC ABBREVIATIONS ===============
            'q & a': 'imibuzo nezimpendulo',
            'q&a': 'imibuzo nezimpendulo',
            'registration and tea': 'ukubhalisa netiye',
            'comfort break': 'ikhefu lokuzelula',
            'closing remarks': 'amazwi okuvala',
            'vote of thanks': 'amazwi okubonga',
            'lunch and departure': 'isidlo sasemini nokugoduka',
            
            # =============== WORKSHOP & CONFERENCE TERMS ===============
            'workshop': 'inkuthazakwenza',
            'workshop on': 'inkuthazakwenza ye',
            'language standardisation': 'ukuvamisa ulimi',
            'standardisation': 'ukuvamisa',
            'language': 'ulimi',
            'date': 'mhla',
            'day': 'usuku',
            'time': 'isikhathi',
            'activity': 'okwenziwayo',
            'person responsible': 'umuntu okenzayo',
            'persons responsible': 'abantu abakenzayo',
            
            # =============== SCHEDULE & ACTIVITY TERMS ===============
            'registration': 'ukubhalisa',
            'tea': 'itiye',
            'opening remarks': 'amazwi okuvula',
            'welcome address': 'inkulumo yokwamukela',
            'introduction': 'ukwethulwa',
            'facilitators': 'abethulisifundo',
            'facilitator': 'mthulisifundo',
            'process': 'inqubo',
            'comfort break': 'ikhefu lokuzelula',
            'break': 'ikhefu',
            'lunch': 'isidlo sasemini',
            'lunch break': 'ikhefu lesidlo sasemini',
            'closing remarks': 'amazwi okuvala',
            'departure': 'ukugoduka',
            'departure and lunch': 'isidlo sasemini nokugoduka',
            
            # =============== MATERIALS DEVELOPMENT TERMS ===============
            'materials development': 'ukusungula nokuthuthukisa izinsizakufundisa',
            'materials': 'izinsizakufundisa',
            'development workshop': 'inkuthazakwenza yokuthuthukisa',
            'invigorating': 'ukuvuselela',
            'african languages': 'izilimi zase-afrika',
            'university glossaries': 'uhlumatemu lwezilimi emanyuvesi',
            'glossaries': 'uhlumatemu lwezilimi',
            'glossary': 'uhlumatelu lwolimi',
            'concept development': 'ukuthuthukiswa komqondomsuka',
            'concept': 'umqondomsuka',
            'concepts': 'imiqondomsuka',
            'ukzn specific': 'ezise-ukzn',
            'foundational concepts': 'imiqondomsuka eyisisekelo',
            'foundational': 'eyisisekelo',
            'series': 'uchungechunge',
            
            # =============== ACADEMIC CONTEXT TERMS ===============
            'select a discipline': 'sikhetha umkhakha',
            'discipline': 'umkhakha',
            'identify key foundational concepts': 'sihlonze imiqondomsuka ebalulekile neyisisekelo',
            'key concepts': 'imiqondomsuka ebalulekile',
            'year 1 undergraduate': 'bafundi abenza unyaka wokuqala enyuvesi',
            'undergraduate': 'bafundi benyuvesi',
            'year 1': 'unyaka wokuqala',
            'how to communicate': 'sixhumana kanjani',
            'communicate': 'sixhumana',
            'target audience': 'izethameli ezihlosiwe',
            'audience': 'izethameli',
            'target': 'ezihlosiwe',
            'convey concepts': 'ukuyidlulisela imiqondomsuka',
            'convey': 'ukudlulisela',
            'beyond terminology': 'asigcini ngokuqamba nje kuphela',
            'terminology': 'ukuqamba',
            'to communication': 'ekuxhumaneni',
            'communication': 'ukuxhumana',
            
            # =============== VISUAL DESIGN TERMS ===============
            'visual language': 'ulimi lohlelokuxhumana ngokwezimpawu',
            'visual': 'ngokwezimpawu',
            'instructional designer': 'umklami wezinsizakufundisa',
            'instructional design': 'ukuklama izinsizakufundisa',
            'graphic designer': 'umklamimidwebo',
            'graphic design': 'ukuklama imidwebo',
            'identify a visual language': 'ngokuhlonza ulimi lohlelokuxhumana ngokwezimpawu',
            'convey what we want': 'lwalokho esikulindele',
            'concept and the visual': 'umqondomsuka nezimpawu',
            'produce a basic example': 'sizokwenza isibonelo esisobala',
            'basic example': 'isibonelo esisobala',
            'visual and text': 'izimpawu nombhalo',
            'text': 'umbhalo',
            
            # =============== DAY 2 & PROCESS TERMS ===============
            'further development': 'ukuqhubeka nokuthuthukiswa',
            'further': 'ukuqhubeka',
            'review and reflection': 'ukubuyekeza nokuphawula ngomsebenzi owenziwe',
            'review': 'ukubuyekeza',
            'reflection': 'okuphawula ngomsebenzi owenziwe',
            'work done': 'ngomsebenzi owenziwe',
            
            # =============== LINGUISTICS & STANDARDIZATION ===============
            'standardisation process': 'inqubo yokuvamisa',
            'politics of standardisation': 'ipolitiki yohlelo lokuvamisa',
            'politics': 'ipolitiki',
            'iso standards': 'amaqophelomvama e-iso',
            'standards': 'amaqophelomvama',
            'terminology development': 'ukuqanjwa kwamatemu',
            'development': 'ukuqanjwa',
            'indigenous languages': 'izilimi zomdabu',
            'indigenous': 'zomdabu',
            'linguistic challenging': 'ucwaningozilimu luphosela inselelo',
            'linguistic': 'locwaningozilimu',
            'sociology of standards': 'isifundonhlalobantu ngokwamaqophelomvama',
            'sociology': 'isifundonhlalobantu',
            'best practices': 'izindlelanhle',
            'practices': 'izindlelanhle',
            'morpho-syntactic annotations': 'izingcaciso ngokwezakhiwomagama nangokohlelomisho',
            'morpho-syntactic': 'ngokwezakhiwomagama nangokohlelomisho',
            'annotations': 'izingcaciso',
            'example': 'isibonelo',
            'community of practice': 'ulusetshenziswayo',
            'dissemination': 'ukusatshalaliswa',
            'dissemination of terminology': 'ukusatshalaliswa kwamatemu',
            'linguistic works': 'imisebenzi yezocwaningozilimi',
            'works': 'imisebenzi',
            'questions and answers': 'imibuzo nezimpendulo',
            'questions': 'imibuzo',
            'answers': 'izimpendulo',
            'evaluation': 'uhlolobunjalo ngesifundo',
            
            # =============== UNIVERSITY & ORGANIZATION TERMS ===============
            'university': 'inyuvesi',
            'department chair': 'usekelasihlalo',
            'programme director': 'umphathi wohlelo',
            
            # =============== MEETING & CONFERENCE TERMS ===============
            'opening': 'ukuqala',
            'closing': 'ukuvala',
            'session': 'isifundo',
            'presentation': 'ukwethulwa',
            'discussion': 'ingxoxo',
            'panel': 'iphaneli',
            'keynote': 'inkulumo eqondisayo',
            'speaker': 'isikhulumi',
            'attendee': 'ozohambela',
            'participant': 'ozohlanganyela',
            'organizer': 'umhleli',
            
            # =============== TIME & DURATION TERMS ===============
            'minutes': 'imizuzu',
            'hours': 'amahora',
            'duration': 'ubude besikhathi',
            'schedule': 'uhlelo',
            'agenda': 'uhlelo',
            'programme': 'uhlelo',
            'timetable': 'uhlelo lwezikhathi',
            
            # =============== MONTHS ===============
            'december': 'zibandlela',
            'november': 'kulwezi',
            'february': 'kolandela',
            'thursday': 'ulwesine',
            'friday': 'ulwesihlanu',
            
            # =============== DOCUMENT & MATERIAL TERMS ===============
            'proceedings': 'izingcaciselo',
            'abstract': 'isifinyezo',
            'paper': 'iphepha',
            'publication': 'ukushicilelwa',
            'handbook': 'incwadi yesandla',
            'manual': 'incwadi yomsebenzi',
            'guide': 'isikhombisi',
            'template': 'isifanekiso',
            
            # =============== ACADEMIC ACTIVITIES ===============
            'research': 'ucwaningo',
            'study': 'isifundo',
            'analysis': 'uhlaziyo',
            'methodology': 'indlela yokusebenza',
            'framework': 'uhlaka',
            'model': 'imodeli',
            'theory': 'inkolelo-mqondo',
            'concept': 'umqondo',
            'definition': 'incazelo',
            'classification': 'ukuhlukanisa',
            'categorization': 'ukuhlukanisa ngezigaba',
            
            # =============== VERBS ===============
            'register': 'bhalisa',
            'open': 'vula',
            'welcome': 'wamukela',
            'introduce': 'ethula',
            'present': 'ethula',
            'facilitate': 'thulisa',
            'standardize': 'vamisa',
            'develop': 'qamba',
            'challenge': 'phonsela inselelo',
            'disseminate': 'satshalalisa',
            'evaluate': 'hlola',
            'thank': 'bonga',
            'close': 'vala',
            'depart': 'goduka',
            
            # =============== ACADEMIC QUALIFIERS ===============
            'academic': 'ezemfundo',
            'scientific': 'zesayensi',
            'technical': 'zobuchwepheshe',
            'professional': 'zobungcweti',
            'formal': 'ezisemthethweni',
            'informal': 'ezingezona ezisemthethweni',
            
            # =============== MEASUREMENT TERMS ===============
            'standard': 'evamile',
            'quality': 'ikhwalithi',
            'accuracy': 'ukunemba',
            'precision': 'ukunemba ngokweqile',
            'consistency': 'ukuqhubekela phambili',
            'reliability': 'ukwethembeka',
            'validity': 'ukuba semthethweni',
            
            # =============== CONFERENCE LOGISTICS ===============
            'venue': 'indawo',
            'location': 'indawo',
            'logistics': 'izinto zokuhlela',
            'accommodation': 'indawo yokuhlala',
            'transport': 'izinto zokuthutha',
            'catering': 'ukuletha ukudla',
            'equipment': 'izinto zokusebenza',
            
            # =============== ACADEMIC TITLES & ROLES ===============
            'secretary': 'unobhala',
            'treasurer': 'umphathi wezimali',
            'advisor': 'umeluleki',
            'consultant': 'umphenyi ngezeluleko',
            'expert': 'ingcweti',
            'specialist': 'ochwepheshe',
            
            # =============== NUMBERS ===============
            'first': 'loku-1',
            'second': 'lwesi-2',
            'one': 'loku-1',
            'two': 'lwesi-2',
            
            # =============== CONNECTORS & PREPOSITIONS ===============
            'all': 'sonke',
            'and': 'futhi',
            'or': 'noma',
            'but': 'kodwa',
            'with': 'nga',
            'without': 'ngaphandle kwa',
            'for': 'nge',
            'about': 'nga',
            'during': 'ngesikhathi',
            'after': 'ngemuva kwa',
            'before': 'ngaphambi kwa',
            'according to': 'ngokwe',
            'within the': 'ngaphakathi kwe',
            'for the': 'nge',
            'of the': 'ka',
            'in the': 'ku',
            'to the': 'uku',
            'and the': 'futhi',
            'with the': 'nga',
            
            # =============== NEW TERMS FROM YOUR TESTS ===============
            'vote of thanks & closing remarks': 'amazwi okubonga nokuvala',
            'vote of thanks and closing remarks': 'amazwi okubonga nokuvala',
            'vote of thanks': 'amazwi okubonga',
            'programme materials development workshop': 'inkuthazakwenza yokusungula nokuthuthukisa izinsizakufundisa zohlelo',
            'materials development workshop': 'inkuthazakwenza yokuthuthukisa izinsizakufundisa',
            'introduction of the facilitator': 'ukwethulwa komthulisifundo',
            'introduction of facilitator': 'ukwethulwa komthulisifundo',
            'facilitator introduction': 'ukwethulwa komthulisifundo',
            'developing a ukzn specific african language foundational concepts series': 'ukuthuthukisa uchungechunge lwemiqondomsuka eyisisekelo yezilimi zase-afrika ezise-ukzn',
            'welcome by': 'siyakwamukela nge',
            'dvc': 'idvc',
            'wrap-up': 'ukusongwa',
            'evaluation': 'ukuhlolwa',
            'workshop evaluation': 'ukuhlolwa kwenkuthazakwenza',
            'welcome by ukzn dvc': 'siyakwamukela ngedvc yase-ukzn',
            'evaluation of the workshop': 'ukuhlolwa kwenkuthazakwenza',
            'workshop wrap-up': 'ukusongwa kwenkuthazakwenza',
            'closing': 'ukuvala',
            'remarks': 'amazwi',
            'introductions': 'izethulo',
        }
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        for eng, zulu in dictionary_terms.items():
            ids.append(str(uuid.uuid4()))
            documents.append(eng.lower())  # Store lowercase for matching
            metadatas.append({
                "zulu": zulu,
                "english_original": eng  # Keep original for capitalization
            })
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✅ Loaded {len(dictionary_terms)} terms into dictionary database")
    
    def get_exact_match(self, text: str) -> Optional[str]:
        """Get exact dictionary match (case-insensitive)"""
        if not text or not isinstance(text, str):
            return None
        
        text_lower = text.lower().strip()
        
        # Clean variations
        variants = [
            text_lower,
            text_lower.replace('&', 'and'),
            text_lower.replace('&', ' and '),
            text_lower.replace('.', ''),  # Remove dots
            text_lower.replace('  ', ' '),  # Remove double spaces
        ]
        
        # Remove "the" from beginning
        for variant in variants[:]:  # Copy list before modifying
            if variant.startswith('the '):
                variants.append(variant[4:].strip())
        
        for variant in variants:
            # Try to find exact match in collection
            try:
                results = self.collection.get(
                    where={"english_original": variant},
                    limit=1
                )
                
                if results['metadatas'] and len(results['metadatas']) > 0:
                    zulu_translation = results['metadatas'][0]["zulu"]
                    
                    # Apply proper capitalization
                    if text.isupper():
                        zulu_translation = zulu_translation.upper()
                    elif text[0].isupper():
                        zulu_translation = zulu_translation[0].upper() + zulu_translation[1:]
                    
                    return zulu_translation
                    
            except Exception as e:
                print(f"⚠️  Error looking up '{variant}': {e}")
                continue
        
        return None
    
    def search_similar(self, query: str, threshold: float = 0.7) -> List[Dict]:
        """Find similar terms using semantic search"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=5,
                include=["metadatas", "distances"]
            )
            
            matches = []
            if results['metadatas'] and len(results['metadatas'][0]) > 0:
                for i, metadata in enumerate(results['metadatas'][0]):
                    distance = results['distances'][0][i] if i < len(results['distances'][0]) else 1.0
                    similarity = 1 - distance
                    
                    if similarity >= threshold:
                        matches.append({
                            "english": metadata["english_original"],
                            "zulu": metadata["zulu"],
                            "similarity": similarity
                        })
            
            return matches
        except Exception as e:
            print(f"⚠️  Error in semantic search: {e}")
            return []
    
    def add_term(self, english: str, zulu: str):
        """Add new term to dictionary"""
        try:
            self.collection.add(
                ids=[str(uuid.uuid4())],
                documents=[english.lower()],
                metadatas=[{
                    "zulu": zulu,
                    "english_original": english
                }]
            )
            print(f"✅ Added term: '{english}' → '{zulu}'")
        except Exception as e:
            print(f"❌ Error adding term: {e}")
    
    def get_stats(self) -> Dict:
        """Get dictionary statistics"""
        try:
            count = self.collection.count()
            return {
                "total_terms": count,
                "status": "loaded"
            }
        except Exception as e:
            return {
                "total_terms": 0,
                "status": f"error: {e}"
            }

# Test the dictionary
if __name__ == "__main__":
    print("🧪 Testing Dictionary Database...")
    
    db = DictionaryDatabase(persist_path="./data/dictionary_db")
    stats = db.get_stats()
    print(f"📊 Stats: {stats}")
    
    # Test some lookups
    test_terms = [
        "workshop",
        "Workshop",
        "WORKSHOP",
        "dr",
        "Dr.",
        "DR",
        "vote of thanks & closing remarks",
        "registration and tea",
        "closing remarks",
        "the workshop",  # Test with "the"
        "Q&A",
        "q & a",
    ]
    
    print("\n🔍 Testing dictionary lookups:")
    for term in test_terms:
        translation = db.get_exact_match(term)
        print(f"  '{term}' → '{translation}'")
    
    # Test semantic search
    print("\n🔍 Semantic search for 'meeting':")
    similar = db.search_similar("meeting", threshold=0.5)
    for match in similar:
        print(f"  {match['english']} → {match['zulu']} (similarity: {match['similarity']:.2f})")