import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from urllib.parse import urljoin, urlparse
import zipfile
import tempfile
from collections import defaultdict
import re

class XBRLTaxonomyParser:
    def __init__(self, base_url="https://xbrl.fasb.org/us-gaap/2025/"):
        self.base_url = base_url
        self.elements = {}
        self.labels = {}
        self.references = {}
        self.presentation_relationships = defaultdict(list)
        self.calculation_relationships = defaultdict(list)
        self.definition_relationships = defaultdict(list)
        self.namespaces = {
            'xs': 'http://www.w3.org/2001/XMLSchema',
            'xsd': 'http://www.w3.org/2001/XMLSchema',
            'link': 'http://www.xbrl.org/2003/linkbase',
            'xlink': 'http://www.w3.org/1999/xlink',
            'xbrldt': 'http://xbrl.org/2005/xbrldt',
            'us-gaap': 'http://fasb.org/us-gaap/2025'
        }
    
    def download_file(self, url):
        """Download a file and return its content"""
        print(f"📥 Downloading: {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"❌ Error downloading {url}: {e}")
            return None
    
    def parse_schema_file(self, content):
        """Parse the main XSD schema file to extract ALL element details"""
        try:
            root = ET.fromstring(content)
            
            # Find all element definitions
            for element in root.findall('.//xs:element', self.namespaces):
                name = element.get('name')
                if name:
                    elem_info = {
                        'name': name,
                        'data_type': element.get('type', ''),
                        'xbrl_type': '',
                        'substitution_group': element.get('substitutionGroup', ''),
                        'abstract': element.get('abstract', 'false'),
                        'nillable': element.get('nillable', 'false'),
                        'period_type': '',
                        'balance': '',
                        'namespace': '',
                        'id': element.get('id', ''),
                        'labels': {},
                        'references': [],
                        'parent_elements': [],
                        'child_elements': [],
                        'calculation_children': [],
                        'definition_children': []
                    }
                    
                    # Extract namespace from type if available
                    elem_type = element.get('type', '')
                    if ':' in elem_type:
                        namespace_prefix = elem_type.split(':')[0]
                        elem_info['namespace'] = self.get_namespace_uri(root, namespace_prefix)
                    
                    # Look for XBRL-specific attributes in annotations
                    annotation = element.find('xs:annotation', self.namespaces)
                    if annotation is not None:
                        appinfo = annotation.find('xs:appinfo', self.namespaces)
                        if appinfo is not None:
                            for child in appinfo:
                                tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                                if tag_name == 'periodType':
                                    elem_info['period_type'] = child.text
                                elif tag_name == 'balance':
                                    elem_info['balance'] = child.text
                                elif 'Type' in tag_name:
                                    elem_info['xbrl_type'] = child.text
                    
                    self.elements[name] = elem_info
                    
        except Exception as e:
            print(f"❌ Error parsing schema: {e}")
    
    def get_namespace_uri(self, root, prefix):
        """Get the full namespace URI for a given prefix"""
        for attr_name, attr_value in root.attrib.items():
            if attr_name == f'xmlns:{prefix}':
                return attr_value
        return ''
    
    def parse_label_linkbase(self, content):
        """Parse label linkbase to get ALL types of labels"""
        try:
            root = ET.fromstring(content)
            
            # First pass: collect all labels
            for label in root.findall('.//link:label', self.namespaces):
                label_text = label.text
                if label_text:
                    role = label.get('{http://www.w3.org/1999/xlink}role', '')
                    
                    # Determine label type from role
                    label_type = 'standard'
                    if 'terseLabel' in role:
                        label_type = 'terse'
                    elif 'verboseLabel' in role:
                        label_type = 'verbose'
                    elif 'documentation' in role:
                        label_type = 'documentation'
                    elif 'totalLabel' in role:
                        label_type = 'total'
                    elif 'negatedLabel' in role:
                        label_type = 'negated'
                    
                    label_id = label.get('{http://www.w3.org/1999/xlink}label', '')
                    if label_id:
                        self.labels[label_id] = {
                            'text': label_text.strip(),
                            'type': label_type,
                            'lang': label.get('{http://www.w3.org/XML/1998/namespace}lang', 'en-US'),
                            'role': role
                        }
            
            # Second pass: link labels to elements
            element_to_labels = defaultdict(dict)
            
            for arc in root.findall('.//link:labelArc', self.namespaces):
                from_ref = arc.get('{http://www.w3.org/1999/xlink}from', '')
                to_ref = arc.get('{http://www.w3.org/1999/xlink}to', '')
                
                if from_ref and to_ref and to_ref in self.labels:
                    # Find the element this refers to
                    for loc in root.findall('.//link:loc', self.namespaces):
                        if loc.get('{http://www.w3.org/1999/xlink}label', '') == from_ref:
                            href = loc.get('{http://www.w3.org/1999/xlink}href', '')
                            if '#' in href:
                                element_name = href.split('#')[-1]
                                if element_name in self.elements:
                                    label_info = self.labels[to_ref]
                                    self.elements[element_name]['labels'][label_info['type']] = label_info['text']
                                    
        except Exception as e:
            print(f"❌ Error parsing label linkbase: {e}")
    
    def parse_reference_linkbase(self, content):
        """Parse reference linkbase to get ALL authoritative references"""
        try:
            root = ET.fromstring(content)
            
            # Collect all references
            for ref in root.findall('.//link:reference', self.namespaces):
                ref_id = ref.get('{http://www.w3.org/1999/xlink}label', '')
                if ref_id:
                    ref_info = {}
                    
                    # Extract ALL reference details
                    for child in ref:
                        tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                        if child.text:
                            ref_info[tag_name] = child.text.strip()
                    
                    self.references[ref_id] = ref_info
            
            # Link references to elements
            for arc in root.findall('.//link:referenceArc', self.namespaces):
                from_ref = arc.get('{http://www.w3.org/1999/xlink}from', '')
                to_ref = arc.get('{http://www.w3.org/1999/xlink}to', '')
                
                if from_ref and to_ref and to_ref in self.references:
                    for loc in root.findall('.//link:loc', self.namespaces):
                        if loc.get('{http://www.w3.org/1999/xlink}label', '') == from_ref:
                            href = loc.get('{http://www.w3.org/1999/xlink}href', '')
                            if '#' in href:
                                element_name = href.split('#')[-1]
                                if element_name in self.elements:
                                    self.elements[element_name]['references'].append(self.references[to_ref])
                                    
        except Exception as e:
            print(f"❌ Error parsing reference linkbase: {e}")
    
    def parse_presentation_linkbase(self, content):
        """Parse presentation linkbase to build the hierarchical structure"""
        try:
            root = ET.fromstring(content)
            
            # Build location map for href -> element name
            href_to_element = {}
            for loc in root.findall('.//link:loc', self.namespaces):
                label = loc.get('{http://www.w3.org/1999/xlink}label', '')
                href = loc.get('{http://www.w3.org/1999/xlink}href', '')
                if label and href and '#' in href:
                    element_name = href.split('#')[-1]
                    href_to_element[label] = element_name
            
            # Parse presentation arcs to build hierarchy
            for arc in root.findall('.//link:presentationArc', self.namespaces):
                from_ref = arc.get('{http://www.w3.org/1999/xlink}from', '')
                to_ref = arc.get('{http://www.w3.org/1999/xlink}to', '')
                order = float(arc.get('order', '0'))
                
                if from_ref in href_to_element and to_ref in href_to_element:
                    parent_element = href_to_element[from_ref]
                    child_element = href_to_element[to_ref]
                    
                    # Store the relationship
                    self.presentation_relationships[parent_element].append({
                        'child': child_element,
                        'order': order,
                        'preferred_label': arc.get('preferredLabel', '')
                    })
                    
                    # Update elements with hierarchy info
                    if parent_element in self.elements:
                        if child_element not in self.elements[parent_element]['child_elements']:
                            self.elements[parent_element]['child_elements'].append(child_element)
                    
                    if child_element in self.elements:
                        if parent_element not in self.elements[child_element]['parent_elements']:
                            self.elements[child_element]['parent_elements'].append(parent_element)
                            
        except Exception as e:
            print(f"❌ Error parsing presentation linkbase: {e}")
    
    def parse_calculation_linkbase(self, content):
        """Parse calculation linkbase to understand calculation relationships"""
        try:
            root = ET.fromstring(content)
            
            # Build location map
            href_to_element = {}
            for loc in root.findall('.//link:loc', self.namespaces):
                label = loc.get('{http://www.w3.org/1999/xlink}label', '')
                href = loc.get('{http://www.w3.org/1999/xlink}href', '')
                if label and href and '#' in href:
                    element_name = href.split('#')[-1]
                    href_to_element[label] = element_name
            
            # Parse calculation arcs
            for arc in root.findall('.//link:calculationArc', self.namespaces):
                from_ref = arc.get('{http://www.w3.org/1999/xlink}from', '')
                to_ref = arc.get('{http://www.w3.org/1999/xlink}to', '')
                weight = float(arc.get('weight', '1'))
                order = float(arc.get('order', '0'))
                
                if from_ref in href_to_element and to_ref in href_to_element:
                    parent_element = href_to_element[from_ref]
                    child_element = href_to_element[to_ref]
                    
                    self.calculation_relationships[parent_element].append({
                        'child': child_element,
                        'weight': weight,
                        'order': order
                    })
                    
                    # Update elements
                    if parent_element in self.elements:
                        self.elements[parent_element]['calculation_children'].append({
                            'element': child_element,
                            'weight': weight
                        })
                        
        except Exception as e:
            print(f"❌ Error parsing calculation linkbase: {e}")
    
    def parse_taxonomy(self):
        """Main method to parse the ENTIRE taxonomy with ALL relationships"""
        print("🚀 Starting comprehensive XBRL taxonomy parsing...")
        
        # Step 1: Download and parse the main schema file
        schema_url = urljoin(self.base_url, "elts/us-gaap-2025.xsd")
        schema_content = self.download_file(schema_url)
        if schema_content:
            self.parse_schema_file(schema_content)
            print(f"✅ Parsed {len(self.elements)} elements from schema")
        
        # Step 2: Parse label linkbases (try different naming patterns)
        label_files = [
            "elts/us-gaap-lab-2025.xml",
            "elts/us-gaap-lab-def-2025.xml",
            "elts/us-gaap-2025-lab.xml",
            "elts/us-gaap-2025-lab-def.xml"
        ]
        
        labels_found = 0
        for label_file in label_files:
            label_url = urljoin(self.base_url, label_file)
            label_content = self.download_file(label_url)
            if label_content:
                self.parse_label_linkbase(label_content)
                labels_found += 1
        
        print(f"✅ Processed labels from {labels_found} files")
        
        # Step 3: Parse reference linkbases (try different naming patterns)
        ref_files = [
            "elts/us-gaap-ref-2025.xml",
            "elts/us-gaap-ref-def-2025.xml",
            "elts/us-gaap-2025-ref.xml",
            "elts/us-gaap-2025-ref-def.xml"
        ]
        
        refs_found = 0
        for ref_file in ref_files:
            ref_url = urljoin(self.base_url, ref_file)
            ref_content = self.download_file(ref_url)
            if ref_content:
                self.parse_reference_linkbase(ref_content)
                refs_found += 1
        
        print(f"✅ Processed references from {refs_found} files")
        
        # Step 4: Parse presentation linkbases (try different naming patterns)
        pres_files = [
            "elts/us-gaap-pre-2025.xml",
            "elts/us-gaap-pre-def-2025.xml", 
            "elts/us-gaap-2025-pre.xml",
            "elts/us-gaap-2025-pre-def.xml",
            "stm/us-gaap-stm-pre-2025.xml",
            "dis/us-gaap-dis-pre-2025.xml"
        ]
        
        pres_found = 0
        for pres_file in pres_files:
            pres_url = urljoin(self.base_url, pres_file)
            pres_content = self.download_file(pres_url)
            if pres_content:
                self.parse_presentation_linkbase(pres_content)
                pres_found += 1
        
        print(f"✅ Built presentation hierarchy from {pres_found} files")
        
        # Step 5: Parse calculation linkbases (try different naming patterns)
        calc_files = [
            "elts/us-gaap-cal-2025.xml", 
            "elts/us-gaap-cal-def-2025.xml",
            "elts/us-gaap-2025-cal.xml",
            "elts/us-gaap-2025-cal-def.xml",
            "stm/us-gaap-stm-cal-2025.xml",
            "dis/us-gaap-dis-cal-2025.xml"
        ]
        
        calc_found = 0
        for calc_file in calc_files:
            calc_url = urljoin(self.base_url, calc_file)
            calc_content = self.download_file(calc_url)
            if calc_content:
                self.parse_calculation_linkbase(calc_content)
                calc_found += 1
        
        print(f"✅ Built calculation relationships from {calc_found} files")
        print("🎉 Comprehensive taxonomy parsing complete!")
        
        # Step 6: Classify elements by financial statement
        self.classify_all_elements()
    
    def to_comprehensive_dataframe(self):
        """Convert ALL parsed data to a comprehensive pandas DataFrame"""
        rows = []
        
        for element_name, element_info in self.elements.items():
            # Build calculation formula
            calc_formula = ""
            if element_info['calculation_children']:
                calc_parts = []
                for calc_child in element_info['calculation_children']:
                    weight = calc_child['weight']
                    child_name = calc_child['element']
                    sign = "+" if weight >= 0 else "-"
                    calc_parts.append(f"{sign} {child_name}")
                calc_formula = " ".join(calc_parts)
            
            # Get all reference info as JSON-like string
            ref_info = ""
            if element_info['references']:
                ref_parts = []
                for ref in element_info['references']:
                    ref_str = "; ".join([f"{k}: {v}" for k, v in ref.items()])
                    ref_parts.append(ref_str)
                ref_info = " | ".join(ref_parts)
            
            row = {
                'element_name': element_name,
                'id': element_info.get('id', ''),
                'namespace': element_info.get('namespace', ''),
                'data_type': element_info.get('data_type', ''),
                'xbrl_type': element_info.get('xbrl_type', ''),
                'substitution_group': element_info.get('substitution_group', ''),
                'abstract': element_info.get('abstract', 'false'),
                'nillable': element_info.get('nillable', 'false'),
                'period_type': element_info.get('period_type', ''),
                'balance': element_info.get('balance', ''),
                
                # Labels
                'standard_label': element_info['labels'].get('standard', ''),
                'terse_label': element_info['labels'].get('terse', ''),
                'verbose_label': element_info['labels'].get('verbose', ''),
                'documentation': element_info['labels'].get('documentation', ''),
                'total_label': element_info['labels'].get('total', ''),
                
                # Hierarchy
                'parent_elements': "; ".join(element_info.get('parent_elements', [])),
                'child_elements': "; ".join(element_info.get('child_elements', [])),
                'has_children': len(element_info.get('child_elements', [])) > 0,
                'is_root': len(element_info.get('parent_elements', [])) == 0,
                'financial_statement': element_info.get('financial_statement', 'Unknown'),
                
                # Calculations
                'calculation_formula': calc_formula,
                'calculation_children_count': len(element_info.get('calculation_children', [])),
                
                # References
                'authoritative_references': ref_info,
                'reference_count': len(element_info.get('references', []))
            }
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def save_comprehensive_csv(self, filename="us_gaap_comprehensive.csv"):
        """Save the complete taxonomy with ALL details to CSV"""
        df = self.to_comprehensive_dataframe()
        df.to_csv(filename, index=False)
        print(f"💾 Saved {len(df)} elements with full details to {filename}")
        
        # Create a hierarchy CSV too
        hierarchy_df = self.build_hierarchy_dataframe()
        hierarchy_filename = filename.replace('.csv', '_hierarchy.csv')
        hierarchy_df.to_csv(hierarchy_filename, index=False)
        print(f"📊 Saved hierarchy structure to {hierarchy_filename}")
        
        return df, hierarchy_df
    
    def build_hierarchy_dataframe(self):
        """Build a separate DataFrame showing the hierarchical relationships"""
        hierarchy_rows = []
        
        for parent, children in self.presentation_relationships.items():
            for child_info in children:
                child = child_info['child']
                hierarchy_rows.append({
                    'parent_element': parent,
                    'child_element': child,
                    'order': child_info['order'],
                    'preferred_label': child_info.get('preferred_label', ''),
                    'parent_label': self.elements.get(parent, {}).get('labels', {}).get('standard', ''),
                    'child_label': self.elements.get(child, {}).get('labels', {}).get('standard', ''),
                    'level': self.calculate_element_level(child)
                })
        
        return pd.DataFrame(hierarchy_rows)
    
    def calculate_element_level(self, element_name, visited=None):
        """Calculate how deep an element is in the hierarchy"""
        if visited is None:
            visited = set()
        
        if element_name in visited:
            return 0  # Circular reference protection
        
        visited.add(element_name)
        
        if element_name not in self.elements:
            return 0
        
        parents = self.elements[element_name].get('parent_elements', [])
        if not parents:
            return 0  # Root level
        
        max_parent_level = 0
        for parent in parents:
            parent_level = self.calculate_element_level(parent, visited.copy())
            max_parent_level = max(max_parent_level, parent_level)
        
        return max_parent_level + 1
    
    def find_top_level_statement(self, element_name, visited=None):
        """Find which top-level financial statement this element belongs to"""
        if visited is None:
            visited = set()
        
        if element_name in visited:
            return "Unknown"  # Circular reference protection
        
        visited.add(element_name)
        
        if element_name not in self.elements:
            return "Unknown"
        
        # Define statement patterns to look for
        statement_patterns = {
            'Statement of Financial Position': [
                'StatementOfFinancialPosition', 'BalanceSheet', 'Assets', 'Liabilities', 
                'StockholdersEquity', 'Equity', 'LiabilitiesAndEquity'
            ],
            'Statement of Income': [
                'StatementOfIncome', 'IncomeStatement', 'Revenues', 'CostsAndExpenses',
                'OperatingIncome', 'NetIncome', 'EarningsPerShare', 'ComprehensiveIncome'
            ],
            'Statement of Cash Flows': [
                'StatementOfCashFlows', 'CashFlow', 'NetCashProvidedByUsedIn',
                'OperatingActivities', 'InvestingActivities', 'FinancingActivities'
            ],
            'Statement of Stockholders Equity': [
                'StatementOfStockholdersEquity', 'StatementOfChangesInEquity',
                'StockholdersEquityChanges', 'EquityAttributable'
            ]
        }
        
        # Check if current element matches any statement pattern
        for statement_type, patterns in statement_patterns.items():
            for pattern in patterns:
                if pattern.lower() in element_name.lower():
                    return statement_type
        
        # Check element's labels for statement indicators
        labels = self.elements[element_name].get('labels', {})
        for label_text in labels.values():
            if label_text:
                label_lower = label_text.lower()
                if any(x in label_lower for x in ['cash flow', 'operating activities', 'investing activities', 'financing activities']):
                    return 'Statement of Cash Flows'
                elif any(x in label_lower for x in ['income', 'revenue', 'expense', 'earnings', 'profit', 'loss']):
                    return 'Statement of Income'
                elif any(x in label_lower for x in ['balance sheet', 'financial position', 'assets', 'liabilities', 'equity']):
                    return 'Statement of Financial Position'
                elif any(x in label_lower for x in ['stockholders equity', 'changes in equity']):
                    return 'Statement of Stockholders Equity'
        
        # If not found, traverse up the hierarchy
        parents = self.elements[element_name].get('parent_elements', [])
        for parent in parents:
            parent_statement = self.find_top_level_statement(parent, visited.copy())
            if parent_statement != "Unknown":
                return parent_statement
        
        return "Unknown"
    
    def classify_all_elements(self):
        """Classify all elements by their top-level financial statement"""
        print("🏷️  Classifying elements by financial statement...")
        
        for element_name in self.elements:
            statement = self.find_top_level_statement(element_name)
            self.elements[element_name]['financial_statement'] = statement

# Usage example
if __name__ == "__main__":
    print("🔥 Let's build the ULTIMATE US-GAAP database!")
    
    parser = XBRLTaxonomyParser()
    parser.parse_taxonomy()
    
    # Save comprehensive data
    main_df, hierarchy_df = parser.save_comprehensive_csv("us_gaap_ultimate.csv")
    
    # Analytics preview
    print("\n📈 COMPREHENSIVE TAXONOMY ANALYSIS:")
    print(f"📊 Total elements: {len(main_df)}")
    print(f"🌳 Root elements: {len(main_df[main_df['is_root'] == True])}")
    print(f"👶 Leaf elements: {len(main_df[main_df['has_children'] == False])}")
    print(f"🔗 Hierarchy relationships: {len(hierarchy_df)}")
    
    # Show some examples
    print("\n🎯 Sample elements with full details:")
    sample = main_df[main_df['standard_label'].str.contains('Revenue', na=False)].head(3)
    for _, row in sample.iterrows():
        print(f"📋 {row['element_name']}")
        print(f"   Label: {row['standard_label']}")
        print(f"   Type: {row['period_type']} | Balance: {row['balance']}")
        print(f"   Children: {row['child_elements'][:100]}{'...' if len(row['child_elements']) > 100 else ''}")
        print()