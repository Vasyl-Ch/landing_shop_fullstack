#!/usr/bin/env python
"""
Script to check Celery and Redis connectivity.
Run this to verify setup in any environment.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_config.settings')
django.setup()

from django.conf import settings
import redis
from celery import Celery

def check_redis():
    """Check Redis connection."""
    print("=" * 50)
    print("Checking Redis connection...")
    print("=" * 50)
    
    try:
        broker_url = settings.CELERY_BROKER_URL
        print(f"Broker URL: {broker_url}")
        
        # Parse Redis URL
        if broker_url.startswith('redis://'):
            url = broker_url.replace('redis://', '')
            if '/' in url:
                host_port, db = url.split('/')
            else:
                host_port, db = url, '0'
            
            if ':' in host_port:
                host, port = host_port.split(':')
            else:
                host, port = host_port, 6379
            
            print(f"Connecting to Redis at {host}:{port}, DB: {db}")
            
            r = redis.Redis(host=host, port=int(port), db=int(db), decode_responses=True)
            r.ping()
            print("✅ Redis connection: SUCCESS")
            
            # Test set/get
            r.set('test_key', 'test_value')
            value = r.get('test_key')
            r.delete('test_key')
            print(f"✅ Redis read/write: SUCCESS (test value: {value})")
            return True
        else:
            print(f"❌ Invalid Redis URL format: {broker_url}")
            return False
            
    except Exception as e:
        print(f"❌ Redis connection: FAILED")
        print(f"   Error: {str(e)}")
        return False

def check_celery():
    """Check Celery configuration."""
    print("\n" + "=" * 50)
    print("Checking Celery configuration...")
    print("=" * 50)
    
    try:
        broker_url = settings.CELERY_BROKER_URL
        result_backend = settings.CELERY_RESULT_BACKEND
        
        print(f"Broker URL: {broker_url}")
        print(f"Result Backend: {result_backend}")
        
        # Create Celery app
        app = Celery('project_config')
        app.config_from_object('django.conf:settings', namespace='CELERY')
        
        # Check broker connection
        with app.connection() as conn:
            conn.ensure_connection(max_retries=3)
            print("✅ Celery broker connection: SUCCESS")
        
        # Check registered tasks
        registered_tasks = list(app.tasks.keys())
        print(f"✅ Registered tasks: {len(registered_tasks)}")
        for task in registered_tasks:
            if not task.startswith('celery.'):
                print(f"   - {task}")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery configuration: FAILED")
        print(f"   Error: {str(e)}")
        return False

def main():
    """Run all checks."""
    print("\n" + "=" * 50)
    print("Celery and Redis Health Check")
    print("=" * 50 + "\n")
    
    redis_ok = check_redis()
    celery_ok = check_celery()
    
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    print(f"Redis: {'✅ OK' if redis_ok else '❌ FAILED'}")
    print(f"Celery: {'✅ OK' if celery_ok else '❌ FAILED'}")
    
    if redis_ok and celery_ok:
        print("\n🎉 All checks passed! Celery and Redis are working correctly.")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please review the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
