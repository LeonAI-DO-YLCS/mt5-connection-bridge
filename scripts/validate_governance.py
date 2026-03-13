import sys
import yaml
from pathlib import Path

def validate():
    config_path = Path('config/governance-checklist.yaml')
    if not config_path.exists():
        print(f"Error: {config_path} not found.")
        sys.exit(1)
        
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
        
    if 'endpoints' not in data:
        print("Error: 'endpoints' key missing in governance-checklist.yaml")
        sys.exit(1)
        
    required_endpoints = [
        '/mt5/raw/margin-check',
        '/mt5/raw/profit-calc',
        '/mt5/raw/market-book',
        '/mt5/raw/terminal-info',
        '/mt5/raw/account-info',
        '/mt5/raw/last-error'
    ]
    
    required_fields = [
        'safety_class',
        'auth_required',
        'logging_policy',
        'readiness_gated'
    ]
    
    endpoints_data = data['endpoints']
    
    for ep in required_endpoints:
        if ep not in endpoints_data:
            print(f"Error: Endpoint {ep} missing from governance checklist.")
            sys.exit(1)
            
        ep_data = endpoints_data[ep]
        for field in required_fields:
            if field not in ep_data:
                print(f"Error: Endpoint {ep} is missing required field '{field}'.")
                sys.exit(1)
                
    print("Governance validation passed.")
    sys.exit(0)

if __name__ == "__main__":
    validate()
