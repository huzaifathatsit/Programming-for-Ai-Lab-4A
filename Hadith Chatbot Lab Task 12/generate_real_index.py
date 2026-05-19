import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

def main():
    csv_file = 'cleaned_hadith.csv'
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found.")
        return
        
    print("Loading corpus...")
    df = pd.read_csv(csv_file, low_memory=False)
    print(f"Loaded {len(df)} records.")
    
    print("Loading SentenceTransformer model ('all-MiniLM-L6-v2')...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    print("Extracting English Hadith texts...")
    texts = [str(t)[:1000] for t in df['English_Hadith']]
    
    try:
        print("Encoding texts chunk by chunk (this may take a few minutes on CPU)...")
        chunk_size = 1000
        all_embeddings = []
        
        for i in range(0, len(texts), chunk_size):
            chunk = texts[i:i+chunk_size]
            print(f"Encoding chunk {i // chunk_size + 1}/{(len(texts) + chunk_size - 1) // chunk_size}... (indices {i} to {i+len(chunk)})")
            import sys
            sys.stdout.flush()
            
            chunk_embeddings = model.encode(chunk, show_progress_bar=False, batch_size=64)
            all_embeddings.append(chunk_embeddings)
            
        embeddings = np.vstack(all_embeddings)
        print(f"All texts encoded. Shape: {embeddings.shape}")
        
        print("Saving embeddings to 'real_hadith_embeddings.npy'...")
        np.save('real_hadith_embeddings.npy', embeddings)
        
        print("Building FAISS index...")
        import faiss
        dimensions = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimensions)
        index.add(embeddings)
        
        print("Saving FAISS index to 'real_faiss_index.index'...")
        faiss.write_index(index, 'real_faiss_index.index')
        print("Real FAISS index generated successfully!")
    except Exception as e:
        import traceback
        print("An error occurred during indexing:")
        traceback.print_exc()

if __name__ == '__main__':
    main()
