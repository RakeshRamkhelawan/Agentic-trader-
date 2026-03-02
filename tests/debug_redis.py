#!/usr/bin/env python3
"""Debug Redis connection and XADD command."""

import sys
sys.path.insert(0, '.')

import redis.asyncio as redis
import asyncio


async def debug_redis():
    print("=" * 60)
    print("REDIS DEBUG")
    print("=" * 60)
    
    # Connect
    print("\n1. Connecting to redis://localhost:6379...")
    r = redis.from_url('redis://localhost:6379', decode_responses=True)
    
    try:
        await r.ping()
        print("   Connected!")
        
        # Get version
        print("\n2. Checking Redis version...")
        info = await r.info('server')
        version = info.get('redis_version', 'unknown')
        print(f"   Redis version: {version}")
        
        # Check if XADD is available
        print("\n3. Checking XADD availability...")
        try:
            cmds = await r.execute_command('COMMAND', 'INFO', 'XADD')
            if cmds and len(cmds) > 0:
                print("   XADD command is available")
            else:
                print("   XADD command NOT found")
        except Exception as e:
            print(f"   Error checking XADD: {e}")
        
        # Try XADD
        print("\n4. Testing XADD...")
        try:
            result = await r.execute_command('XADD', 'debug_stream', '*', 'test', 'value')
            print(f"   XADD success: {result}")
            
            # Cleanup
            await r.delete('debug_stream')
            print("   Cleanup done")
            
        except Exception as e:
            print(f"   XADD failed: {type(e).__name__}: {e}")
        
        # Check loaded modules
        print("\n5. Checking Redis modules...")
        try:
            modules = await r.execute_command('MODULE', 'LIST')
            if modules:
                print(f"   Loaded modules: {modules}")
            else:
                print("   No modules loaded")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test with redis-py's xadd method
        print("\n6. Testing r.xadd() method...")
        try:
            result = await r.xadd('test_stream', {'field': 'value'})
            print(f"   r.xadd() success: {result}")
            await r.delete('test_stream')
        except Exception as e:
            print(f"   r.xadd() failed: {type(e).__name__}: {e}")
        
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        await r.close()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(debug_redis())
