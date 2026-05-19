import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import glob
import json
import requests
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.', static_url_path='')

# Configuration
PATH_CORPUS = './LK-Hadith-Corpus'
CSV_FILE = 'cleaned_hadith.csv'
FAISS_INDEX_FILE = 'faiss_index.index'
TRANSLATIONS_FILE = 'urdu_translations.json'

# Global variables to store models and data
model = None
faiss_index = None
df = None
urdu_translations = {}
tfidf_vectorizer = None
tfidf_matrix = None

# 1. Load Urdu Translations Cache
if os.path.exists(TRANSLATIONS_FILE):
    try:
        with open(TRANSLATIONS_FILE, 'r', encoding='utf-8') as f:
            urdu_translations = json.load(f)
        print(f"Loaded {len(urdu_translations)} cached translations.")
    except Exception as e:
        print(f"Error loading translations file: {e}")
        urdu_translations = {}

def save_translations():
    try:
        with open(TRANSLATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(urdu_translations, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving translations: {e}")

# 2. Urdu Translator Helper
def translate_to_urdu(text, hadith_id):
    hadith_id_str = str(hadith_id)
    if hadith_id_str in urdu_translations:
        return urdu_translations[hadith_id_str]
    
    # Strip some common noise from text
    text_clean = text.replace('ﷺ', '(peace be upon him)').strip()
    
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": "ur",
            "dt": "t",
            "q": text_clean
        }
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            res = r.json()
            translated = "".join([sentence[0] for sentence in res[0] if sentence[0]])
            urdu_translations[hadith_id_str] = translated
            save_translations()
            return translated
    except Exception as e:
        print(f"Translation API error: {e}")
    
    return "ترجمہ دستیاب نہیں ہے (Urdu translation currently unavailable)"

# 3. Scholarly Explanation Generator
def generate_explanation(hadith):
    english_hadith = str(hadith.get('English_Hadith', ''))
    chapter_eng = str(hadith.get('Chapter_English', ''))
    section_eng = str(hadith.get('Section_English', ''))
    book = str(hadith.get('Book_Display', ''))
    grade = str(hadith.get('English_Grade', ''))
    hadith_num = str(hadith.get('Hadith_Number', ''))
    
    text_lower = english_hadith.lower()
    
    # Identify context keywords
    title = "Scholarly Commentary & Explanation"
    intro = ""
    lessons = []
    commentary = ""
    
    if "wudu" in text_lower or "ablution" in text_lower or "purification" in text_lower or "wash" in text_lower:
        title = "The Fiqh and Virtues of Wudu (Ablution)"
        intro = f"This Hadith, recorded in {book} under the section of {section_eng}, outlines the precise methodology and spiritual importance of ritual purification."
        lessons = [
            "Purification is half of faith (Iman). Performing ablution diligently purges the believer of minor sins with each drop of water.",
            "Washing the face, hands, and feet in the prescribed order is a fundamental prerequisite for the validity of daily prayers.",
            "Prophetic practice highlights ease and moderation—using an appropriate amount of water without extravagance."
        ]
        commentary = "Classical scholars, including Imam al-Nawawi, note that performing Wudu thoroughly (Isbagh al-Wudu) in difficult conditions carries a doubled reward and elevates a believer's status in the hereafter."
        
    elif "dajjal" in text_lower or "antichrist" in text_lower or "tribulation" in text_lower:
        title = "The Trial (Fitnah) of the Dajjal"
        intro = f"This profound narration in {book} alerts the Muslim community to one of the greatest tribulations to appear before the Day of Judgment."
        lessons = [
            "The Prophet (ﷺ) warned his Ummah about the deceptive nature of the Dajjal, describing his physical traits so believers would recognize him.",
            "Seeking refuge in Allah from the Fitnah of Dajjal at the end of every prayer is a highly emphasized Sunnah.",
            "Reciting the first ten verses of Surah Al-Kahf serves as a spiritual shield and protection against his trials."
        ]
        commentary = "Ibn Hajar al-Asqalani in Fath al-Bari explains that the trial of Dajjal is a test of faith, where miracles will be permitted for him as a tribulation, and steadfastness in tawhid (monotheism) is the only salvation."
        
    elif "fast" in text_lower or "ramadan" in text_lower or "sawm" in text_lower:
        title = "The Spiritual Essence of Fasting"
        intro = f"This Hadith, from the collection of {book}, underscores the unique spiritual rewards and disciplinary nature of fasting."
        lessons = [
            "Fasting (Sawm) is not merely abstaining from food and drink, but also protecting one's tongue, gaze, and actions from sin.",
            "The month of Ramadan is a period of intense Quranic study, generosity, and night prayers (Qiyam).",
            "Fasting acts as a shield (Junnah) protecting the believer from base desires and shielding them in the hereafter."
        ]
        commentary = "Scholars emphasize that the reward for fasting is uniquely reserved by Allah Himself, as it is an act of worship free from ostentation (Riya) and requires absolute sincerity."
        
    elif "pray" in text_lower or "salat" in text_lower or "prostrat" in text_lower or "rak'ah" in text_lower:
        title = "The Pillars and Nuances of Salat (Prayer)"
        intro = f"This narration from {book} highlights the mechanics, virtues, and spiritual heights of the Islamic prayer."
        lessons = [
            "Salat serves as a direct link between the servant and the Creator, offering peace and spiritual replenishment.",
            "Establishing the prayer with correct physical postures—such as prostration (Sujud), where a servant is closest to Allah—is essential.",
            "Consistency in performing voluntary (Sunnah and Nawafil) prayers builds a protective boundary around the obligatory prayers."
        ]
        commentary = "Imam al-Ghazali highlights that the outer postures of prayer should reflect the inner humility of the heart, transforming a daily ritual into a profound spiritual ascent (Mi'raj) for the believer."

    elif "charity" in text_lower or "zakat" in text_lower or "sadaqah" in text_lower or "generous" in text_lower:
        title = "The Economics and Virtues of Charity"
        intro = f"This Hadith in {book} emphasizes the moral obligation of sharing wealth and the spiritual purity of charity."
        lessons = [
            "Charity (Sadaqah) does not decrease wealth; rather, it blesses and purifies the remaining sustenance.",
            "The Prophet (ﷺ) was the most generous of people, particularly during Ramadan, teaching us to give without fear of poverty.",
            "Every good deed is a form of charity, including a kind word, a smile, or removing an obstacle from the path."
        ]
        commentary = "Scholarly commentary explains that Zakat is a mandatory pillar to ensure wealth redistribution, while Sadaqah serves as proof (Burhan) of a person's sincere faith and reliance on Allah."

    elif "quran" in text_lower or "recite" in text_lower or "jibril" in text_lower or "revelation" in text_lower:
        title = "The Revelation and Study of the Noble Qur'an"
        intro = f"This narration details the historical and spiritual relationship between the Prophet (ﷺ), the Angel Gabriel, and the Qur'an."
        lessons = [
            "The regular review and study of the Qur'an is a Sunnah established by the Prophet (ﷺ) and Angel Jibril.",
            "The Qur'an is the ultimate source of guidance, light, and healing for the hearts of believers.",
            "Reciting and reflecting upon the Quranic verses brings peace (Sakinah) and causes angels to descend."
        ]
        commentary = "Imam al-Suyuti notes that studying the Quran in the company of others (Mudarasah) is one of the most virtuous deeds, enhancing understanding and strengthening spiritual bond with the divine speech."

    elif "parent" in text_lower or "mother" in text_lower or "father" in text_lower or "family" in text_lower:
        title = "Filial Piety and Family Ties (Silat ar-Rahim)"
        intro = f"This Hadith stresses the paramount importance of honoring parents and maintaining strong family relations."
        lessons = [
            "Obedience and kindness to parents are ranked among the most beloved deeds to Allah, second only to prayer.",
            "Upholding family ties (Silat ar-Rahim) is a means of increasing one's sustenance and extending one's life.",
            "Treating relatives and family members with patience, even when they do not reciprocate, is a sign of true faith."
        ]
        commentary = "Scholars explain that the womb (Rahim) is named after the Merciful (Rahman), and Allah connects Himself with those who maintain family ties and cuts off those who sever them."

    elif "knowledge" in text_lower or "learn" in text_lower or "scholar" in text_lower:
        title = "The Status and Obligation of Seeking Knowledge"
        intro = f"This Hadith, from {book}, highlights the immense virtues and mandatory nature of seeking sacred knowledge."
        lessons = [
            "Seeking knowledge is an obligation upon every Muslim, enabling them to worship Allah with insight.",
            "Allah makes the path to Paradise easy for anyone who sets out on a path in search of knowledge.",
            "Scholars are the inheritors of the Prophets, inheriting knowledge rather than material wealth."
        ]
        commentary = "Ibn al-Qayyim states that the superiority of knowledge over worship lies in its reach; while worship benefits the individual, knowledge guides the entire community and preserves the religion."

    else:
        # General explanation based on Chapter and Section
        title = f"Lessons from Chapter: {chapter_eng}"
        intro = f"This Hadith, found in {book} (Hadith No. {hadith_num}), is classified under the chapter of '{chapter_eng}' and section of '{section_eng}'."
        lessons = [
            f"It provides practical guidance regarding {section_eng.lower() if section_eng else 'righteous behavior'}, illustrating the comprehensive nature of Islamic ethics.",
            f"The narration holds a grading of '{grade}' indicating its level of transmission and authenticity.",
            "Believers are encouraged to study the chain of narrators (Isnad) and text (Matn) to appreciate the preservation of prophetic history."
        ]
        commentary = f"Commentators of {book} explain that narrations in this section are aimed at refining the daily conduct of the believer and aligning their actions with the spiritual model of the Prophet (ﷺ)."
        
    return {
        "title": title,
        "introduction": intro,
        "lessons": lessons,
        "scholarly_commentary": commentary
    }

# 4. Initialization at Startup
def init_data():
    global model, faiss_index, df
    
    print("--------------------------------------------------")
    print("INITIALIZING RAG SYSTEM BACKEND...")
    print("--------------------------------------------------")
    
    # Check if files exist
    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"Missing base corpus CSV: {CSV_FILE}")
    if not os.path.exists(FAISS_INDEX_FILE):
        raise FileNotFoundError(f"Missing FAISS index file: {FAISS_INDEX_FILE}")
        
    # Load DataFrame
    print("Loading cleaned_hadith.csv into memory...")
    df = pd.read_csv(CSV_FILE)
    print(f"Loaded {len(df)} hadith records successfully.")
    
    # Map Book Ranges
    print("Computing book ranges from folder structure...")
    files = glob.glob(PATH_CORPUS + '/**/*.csv', recursive=True)
    columns_spec = [
        'Chapter_Number', 'Chapter_English', 'Chapter_Arabic',
        'Section_Number', 'Section_English', 'Section_Arabic',
        'Hadith_Number', 'English_Hadith', 'English_Isnad',
        'English_Matn', 'Arabic_Hadith', 'Arabic_Isnad',
        'Arabic_Matn', 'Arabic_Grade', 'English_Grade'
    ]
    
    book_ranges = []
    current_idx = 0
    for f in files:
        parent_folder = os.path.basename(os.path.dirname(f))
        try:
            df_temp = pd.read_csv(f, names=columns_spec, skiprows=1)
            row_count = len(df_temp)
            book_ranges.append((parent_folder, current_idx, current_idx + row_count))
            current_idx += row_count
        except Exception as e:
            print(f"Warning: could not process {f}: {e}")
            
    df['Book'] = 'Unknown'
    for book, start, end in book_ranges:
        df.loc[start:end-1, 'Book'] = book
        
    book_display_names = {
        'AbuDaud': 'Sunan Abi Dawud',
        'Bukhari': 'Sahih al-Bukhari',
        'IbnMaja': 'Sunan Ibn Majah',
        'Muslim': 'Sahih Muslim',
        'Nesai': "Sunan an-Nasa'i",
        'Tirmizi': "Jami' at-Tirmidhi",
        'Unknown': 'Unknown Collector'
    }
    df['Book_Display'] = df['Book'].map(book_display_names).fillna(df['Book'])
    print("Book ranges calculated and mapped successfully:")
    print(df['Book_Display'].value_counts())
    
    # Load FAISS index
    print("Loading FAISS index...")
    real_index_path = 'real_faiss_index.index'
    if os.path.exists(real_index_path):
        print(f"Found real semantic FAISS index: {real_index_path}. Loading it.")
        faiss_index = faiss.read_index(real_index_path)
    else:
        print(f"Loading baseline FAISS index: {FAISS_INDEX_FILE}")
        faiss_index = faiss.read_index(FAISS_INDEX_FILE)
    print(f"FAISS index loaded. Total elements in index: {faiss_index.ntotal}")
    
    # Load SentenceTransformer model
    print("Loading SentenceTransformer model ('all-MiniLM-L6-v2')...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    # Initialize TF-IDF text search index
    global tfidf_vectorizer, tfidf_matrix
    from sklearn.feature_extraction.text import TfidfVectorizer
    print("Fitting TF-IDF text search index...")
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(df['English_Hadith'].fillna('').astype(str))
    print("TF-IDF index built successfully.")
    
    print("Model loaded successfully. System ready.")
    print("--------------------------------------------------")

# Initialize models and data
init_data()

# 5. Routing
@app.route('/')
def home():
    # Serve index.html from static folder
    return send_from_directory('.', 'index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json or {}
        query = data.get('message', '').strip()
        count = int(data.get('count', 5))
        
        if not query:
            return jsonify({"error": "Query message cannot be empty"}), 400
            
        print(f"Received similarity query: '{query}' (requesting top {count})")
        
        # Embed query
        query_embeddings = model.encode([query])
        
        # 1. Search FAISS first (semantic baseline)
        distances, indices = faiss_index.search(query_embeddings, count * 5)
        
        # 2. Build candidate indices
        import re
        matched_indices = []
        matched_distances = {}
        
        q_lower = query.lower().strip()
        
        # Try exact word matches in English_Hadith
        try:
            pattern = rf'\b{re.escape(q_lower)}\b'
            mask = df['English_Hadith'].astype(str).str.lower().str.contains(pattern, regex=True, na=False)
            keyword_matches = df[mask]
        except Exception:
            mask = df['English_Hadith'].astype(str).str.lower().str.contains(re.escape(q_lower), na=False)
            keyword_matches = df[mask]
            
        # Fallback to multi-word check if no exact phrase matches
        if len(keyword_matches) == 0 and len(q_lower.split()) > 1:
            words = [w for w in q_lower.split() if len(w) > 3]
            if words:
                mask = np.ones(len(df), dtype=bool)
                for w in words:
                    mask = mask & df['English_Hadith'].astype(str).str.lower().str.contains(re.escape(w), na=False)
                keyword_matches = df[mask]
                
        # Prioritize Bukhari and Muslim in keyword matches
        if len(keyword_matches) > 0:
            keyword_matches = keyword_matches.copy()
            keyword_matches['priority'] = keyword_matches['Book'].apply(
                lambda b: 0 if b in ['Bukhari', 'Muslim'] else 1
            )
            keyword_matches = keyword_matches.sort_values(by=['priority'])
            for idx, row in keyword_matches.head(count).iterrows():
                matched_indices.append(int(idx))
                matched_distances[int(idx)] = 0.1  # High similarity score for exact matches
                
        # Fill remaining slots using TF-IDF text search
        if len(matched_indices) < count:
            try:
                # Transform query to TF-IDF vector
                query_vec = tfidf_vectorizer.transform([query])
                # Calculate cosine similarities
                from sklearn.metrics.pairwise import cosine_similarity
                similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
                
                # Sort indices by highest similarity
                top_similar_indices = np.argsort(similarities)[::-1]
                
                for idx in top_similar_indices:
                    idx = int(idx)
                    # Ignore if similarity is 0
                    if similarities[idx] <= 0:
                        break
                    if idx not in matched_indices:
                        matched_indices.append(idx)
                        # Map cosine similarity to a distance-like value
                        matched_distances[idx] = float(1.0 - similarities[idx])
                        if len(matched_indices) >= count:
                            break
            except Exception as e:
                print(f"TF-IDF search error: {e}")
                
        # Fill remaining slots using FAISS index as final fallback
        if len(matched_indices) < count:
            for i in range(len(indices[0])):
                idx = int(indices[0][i])
                if idx < 0 or idx >= len(df):
                    continue
                if idx not in matched_indices:
                    matched_indices.append(idx)
                    matched_distances[idx] = float(distances[0][i])
                    if len(matched_indices) >= count:
                        break
                        
        # Trim to count
        matched_indices = matched_indices[:count]
        
        results = []
        for idx in matched_indices:
            row = df.iloc[idx]
            
            # Translate English to Urdu on the fly (and cache it)
            english_hadith = str(row.get('English_Hadith', ''))
            urdu_hadith = translate_to_urdu(english_hadith, idx)
            
            # Generate Scholarly Explanation
            explanation = generate_explanation(row)
            
            dist = matched_distances.get(idx, 1.0)
            
            results.append({
                "id": idx,
                "hadith_number": str(row.get('Hadith_Number', '')),
                "book": str(row.get('Book_Display', '')),
                "chapter_english": str(row.get('Chapter_English', '')),
                "chapter_arabic": str(row.get('Chapter_Arabic', '')),
                "section_english": str(row.get('Section_English', '')),
                "section_arabic": str(row.get('Section_Arabic', '')),
                "english_hadith": english_hadith,
                "arabic_hadith": str(row.get('Arabic_Hadith', '')),
                "english_grade": str(row.get('English_Grade', '')),
                "arabic_grade": str(row.get('Arabic_Grade', '')),
                "urdu_hadith": urdu_hadith,
                "explanation": explanation,
                "distance": dist
            })
            
        return jsonify({
            "query": query,
            "results": results
        })
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/explore', methods=['GET'])
def explore():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        book_filter = request.args.get('book', 'All')
        search_query = request.args.get('search', '').strip().lower()
        
        filtered_df = df
        
        if book_filter != 'All':
            filtered_df = filtered_df[filtered_df['Book'] == book_filter]
            
        if search_query:
            mask = (
                filtered_df['English_Hadith'].astype(str).str.lower().str.contains(search_query, na=False) |
                filtered_df['Arabic_Hadith'].astype(str).str.contains(search_query, na=False) |
                filtered_df['Chapter_English'].astype(str).str.lower().str.contains(search_query, na=False) |
                filtered_df['Section_English'].astype(str).str.lower().str.contains(search_query, na=False)
            )
            filtered_df = filtered_df[mask]
            
        total_records = len(filtered_df)
        total_pages = (total_records + per_page - 1) // per_page if total_records > 0 else 1
        
        start_row = (page - 1) * per_page
        end_row = start_row + per_page
        paginated_df = filtered_df.iloc[start_row:end_row]
        
        results = []
        for idx, row in paginated_df.iterrows():
            results.append({
                "id": int(idx),
                "hadith_number": str(row.get('Hadith_Number', '')),
                "book": str(row.get('Book_Display', '')),
                "chapter_english": str(row.get('Chapter_English', '')),
                "chapter_arabic": str(row.get('Chapter_Arabic', '')),
                "section_english": str(row.get('Section_English', '')),
                "section_arabic": str(row.get('Section_Arabic', '')),
                "english_hadith": str(row.get('English_Hadith', '')),
                "arabic_hadith": str(row.get('Arabic_Hadith', '')),
                "english_grade": str(row.get('English_Grade', '')),
                "arabic_grade": str(row.get('Arabic_Grade', ''))
            })
            
        return jsonify({
            "hadiths": results,
            "total": total_records,
            "page": page,
            "pages": total_pages,
            "per_page": per_page
        })
    except Exception as e:
        print(f"Error in explore endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/books', methods=['GET'])
def get_books():
    try:
        total_count = len(df)
        books = [{"name": "All Books", "id": "All", "count": total_count}]
        
        book_ids = ['Bukhari', 'Muslim', 'AbuDaud', 'Tirmizi', 'Nesai', 'IbnMaja']
        book_display_names = {
            'AbuDaud': 'Sunan Abi Dawud',
            'Bukhari': 'Sahih al-Bukhari',
            'IbnMaja': 'Sunan Ibn Majah',
            'Muslim': 'Sahih Muslim',
            'Nesai': "Sunan an-Nasa'i",
            'Tirmizi': "Jami' at-Tirmidhi"
        }
        
        for bid in book_ids:
            count = int((df['Book'] == bid).sum())
            books.append({
                "name": book_display_names[bid],
                "id": bid,
                "count": count
            })
            
        return jsonify(books)
    except Exception as e:
        print(f"Error in get_books endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/translate/<int:hadith_id>', methods=['GET'])
def translate(hadith_id):
    try:
        if hadith_id < 0 or hadith_id >= len(df):
            return jsonify({"error": "Invalid Hadith ID"}), 400
            
        row = df.iloc[hadith_id]
        english_hadith = str(row.get('English_Hadith', ''))
        
        # Translate
        urdu_hadith = translate_to_urdu(english_hadith, hadith_id)
        
        # Explanation
        explanation = generate_explanation(row)
        
        return jsonify({
            "id": hadith_id,
            "urdu_hadith": urdu_hadith,
            "explanation": explanation
        })
    except Exception as e:
        print(f"Error in translate endpoint: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
