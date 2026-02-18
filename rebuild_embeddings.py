"""
Rebuild embeddings with the correct model (BAAI/bge-small-en-v1.5).
This fixes the dimension mismatch issue.
"""
import pickle
import json
import numpy as np
from pathlib import Path
from fastembed import TextEmbedding

# Fix Windows console encoding
import sys
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def main():
    print("\n" + "="*80)
    print("  Rebuilding Embeddings with Correct Model")
    print("="*80 + "\n")
    
    # Configuration
    MODEL_NAME = "BAAI/bge-small-en-v1.5"  # 384 dimensions, memory efficient
    DATA_FILE = Path("data/gita_english.json")
    OUTPUT_FILE = Path("models/gita_embeddings.pkl")
    
    # Fallback to Hindi if English not available
    if not DATA_FILE.exists():
        print("[WARNING] English file not found, using Hindi version...")
        DATA_FILE = Path("data/gita_emotions.json")
    
    # Step 1: Load data
    print(f"[1/4] Loading data from {DATA_FILE}...")
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    chapters = data.get('chapters', {})
    print(f"      Loaded {len(chapters)} chapters\n")
    
    # Step 2: Prepare texts
    print("[2/4] Preparing texts for embedding...")
    shlokas = []
    texts_to_embed = []
    
    for ch_id, verses in chapters.items():
        for v_id, verse in verses.items():
            # Use English meaning if available, else Hindi
            meaning = verse.get('meaning_english', verse.get('meaning', ''))
            text = verse.get('text', '')
            
            # Get emotions if available
            emotions = verse.get('emotions', {})
            dominant_emotion = verse.get('dominant_emotion', 'neutral')
            top_emotions = [k for k, v in emotions.items() if v > 0.3]
            emotion_text = " ".join(top_emotions)
            
            # Create rich searchable text
            full_text = f"{text} {meaning} {dominant_emotion} {emotion_text}"
            
            shloka_info = {
                "id": f"{ch_id}.{v_id}",
                "chapter": int(ch_id),
                "verse": int(v_id),
                "sanskrit": text,
                "meaning": verse.get('meaning_hindi', verse.get('meaning', '')),  # Hindi for display
                "meaning_english": meaning,  # English for search
                "emotions": emotions,
                "dominant_emotion": dominant_emotion
            }
            
            shlokas.append(shloka_info)
            texts_to_embed.append(full_text)
    
    print(f"      Prepared {len(texts_to_embed)} verses\n")
    
    # Step 3: Generate embeddings
    print(f"[3/4] Generating embeddings with {MODEL_NAME}...")
    print("      This will take a few minutes. Please wait...")
    
    model = TextEmbedding(model_name=MODEL_NAME)
    embedding_gen = model.embed(texts_to_embed, batch_size=32)
    
    # Concatenate all batches - FastEmbed returns list of arrays
    embedding_batches = list(embedding_gen)
    
    # Check if we got embeddings
    if not embedding_batches:
        raise ValueError("No embeddings generated!")
    
    # Concatenate along axis 0 (rows)
    embeddings = np.vstack(embedding_batches)
    
    print(f"      Generated {embeddings.shape[0]} embeddings")
    print(f"      Embedding dimension: {embeddings.shape[1]}\n")
    
    # Step 4: Save embeddings
    print(f"[4/4] Saving embeddings to {OUTPUT_FILE}...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'wb') as f:
        pickle.dump({
            'shlokas': shlokas,
            'embeddings': embeddings,
            'model_name': MODEL_NAME
        }, f)
    
    print(f"      Saved successfully!\n")
    
    # Summary
    print("="*80)
    print("[SUCCESS] Embeddings rebuilt successfully!")
    print("="*80)
    print(f"\nModel: {MODEL_NAME}")
    print(f"Verses: {len(shlokas)}")
    print(f"Embedding dimensions: {embeddings.shape[1]}")
    print(f"File size: {OUTPUT_FILE.stat().st_size / (1024*1024):.2f} MB")
    print("\nYou can now run your tests again. Semantic search should work properly!\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
