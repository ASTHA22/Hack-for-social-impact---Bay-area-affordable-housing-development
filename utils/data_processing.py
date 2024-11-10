import pandas as pd

def process_code_differences(codes_data):
    """Process and highlight differences between building codes"""
    df = pd.DataFrame(codes_data)
    
    differences = []
    categories = df['category'].unique()
    
    for category in categories:
        category_codes = df[df['category'] == category]
        jurisdictions = category_codes['jurisdiction'].unique()
        
        for section in category_codes['section'].unique():
            section_codes = category_codes[category_codes['section'] == section]
            if len(section_codes) > 1 and not all(section_codes['content'].iloc[0] == section_codes['content']):
                differences.append({
                    'category': category,
                    'section': section,
                    'jurisdictions': list(jurisdictions),
                    'severity': 'high' if len(set(section_codes['content'])) > 2 else 'medium'
                })
    
    return differences
