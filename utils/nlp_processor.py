import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class BuildingCodeNLP:
    def __init__(self):
        self.stop_words = set(['a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it',
                             'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with'])
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
        # Technical terms dictionary
        self.technical_terms = {
            'structural': [
                'load', 'bearing', 'foundation', 'frame', 'steel', 'concrete',
                'beam', 'column', 'joist', 'truss', 'seismic', 'shear', 'lateral'
            ],
            'electrical': [
                'voltage', 'circuit', 'wiring', 'conduit', 'grounding',
                'breaker', 'panel', 'lighting', 'power'
            ],
            'plumbing': [
                'pipe', 'drainage', 'vent', 'fixture', 'water',
                'valve', 'pressure', 'supply', 'waste'
            ]
        }
        
        # Patterns for measurements, requirements, and references
        self.measurement_patterns = [
            r'\d+(?:\.\d+)?\s*(?:feet|foot|ft|inches|inch|in|meters|m)',
            r'\d+(?:\.\d+)?\s*(?:square\s+feet|sq\s+ft|sf)',
            r'\d+(?:\.\d+)?\s*%'
        ]
        
        self.requirement_patterns = {
            'mandatory': r'\b(?:shall|must|required)\b',
            'recommended': r'\b(?:should|recommended)\b',
            'prohibited': r'\b(?:shall not|must not|prohibited)\b',
            'optional': r'\b(?:may|optional|permitted)\b'
        }

        self.reference_patterns = {
            'section': r'\b(?:section|sect\.)\s+\d+(?:\.\d+)*\b',
            'code': r'\b(?:code|standard|regulation)\s+[\w\d\.-]+\b',
            'external': r'\b(?:ASTM|IBC|NFPA|ANSI|IEEE)\s+[\w\d\.-]+\b'
        }

    def preprocess_text(self, text):
        """Simple text preprocessing without NLTK"""
        # Convert to lowercase
        text = text.lower()
        # Split into sentences using basic punctuation
        sentences = re.split('[.!?]+', text)
        # Remove empty sentences and extra whitespace
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def calculate_similarity(self, text1, text2):
        """Calculate similarity between two texts"""
        try:
            # Preprocess texts
            proc_text1 = ' '.join(self.preprocess_text(text1))
            proc_text2 = ' '.join(self.preprocess_text(text2))
            
            # Calculate TF-IDF similarity
            tfidf_matrix = self.vectorizer.fit_transform([proc_text1, proc_text2])
            return float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        except Exception as e:
            print(f"Error in similarity calculation: {e}")
            return 0.5  # Return moderate similarity on error

    def extract_entities(self, text):
        """Extract entities from text"""
        text = text.lower()
        sentences = self.preprocess_text(text)
        entities = {
            'measurements': [],
            'requirements': [],
            'technical_terms': [],
            'references': []
        }
        
        # Extract measurements
        for pattern in self.measurement_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities['measurements'].append({
                    'value': match.group(),
                    'type': 'measurement'
                })
        
        # Extract requirements
        for req_type, pattern in self.requirement_patterns.items():
            for sentence in sentences:
                if re.search(pattern, sentence):
                    entities['requirements'].append({
                        'text': sentence,
                        'type': req_type
                    })
        
        # Extract references
        for ref_type, pattern in self.reference_patterns.items():
            for sentence in sentences:
                matches = re.finditer(pattern, sentence)
                for match in matches:
                    entities['references'].append({
                        'text': sentence,
                        'type': ref_type
                    })
        
        # Extract technical terms
        for category, terms in self.technical_terms.items():
            found_terms = []
            for term in terms:
                if term in text:
                    found_terms.append(term)
            if found_terms:
                entities['technical_terms'].append({
                    'category': category,
                    'terms': found_terms
                })
        
        return entities

def analyze_code_differences(code1, code2):
    """Analyze differences between code sections"""
    try:
        nlp = BuildingCodeNLP()
        
        similarity = nlp.calculate_similarity(code1, code2)
        entities1 = nlp.extract_entities(code1)
        entities2 = nlp.extract_entities(code2)
        
        # Find changes in requirements
        req_changes = {
            'added': [],
            'removed': [],
            'modified': []
        }
        
        # Compare requirements
        for req2 in entities2['requirements']:
            if not any(nlp.calculate_similarity(req2['text'], req1['text']) > 0.8 
                      for req1 in entities1['requirements']):
                req_changes['added'].append(req2)
        
        for req1 in entities1['requirements']:
            if not any(nlp.calculate_similarity(req1['text'], req2['text']) > 0.8 
                      for req2 in entities2['requirements']):
                req_changes['removed'].append(req1)
        
        return {
            'similarity_score': similarity,
            'entities_code1': entities1,
            'entities_code2': entities2,
            'requirement_changes': req_changes
        }
    except Exception as e:
        print(f"Error in code difference analysis: {e}")
        return {
            'similarity_score': 0.5,
            'entities_code1': {'measurements': [], 'requirements': [], 'technical_terms': [], 'references': []},
            'entities_code2': {'measurements': [], 'requirements': [], 'technical_terms': [], 'references': []},
            'requirement_changes': {'added': [], 'removed': [], 'modified': []}
        }
