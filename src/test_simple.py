# test_simple.py - FIXED VERSION
import os
import shutil
import time
import sys
sys.path.append('src')

from core.agent import create_translator
from core.logger import TranslationLogger  # Import the class
from core.memory import TranslationMemory  # Import the class

# Create instances instead of importing them
logger = TranslationLogger()
memory = TranslationMemory()

def clean_old_data():
    """Remove old ChromaDB data to start fresh"""
    print("🧹 Cleaning old memory data...")
    
    # Paths to clean
    data_paths = [
        "./data/chroma_db",
        "./data/test_memory", 
    ]
    
    for path in data_paths:
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"✅ Removed: {path}")
    
    # Recreate directory
    os.makedirs("./data", exist_ok=True)
    print("✅ Fresh start ready!")

def test_translations():
    print("🧪 Testing Translator with YOUR Test Cases...")
    
    # DO NOT CLEAN DATA - WE WANT TO KEEP LOADED DATASET!
    # clean_old_data()  # <-- COMMENTED OUT!
    
    # Create translator with NEW session
    translator = create_translator(session_id="your_tests_" + str(int(time.time())))
    
    # YOUR TEST CASES
    test_cases = [
        ("partnerships working with industry", "zu"),
        ("we received orders to march and left camp to the rousing sound of our brass band with everyone cheery and excited at the prospect of what lay ahead", "zu"),
        ("the lecturer responsible for this module is as follows", "zu"),
        ("the unisa library offers a range of information services and resources", "zu"),
        ("to learning much inclined", "zu"),
        ("in phase two of the data collection interviews were used as a qualitative data gathering tool to explain triangulate and strengthen the survey results", "zu"),
        ("spiritual wisdom is the most ancient and yet most contemporary of knowledge forms it predates written records and at the same time speaks to the hearts of people of the third millennium", "zu"),
        ("we are starting a boxing tournament today he said", "zu"),
        ("the book can be downloaded from the links", "zu"),
        ("recommendations emphasize the need for collaboration among stakeholders including the department of agriculture south african police service and state information technology agency", "zu"),
        ("speak to people on a level that enables them to understand the ramifications of continuing with life as normal", "zu"),
        ("senior appointments", "zu"),
    ]
    
    print(f"\n{'='*70}")
    print("🎯 YOUR TEST CASES - Translation Test")
    print('='*70)
    
    results = []
    
    for i, (text, target_lang) in enumerate(test_cases):
        print(f"\n📋 Test {i+1}:")
        print(f"   English: '{text}'")
        print(f"   → isiZulu")
        
        try:
            result = translator.translate(
                text=text,
                target_lang=target_lang,
            )
            
            results.append(result)
            
            print(f"   ✅ Translation: {result['translation']}")
            print(f"   📊 Source: {result['source']}")
            print(f"   🎯 Quality: {result.get('quality', 'unknown')}")
            
            # Log the translation using the logger instance
            logger.log(
                input_text=text,
                output_text=result['translation'],
                source_lang="en",
                target_lang=target_lang,
                session_id=translator.session_id,
                agent_thoughts=f"Source: {result['source']}, Quality: {result.get('quality', 'unknown')}",
                tools_used=[result['source']],
                confidence=result.get('confidence', 0.0)
            )
            
            # ADD THIS TO SEE IF DATASET IS LOADED
            if result['source'] == 'memory':
                print("   🎯 FOUND IN DATASET!")
            elif result['source'] == 'api':
                print("   🌐 Using API (dataset not loaded or not matching)")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results.append({"error": str(e)})
        
        # Wait a bit
        print(f"   ⏳ Waiting 2 seconds...")
        time.sleep(2)
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 RESULTS SUMMARY")
    print('='*70)
    
    dictionary_count = 0
    api_count = 0
    memory_count = 0
    errors = 0
    
    for i, result in enumerate(results):
        if isinstance(result, dict) and "error" not in result:
            source = result.get('source', 'unknown')
            if source == 'dictionary':
                dictionary_count += 1
            elif source == 'api':
                api_count += 1
            elif source == 'memory':
                memory_count += 1
        else:
            errors += 1
    
    print(f"\n📈 Translation Sources:")
    print(f"   Dictionary: {dictionary_count}/{len(test_cases)}")
    print(f"   API: {api_count}/{len(test_cases)}")
    print(f"   Memory: {memory_count}/{len(test_cases)}")
    print(f"   Errors: {errors}/{len(test_cases)}")
    
    # Get stats from logger
    stats = logger.get_stats()
    print(f"\n📊 Logger Statistics:")
    print(f"   Total translations logged: {stats.get('total_translations', 0)}")
    print(f"   Average confidence: {stats.get('avg_confidence', 0):.2f}")
    
    # Add interpretation
    print(f"\n💡 INTERPRETATION:")
    if memory_count > 0:
        print(f"   ✅ Dataset is loaded! Found {memory_count} matches")
    else:
        print(f"   ⚠️ Dataset NOT loaded or not matching")
        print(f"   You need to load dataset.csv first using:")
        print(f"   python -c \"import sys; sys.path.append('src'); from core.memory import TranslationMemory; m=TranslationMemory(); m.load_dataset_from_csv('dataset.csv')\"")
    
    print(f"\n{'='*70}")
    print("✅ Test complete!")

# ADD THIS: Test the logger functions
def test_logger_functions():
    """Test that logger methods work"""
    print("\n🧪 Testing Logger Functions...")
    
    # Test read_logs
    logs = logger.read_logs(limit=5)
    print(f"Recent logs: {len(logs)} entries")
    
    # Test get_stats
    stats = logger.get_stats()
    print(f"Stats available: {bool(stats)}")
    
    print("✅ Logger functions working!")

if __name__ == "__main__":
    # Test logger first
    test_logger_functions()
    
    # Then run main tests
    test_translations()