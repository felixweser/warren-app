#!/usr/bin/env python3
import requests
import time
import subprocess
import sys

def test_endpoint():
    try:
        # Test the new endpoint
        response = requests.get('http://localhost:8000/company-metrics/GOOGL')
        if response.status_code == 200:
            data = response.json()
            print('✅ New endpoint works!')
            print(f'Company: {data["ticker"]}')
            print(f'Fiscal Year: {data["fiscal_year"]}')
            print(f'Revenue Growth: {data["metrics"]["revenue_growth"]:.1f}%')
            print(f'Free Cash Flow: ${data["metrics"]["free_cash_flow"]:,.0f}')
            print(f'Net Margin: {data["metrics"]["net_margin"]:.1f}%')
            print(f'ROE: {data["metrics"]["roe"]:.1f}%')
            print(f'Debt/Equity: {data["metrics"]["debt_to_equity"]:.2f}')
        else:
            print(f'❌ Error: {response.status_code} - {response.text}')
    except Exception as e:
        print(f'❌ Error testing endpoint: {e}')

if __name__ == "__main__":
    test_endpoint()