"""
Test script for checking view functionality and URL routing
"""
import os
import sys
import django
from urllib.parse import urlparse

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_venda.settings')
django.setup()

from django.test import Client
from django.urls import reverse, resolve, NoReverseMatch
from django.contrib.auth import get_user_model

User = get_user_model()

def test_configuracao_urls():
    """Test URL routing for the configuracao app"""
    print("\nTesting URL configuration for configuracao app:")

    # List of expected URL names in the configuracao app
    url_names = [
        'dashboard',
        'general_settings',
        'email_settings',
        'notification_settings',
        'appearance_settings',
        'backup_settings',
        'custom_fields',
        'system_maintenance'
    ]

    # Check each URL name
    for name in url_names:
        try:
            url = reverse(f'configuracao:{name}')
            print(f"✓ URL 'configuracao:{name}' resolves to: {url}")

            # Check reverse resolution
            resolver = resolve(url)
            print(f"  - Maps to view: {resolver.func.__name__}")
        except NoReverseMatch:
            print(f"✗ URL 'configuracao:{name}' could not be resolved")
        except Exception as e:
            print(f"✗ Error with URL 'configuracao:{name}': {str(e)}")

    return True

def test_view_responses():
    """Test basic view responses (without authentication)"""
    client = Client()

    print("\nChecking view responses (without authentication):")
    try:
        # Test home page
        response = client.get('/')
        print(f"Home page response: {response.status_code}")

        # Try configuracao URLs
        try:
            dashboard_url = reverse('configuracao:dashboard')
            response = client.get(dashboard_url)
            print(f"Configuration dashboard response: {response.status_code}")
            # 302 (redirect) is expected if login is required
        except NoReverseMatch:
            print("Configuration dashboard URL not found")
    except Exception as e:
        print(f"Error testing views: {str(e)}")

    return True

def list_all_urls():
    """List all available URLs in the project"""
    print("\nAttempting to discover all URLs in the project:")

    from django.urls import get_resolver
    resolver = get_resolver()

    def extract_urls(resolver, prefix=''):
        urls = []
        for pattern in resolver.url_patterns:
            if hasattr(pattern, 'url_patterns'):
                # Fix the NoneType error by properly checking app_name
                new_prefix = prefix
                if hasattr(pattern, 'app_name') and pattern.app_name:
                    new_prefix = prefix + pattern.app_name + ':'
                urls.extend(extract_urls(pattern, new_prefix))
            else:
                url_name = pattern.name
                if url_name:
                    full_url_name = prefix + url_name if prefix else url_name
                    urls.append(full_url_name)
        return urls

    all_urls = extract_urls(resolver)
    for url_name in sorted(all_urls):
        if url_name:
            try:
                url = reverse(url_name)
                print(f"URL '{url_name}' -> {url}")
            except NoReverseMatch:
                print(f"Could not reverse '{url_name}'")

    return True

if __name__ == "__main__":
    print("Testing views and URL routing...")
    test_configuracao_urls()
    test_view_responses()
    list_all_urls()
    print("\nView tests completed.")
