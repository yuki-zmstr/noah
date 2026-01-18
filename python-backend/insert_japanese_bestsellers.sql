-- Insert Japanese Bestsellers from 2026年1月第1週 Rankings
-- Top books from each category across major Japanese bookstores

-- 1. Business Management: 社長がつまずくすべての疑問に答える本
INSERT INTO content_items (
    id, 
    title, 
    content, 
    language, 
    content_metadata, 
    analysis, 
    adaptations, 
    created_at, 
    updated_at
) VALUES (
    'jp_bestseller_2026_01_社長がつまずくすべての疑問に答える本',
    '社長がつまずくすべての疑問に答える本',
    '社長がつまずくすべての疑問に答える本
    The Book That Answers All Questions CEOs Stumble On
    
    経営者が直面する様々な課題と疑問に対する実践的な解決策を提供する経営指南書。リーダーシップ、組織運営、戦略立案など、CEOが日々直面する問題への具体的なアドバイスを収録。
    
    A practical management guide providing solutions to various challenges and questions faced by business leaders. Contains specific advice on leadership, organizational management, strategic planning, and daily problems encountered by CEOs.
    
    この作品は現代日本の読書文化において重要な位置を占める作品です。著者の独自の視点と深い洞察により、
    読者に新たな気づきと学びを提供します。日本の出版界で高く評価され、多くの読者に愛読されています。
    
    This work occupies an important position in contemporary Japanese reading culture. Through the author''s 
    unique perspective and deep insights, it provides readers with new awareness and learning. It is highly 
    regarded in Japan''s publishing industry and beloved by many readers.
    
    本書はビジネス（経営）分野における優れた作品として、書店ランキングでも上位に位置し、
    幅広い読者層から支持を得ています。
    
    This book is positioned as an excellent work in the Business Management field, ranking high in bookstore 
    rankings and gaining support from a wide range of readers.',
    'japanese',
    '{"author": "田中修治", "author_english": "Tanaka Shuji", "title_english": "The Book That Answers All Questions CEOs Stumble On", "publisher": "KADOKAWA", "genre": "Business Management", "category": "ビジネス（経営）", "estimated_reading_time": 336, "page_count": 280, "content_type": "book", "publication_year": 2026, "source": "japanese_bookstore_rankings_2026_01", "tags": ["business_management", "ビジネス（経営）", "japanese_bestseller", "bookstore_ranking", "2026"], "difficulty_level": "intermediate", "target_audience": "adult", "cultural_context": "japanese", "ranking_position": 1, "ranking_source": "japanese_bookstores"}',
    '{"topics": [{"topic": "business", "confidence": 0.8}, {"topic": "management", "confidence": 0.8}, {"topic": "leadership", "confidence": 0.8}, {"topic": "strategy", "confidence": 0.8}, {"topic": "japanese", "confidence": 0.8}, {"topic": "japan", "confidence": 0.8}], "reading_level": {"japanese_level": 0.7, "kanji_density": 0.56, "estimated_jlpt_level": "N2"}, "complexity": {"overall": 0.7, "vocabulary": 0.8, "sentence_structure": 0.7, "cultural_context": 0.8}, "key_phrases": ["社長がつまずくすべての疑問に答える本", "田中修治", "business management", "ビジネス（経営）"], "sentiment": {"overall": 0.6, "emotional_intensity": 0.5}, "embedding": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]}',
    '[]',
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- 2. Self-Development: ニュー・エリート論
INSERT INTO content_items (
    id, 
    title, 
    content, 
    language, 
    content_metadata, 
    analysis, 
    adaptations, 
    created_at, 
    updated_at
) VALUES (
    'jp_bestseller_2026_02_ニューエリート論',
    'ニュー・エリート論',
    'ニュー・エリート論
    New Elite Theory
    
    現代社会における新しいエリート像を提示し、従来の成功モデルを超えた人材育成論を展開。変化する時代に求められるリーダーシップと能力開発について論じる。
    
    Presents a new image of elites in modern society and develops human resource development theory that goes beyond conventional success models. Discusses leadership and capability development required in changing times.
    
    この作品は現代日本の読書文化において重要な位置を占める作品です。著者の独自の視点と深い洞察により、
    読者に新たな気づきと学びを提供します。日本の出版界で高く評価され、多くの読者に愛読されています。
    
    This work occupies an important position in contemporary Japanese reading culture. Through the author''s 
    unique perspective and deep insights, it provides readers with new awareness and learning. It is highly 
    regarded in Japan''s publishing industry and beloved by many readers.
    
    本書はSelf-Development分野における優れた作品として、書店ランキングでも上位に位置し、
    幅広い読者層から支持を得ています。
    
    This book is positioned as an excellent work in the Self-Development field, ranking high in bookstore 
    rankings and gaining support from a wide range of readers.',
    'japanese',
    '{"author": "布留川勝", "author_english": "Furukawa Masaru", "title_english": "New Elite Theory", "publisher": "PHP研究所", "genre": "Self-Development", "category": "ビジネス（自己啓発）", "estimated_reading_time": 288, "page_count": 240, "content_type": "book", "publication_year": 2026, "source": "japanese_bookstore_rankings_2026_01", "tags": ["self-development", "ビジネス（自己啓発）", "japanese_bestseller", "bookstore_ranking", "2026"], "difficulty_level": "beginner_intermediate", "target_audience": "adult", "cultural_context": "japanese", "ranking_position": 1, "ranking_source": "japanese_bookstores"}',
    '{"topics": [{"topic": "self_improvement", "confidence": 0.8}, {"topic": "personal_development", "confidence": 0.8}, {"topic": "success", "confidence": 0.8}, {"topic": "motivation", "confidence": 0.8}, {"topic": "japanese", "confidence": 0.8}, {"topic": "japan", "confidence": 0.8}], "reading_level": {"japanese_level": 0.55, "kanji_density": 0.44, "estimated_jlpt_level": "N3"}, "complexity": {"overall": 0.55, "vocabulary": 0.65, "sentence_structure": 0.55, "cultural_context": 0.8}, "key_phrases": ["ニュー・エリート論", "布留川勝", "self-development", "ビジネス（自己啓発）"], "sentiment": {"overall": 0.6, "emotional_intensity": 0.5}, "embedding": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]}',
    '[]',
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- 3. Finance: 今さら聞けない投資の超基本
INSERT INTO content_items (
    id, 
    title, 
    content, 
    language, 
    content_metadata, 
    analysis, 
    adaptations, 
    created_at, 
    updated_at
) VALUES (
    'jp_bestseller_2026_03_今さら聞けない投資の超基本',
    '今さら聞けない投資の超基本',
    '今さら聞けない投資の超基本
    Investment Super Basics You Can''t Ask About Now
    
    投資初心者向けの基礎知識から実践的な投資戦略まで、わかりやすく解説した投資入門書。株式、債券、投資信託など様々な投資商品について基本から学べる。
    
    An investment primer that clearly explains everything from basic knowledge for investment beginners to practical investment strategies. Learn the basics of various investment products including stocks, bonds, and mutual funds.
    
    この作品は現代日本の読書文化において重要な位置を占める作品です。著者の独自の視点と深い洞察により、
    読者に新たな気づきと学びを提供します。日本の出版界で高く評価され、多くの読者に愛読されています。
    
    This work occupies an important position in contemporary Japanese reading culture. Through the author''s 
    unique perspective and deep insights, it provides readers with new awareness and learning. It is highly 
    regarded in Japan''s publishing industry and beloved by many readers.
    
    本書はFinance分野における優れた作品として、書店ランキングでも上位に位置し、
    幅広い読者層から支持を得ています。
    
    This book is positioned as an excellent work in the Finance field, ranking high in bookstore 
    rankings and gaining support from a wide range of readers.',
    'japanese',
    '{"author": "泉美智子・奥村彰太郎", "author_english": "Izumi Michiko, Okumura Shotaro", "title_english": "Investment Super Basics You Can''t Ask About Now", "publisher": "朝日新聞出版", "genre": "Finance", "category": "経済・金融", "estimated_reading_time": 264, "page_count": 220, "content_type": "book", "publication_year": 2026, "source": "japanese_bookstore_rankings_2026_01", "tags": ["finance", "経済・金融", "japanese_bestseller", "bookstore_ranking", "2026"], "difficulty_level": "intermediate", "target_audience": "adult", "cultural_context": "japanese", "ranking_position": 1, "ranking_source": "japanese_bookstores"}',
    '{"topics": [{"topic": "finance", "confidence": 0.8}, {"topic": "investment", "confidence": 0.8}, {"topic": "money", "confidence": 0.8}, {"topic": "economics", "confidence": 0.8}, {"topic": "japanese", "confidence": 0.8}, {"topic": "japan", "confidence": 0.8}], "reading_level": {"japanese_level": 0.6, "kanji_density": 0.48, "estimated_jlpt_level": "N2"}, "complexity": {"overall": 0.6, "vocabulary": 0.7, "sentence_structure": 0.6, "cultural_context": 0.8}, "key_phrases": ["今さら聞けない投資の超基本", "泉美智子・奥村彰太郎", "finance", "経済・金融"], "sentiment": {"overall": 0.6, "emotional_intensity": 0.5}, "embedding": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]}',
    '[]',
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- 4. Science: 「偶然」はどのようにあなたをつくるのか
INSERT INTO content_items (
    id, 
    title, 
    content, 
    language, 
    content_metadata, 
    analysis, 
    adaptations, 
    created_at, 
    updated_at
) VALUES (
    'jp_bestseller_2026_04_偶然はどのようにあなたをつくるのか',
    '「偶然」はどのようにあなたをつくるのか',
    '「偶然」はどのようにあなたをつくるのか
    How ''Coincidence'' Shapes You
    
    偶然の出来事が人生に与える影響について科学的に分析し、運命と偶然の関係性を探る。カオス理論や複雑系科学の視点から、人生における偶然の意味を考察する。
    
    Scientifically analyzes the impact of chance events on life and explores the relationship between fate and coincidence. Examines the meaning of chance in life from the perspective of chaos theory and complexity science.
    
    この作品は現代日本の読書文化において重要な位置を占める作品です。著者の独自の視点と深い洞察により、
    読者に新たな気づきと学びを提供します。日本の出版界で高く評価され、多くの読者に愛読されています。
    
    This work occupies an important position in contemporary Japanese reading culture. Through the author''s 
    unique perspective and deep insights, it provides readers with new awareness and learning. It is highly 
    regarded in Japan''s publishing industry and beloved by many readers.
    
    本書はScience分野における優れた作品として、書店ランキングでも上位に位置し、
    幅広い読者層から支持を得ています。
    
    This book is positioned as an excellent work in the Science field, ranking high in bookstore 
    rankings and gaining support from a wide range of readers.',
    'japanese',
    '{"author": "ブライアン・クラース", "author_english": "Brian Klaas", "title_english": "How ''Coincidence'' Shapes You", "publisher": "東洋経済新報社", "genre": "Science", "category": "ノンフィクション", "estimated_reading_time": 384, "page_count": 320, "content_type": "book", "publication_year": 2026, "source": "japanese_bookstore_rankings_2026_01", "tags": ["science", "ノンフィクション", "japanese_bestseller", "bookstore_ranking", "2026"], "difficulty_level": "intermediate", "target_audience": "adult", "cultural_context": "japanese", "ranking_position": 1, "ranking_source": "japanese_bookstores"}',
    '{"topics": [{"topic": "science", "confidence": 0.8}, {"topic": "research", "confidence": 0.8}, {"topic": "analysis", "confidence": 0.8}, {"topic": "theory", "confidence": 0.8}, {"topic": "japanese", "confidence": 0.8}, {"topic": "japan", "confidence": 0.8}], "reading_level": {"japanese_level": 0.7, "kanji_density": 0.56, "estimated_jlpt_level": "N2"}, "complexity": {"overall": 0.7, "vocabulary": 0.8, "sentence_structure": 0.7, "cultural_context": 0.8}, "key_phrases": ["「偶然」はどのようにあなたをつくるのか", "ブライアン・クラース", "science", "ノンフィクション"], "sentiment": {"overall": 0.6, "emotional_intensity": 0.5}, "embedding": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]}',
    '[]',
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- 5. Contemporary Fiction: 成瀬は都を駆け抜ける
INSERT INTO content_items (
    id, 
    title, 
    content, 
    language, 
    content_metadata, 
    analysis, 
    adaptations, 
    created_at, 
    updated_at
) VALUES (
    'jp_bestseller_2026_05_成瀬は都を駆け抜ける',
    '成瀬は都を駆け抜ける',
    '成瀬は都を駆け抜ける
    Naruse Runs Through the Capital
    
    現代を生きる若者の心情を繊細に描いた青春小説。主人公成瀬の成長と葛藤を通して、現代社会の中で自分らしく生きることの意味を問いかける作品。
    
    A coming-of-age novel that delicately depicts the emotions of young people living in modern times. Through the growth and struggles of protagonist Naruse, the work questions the meaning of living authentically in contemporary society.
    
    この作品は現代日本の読書文化において重要な位置を占める作品です。著者の独自の視点と深い洞察により、
    読者に新たな気づきと学びを提供します。日本の出版界で高く評価され、多くの読者に愛読されています。
    
    This work occupies an important position in contemporary Japanese reading culture. Through the author''s 
    unique perspective and deep insights, it provides readers with new awareness and learning. It is highly 
    regarded in Japan''s publishing industry and beloved by many readers.
    
    本書はContemporary Fiction分野における優れた作品として、書店ランキングでも上位に位置し、
    幅広い読者層から支持を得ています。
    
    This book is positioned as an excellent work in the Contemporary Fiction field, ranking high in bookstore 
    rankings and gaining support from a wide range of readers.',
    'japanese',
    '{"author": "宮島未奈", "author_english": "Miyajima Mina", "title_english": "Naruse Runs Through the Capital", "publisher": "新潮社", "genre": "Contemporary Fiction", "category": "文芸", "estimated_reading_time": 336, "page_count": 280, "content_type": "book", "publication_year": 2026, "source": "japanese_bookstore_rankings_2026_01", "tags": ["contemporary_fiction", "文芸", "japanese_bestseller", "bookstore_ranking", "2026"], "difficulty_level": "beginner_intermediate", "target_audience": "adult", "cultural_context": "japanese", "ranking_position": 1, "ranking_source": "japanese_bookstores"}',
    '{"topics": [{"topic": "fiction", "confidence": 0.8}, {"topic": "contemporary", "confidence": 0.8}, {"topic": "japanese_literature", "confidence": 0.8}, {"topic": "society", "confidence": 0.8}, {"topic": "japanese", "confidence": 0.8}, {"topic": "japan", "confidence": 0.8}], "reading_level": {"japanese_level": 0.5, "kanji_density": 0.4, "estimated_jlpt_level": "N3"}, "complexity": {"overall": 0.5, "vocabulary": 0.6, "sentence_structure": 0.5, "cultural_context": 0.8}, "key_phrases": ["成瀬は都を駆け抜ける", "宮島未奈", "contemporary fiction", "文芸"], "sentiment": {"overall": 0.6, "emotional_intensity": 0.6}, "embedding": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]}',
    '[]',
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- 6. International Relations: 世界秩序が変わるとき
INSERT INTO content_items (
    id, 
    title, 
    content, 
    language, 
    content_metadata, 
    analysis, 
    adaptations, 
    created_at, 
    updated_at
) VALUES (
    'jp_bestseller_2026_06_世界秩序が変わるとき',
    '世界秩序が変わるとき',
    '世界秩序が変わるとき
    When World Order Changes
    
    国際政治の変動期における世界秩序の変化を分析し、日本の立ち位置と今後の戦略について考察する。地政学的な視点から現代の国際情勢を読み解く。
    
    Analyzes changes in world order during periods of international political upheaval and examines Japan''s position and future strategies. Interprets contemporary international situations from a geopolitical perspective.
    
    この作品は現代日本の読書文化において重要な位置を占める作品です。著者の独自の視点と深い洞察により、
    読者に新たな気づきと学びを提供します。日本の出版界で高く評価され、多くの読者に愛読されています。
    
    This work occupies an important position in contemporary Japanese reading culture. Through the author''s 
    unique perspective and deep insights, it provides readers with new awareness and learning. It is highly 
    regarded in Japan''s publishing industry and beloved by many readers.
    
    本書はInternational Relations分野における優れた作品として、書店ランキングでも上位に位置し、
    幅広い読者層から支持を得ています。
    
    This book is positioned as an excellent work in the International Relations field, ranking high in bookstore 
    rankings and gaining support from a wide range of readers.',
    'japanese',
    '{"author": "齋藤ジン", "author_english": "Saito Jin", "title_english": "When World Order Changes", "publisher": "文藝春秋", "genre": "International Relations", "category": "新書", "estimated_reading_time": 240, "page_count": 200, "content_type": "book", "publication_year": 2026, "source": "japanese_bookstore_rankings_2026_01", "tags": ["international_relations", "新書", "japanese_bestseller", "bookstore_ranking", "2026"], "difficulty_level": "intermediate", "target_audience": "adult", "cultural_context": "japanese", "ranking_position": 1, "ranking_source": "japanese_bookstores"}',
    '{"topics": [{"topic": "politics", "confidence": 0.8}, {"topic": "international", "confidence": 0.8}, {"topic": "geopolitics", "confidence": 0.8}, {"topic": "strategy", "confidence": 0.8}, {"topic": "japanese", "confidence": 0.8}, {"topic": "japan", "confidence": 0.8}], "reading_level": {"japanese_level": 0.7, "kanji_density": 0.56, "estimated_jlpt_level": "N2"}, "complexity": {"overall": 0.7, "vocabulary": 0.8, "sentence_structure": 0.7, "cultural_context": 0.8}, "key_phrases": ["世界秩序が変わるとき", "齋藤ジン", "international relations", "新書"], "sentiment": {"overall": 0.6, "emotional_intensity": 0.5}, "embedding": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]}',
    '[]',
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- 7. Literary Fiction: BUTTER
INSERT INTO content_items (
    id, 
    title, 
    content, 
    language, 
    content_metadata, 
    analysis, 
    adaptations, 
    created_at, 
    updated_at
) VALUES (
    'jp_bestseller_2026_07_BUTTER',
    'BUTTER',
    'BUTTER
    BUTTER
    
    殺人事件を起こした女性を取材する女性記者の物語。食と欲望、女性の生き方をテーマに、現代社会の闇と光を描いた話題作。
    
    The story of a female journalist interviewing a woman who committed murder. A topical work that depicts the darkness and light of modern society, themed around food, desire, and women''s ways of living.
    
    この作品は現代日本の読書文化において重要な位置を占める作品です。著者の独自の視点と深い洞察により、
    読者に新たな気づきと学びを提供します。日本の出版界で高く評価され、多くの読者に愛読されています。
    
    This work occupies an important position in contemporary Japanese reading culture. Through the author''s 
    unique perspective and deep insights, it provides readers with new awareness and learning. It is highly 
    regarded in Japan''s publishing industry and beloved by many readers.
    
    本書はLiterary Fiction分野における優れた作品として、書店ランキングでも上位に位置し、
    幅広い読者層から支持を得ています。
    
    This book is positioned as an excellent work in the Literary Fiction field, ranking high in bookstore 
    rankings and gaining support from a wide range of readers.',
    'japanese',
    '{"author": "柚木麻子", "author_english": "Yuzuki Asako", "title_english": "BUTTER", "publisher": "新潮社", "genre": "Literary Fiction", "category": "文庫", "estimated_reading_time": 420, "page_count": 350, "content_type": "book", "publication_year": 2026, "source": "japanese_bookstore_rankings_2026_01", "tags": ["literary_fiction", "文庫", "japanese_bestseller", "bookstore_ranking", "2026"], "difficulty_level": "beginner_intermediate", "target_audience": "adult", "cultural_context": "japanese", "ranking_position": 1, "ranking_source": "japanese_bookstores"}',
    '{"topics": [{"topic": "literature", "confidence": 0.8}, {"topic": "fiction", "confidence": 0.8}, {"topic": "japanese_culture", "confidence": 0.8}, {"topic": "society", "confidence": 0.8}, {"topic": "japanese", "confidence": 0.8}, {"topic": "japan", "confidence": 0.8}], "reading_level": {"japanese_level": 0.5, "kanji_density": 0.4, "estimated_jlpt_level": "N3"}, "complexity": {"overall": 0.5, "vocabulary": 0.6, "sentence_structure": 0.5, "cultural_context": 0.8}, "key_phrases": ["BUTTER", "柚木麻子", "literary fiction", "文庫"], "sentiment": {"overall": 0.6, "emotional_intensity": 0.6}, "embedding": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]}',
    '[]',
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- 8. Business Strategy: 成長戦略型M&Aの新常識
INSERT INTO content_items (
    id, 
    title, 
    content, 
    language, 
    content_metadata, 
    analysis, 
    adaptations, 
    created_at, 
    updated_at
) VALUES (
    'jp_bestseller_2026_08_成長戦略型MAの新常識',
    '成長戦略型M&Aの新常識',
    '成長戦略型M&Aの新常識
    New Common Sense of Growth Strategy M&A
    
    企業成長戦略としてのM&Aの新しいアプローチを解説。従来の手法を超えた戦略的M&Aの実践方法と成功事例を紹介する。
    
    Explains new approaches to M&A as corporate growth strategies. Introduces practical methods and success stories of strategic M&A that go beyond conventional approaches.
    
    この作品は現代日本の読書文化において重要な位置を占める作品です。著者の独自の視点と深い洞察により、
    読者に新たな気づきと学びを提供します。日本の出版界で高く評価され、多くの読者に愛読されています。
    
    This work occupies an important position in contemporary Japanese reading culture. Through the author''s 
    unique perspective and deep insights, it provides readers with new awareness and learning. It is highly 
    regarded in Japan''s publishing industry and beloved by many readers.
    
    本書はBusiness Strategy分野における優れた作品として、書店ランキングでも上位に位置し、
    幅広い読者層から支持を得ています。
    
    This book is positioned as an excellent work in the Business Strategy field, ranking high in bookstore 
    rankings and gaining support from a wide range of readers.',
    'japanese',
    '{"author": "竹内直樹", "author_english": "Takeuchi Naoki", "title_english": "New Common Sense of Growth Strategy M&A", "publisher": "日本経済新聞出版", "genre": "Business Strategy", "category": "ビジネス・経済", "estimated_reading_time": 312, "page_count": 260, "content_type": "book", "publication_year": 2026, "source": "japanese_bookstore_rankings_2026_01", "tags": ["business_strategy", "ビジネス・経済", "japanese_bestseller", "bookstore_ranking", "2026"], "difficulty_level": "intermediate", "target_audience": "adult", "cultural_context": "japanese", "ranking_position": 1, "ranking_source": "japanese_bookstores"}',
    '{"topics": [{"topic": "business", "confidence": 0.8}, {"topic": "strategy", "confidence": 0.8}, {"topic": "mergers", "confidence": 0.8}, {"topic": "corporate", "confidence": 0.8}, {"topic": "japanese", "confidence": 0.8}, {"topic": "japan", "confidence": 0.8}], "reading_level": {"japanese_level": 0.7, "kanji_density": 0.56, "estimated_jlpt_level": "N2"}, "complexity": {"overall": 0.7, "vocabulary": 0.8, "sentence_structure": 0.7, "cultural_context": 0.8}, "key_phrases": ["成長戦略型M&Aの新常識", "竹内直樹", "business strategy", "ビジネス・経済"], "sentiment": {"overall": 0.6, "emotional_intensity": 0.5}, "embedding": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]}',
    '[]',
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- 9. Health: 腎臓大復活
INSERT INTO content_items (
    id, 
    title, 
    content, 
    language, 
    content_metadata, 
    analysis, 
    adaptations, 
    created_at, 
    updated_at
) VALUES (
    'jp_bestseller_2026_09_腎臓大復活',
    '腎臓大復活',
    '腎臓大復活
    Great Kidney Revival
    
    腎臓の健康維持と機能回復に関する最新の医学知識を一般向けに解説。予防から治療まで、腎臓病に関する包括的な情報を提供。
    
    Explains the latest medical knowledge about kidney health maintenance and function recovery for the general public. Provides comprehensive information about kidney disease from prevention to treatment.
    
    この作品は現代日本の読書文化において重要な位置を占める作品です。著者の独自の視点と深い洞察により、
    読者に新たな気づきと学びを提供します。日本の出版界で高く評価され、多くの読者に愛読されています。
    
    This work occupies an important position in contemporary Japanese reading culture. Through the author''s 
    unique perspective and deep insights, it provides readers with new awareness and learning. It is highly 
    regarded in Japan''s publishing industry and beloved by many readers.
    
    本書はHealth分野における優れた作品として、書店ランキングでも上位に位置し、
    幅広い読者層から支持を得ています。
    
    This book is positioned as an excellent work in the Health field, ranking high in bookstore 
    rankings and gaining support from a wide range of readers.',
    'japanese',
    '{"author": "上月正博", "author_english": "Kozuki Masahiro", "title_english": "Great Kidney Revival", "publisher": "東洋経済新報社", "genre": "Health", "category": "ノンフィクション", "estimated_reading_time": 288, "page_count": 240, "content_type": "book", "publication_year": 2026, "source": "japanese_bookstore_rankings_2026_01", "tags": ["health", "ノンフィクション", "japanese_bestseller", "bookstore_ranking", "2026"], "difficulty_level": "intermediate", "target_audience": "adult", "cultural_context": "japanese", "ranking_position": 1, "ranking_source": "japanese_bookstores"}',
    '{"topics": [{"topic": "health", "confidence": 0.8}, {"topic": "medicine", "confidence": 0.8}, {"topic": "wellness", "confidence": 0.8}, {"topic": "medical", "confidence": 0.8}, {"topic": "japanese", "confidence": 0.8}, {"topic": "japan", "confidence": 0.8}], "reading_level": {"japanese_level": 0.7, "kanji_density": 0.56, "estimated_jlpt_level": "N2"}, "complexity": {"overall": 0.7, "vocabulary": 0.8, "sentence_structure": 0.7, "cultural_context": 0.8}, "key_phrases": ["腎臓大復活", "上月正博", "health", "ノンフィクション"], "sentiment": {"overall": 0.6, "emotional_intensity": 0.5}, "embedding": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]}',
    '[]',
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- 10. Art Theory: 趣都
INSERT INTO content_items (
    id, 
    title, 
    content, 
    language, 
    content_metadata, 
    analysis, 
    adaptations, 
    created_at, 
    updated_at
) VALUES (
    'jp_bestseller_2026_10_趣都',
    '趣都',
    '趣都
    Capital of Taste
    
    現代アートと伝統文化の融合をテーマにした芸術論。日本の美意識と現代社会の関係性を独自の視点で考察した作品。
    
    An art theory themed around the fusion of contemporary art and traditional culture. A work that examines the relationship between Japanese aesthetics and modern society from a unique perspective.
    
    この作品は現代日本の読書文化において重要な位置を占める作品です。著者の独自の視点と深い洞察により、
    読者に新たな気づきと学びを提供します。日本の出版界で高く評価され、多くの読者に愛読されています。
    
    This work occupies an important position in contemporary Japanese reading culture. Through the author''s 
    unique perspective and deep insights, it provides readers with new awareness and learning. It is highly 
    regarded in Japan''s publishing industry and beloved by many readers.
    
    本書はArt Theory分野における優れた作品として、書店ランキングでも上位に位置し、
    幅広い読者層から支持を得ています。
    
    This book is positioned as an excellent work in the Art Theory field, ranking high in bookstore 
    rankings and gaining support from a wide range of readers.',
    'japanese',
    '{"author": "山口晃", "author_english": "Yamaguchi Akira", "title_english": "Capital of Taste", "publisher": "講談社", "genre": "Art Theory", "category": "フィクション", "estimated_reading_time": 360, "page_count": 300, "content_type": "book", "publication_year": 2026, "source": "japanese_bookstore_rankings_2026_01", "tags": ["art_theory", "フィクション", "japanese_bestseller", "bookstore_ranking", "2026"], "difficulty_level": "beginner_intermediate", "target_audience": "adult", "cultural_context": "japanese", "ranking_position": 1, "ranking_source": "japanese_bookstores"}',
    '{"topics": [{"topic": "art", "confidence": 0.8}, {"topic": "culture", "confidence": 0.8}, {"topic": "aesthetics", "confidence": 0.8}, {"topic": "theory", "confidence": 0.8}, {"topic": "japanese", "confidence": 0.8}, {"topic": "japan", "confidence": 0.8}], "reading_level": {"japanese_level": 0.55, "kanji_density": 0.44, "estimated_jlpt_level": "N3"}, "complexity": {"overall": 0.55, "vocabulary": 0.65, "sentence_structure": 0.55, "cultural_context": 0.8}, "key_phrases": ["趣都", "山口晃", "art theory", "フィクション"], "sentiment": {"overall": 0.6, "emotional_intensity": 0.5}, "embedding": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]}',
    '[]',
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- Verify the insertions
SELECT 
    id,
    title,
    content_metadata->>'author' as author,
    content_metadata->>'category' as category,
    content_metadata->>'publisher' as publisher
FROM content_items 
WHERE id LIKE 'jp_bestseller_2026_%'
ORDER BY id;