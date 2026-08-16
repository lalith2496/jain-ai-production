CREATE TABLE IF NOT EXISTS content_items(
 id BIGSERIAL PRIMARY KEY, content_type VARCHAR(30) NOT NULL, title TEXT NOT NULL,
 slug TEXT UNIQUE NOT NULL, author TEXT, language VARCHAR(50) DEFAULT 'English',
 category VARCHAR(100), summary TEXT, rights_status VARCHAR(40) DEFAULT 'original',
 rights_note TEXT, status VARCHAR(20) DEFAULT 'draft', featured BOOLEAN DEFAULT FALSE,
 reading_minutes INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS content_sections(
 id BIGSERIAL PRIMARY KEY, content_id BIGINT REFERENCES content_items(id) ON DELETE CASCADE,
 section_index INTEGER NOT NULL, title TEXT, body TEXT NOT NULL, UNIQUE(content_id,section_index));
CREATE TABLE IF NOT EXISTS content_chunks(
 id BIGSERIAL PRIMARY KEY, content_id BIGINT REFERENCES content_items(id) ON DELETE CASCADE,
 section_id BIGINT REFERENCES content_sections(id) ON DELETE CASCADE, chunk_index INTEGER NOT NULL,
 content TEXT NOT NULL, embedding vector(384), metadata JSONB DEFAULT '{}'::jsonb);
CREATE INDEX IF NOT EXISTS content_items_type_status_idx ON content_items(content_type,status);

INSERT INTO content_items(content_type,title,slug,author,category,summary,rights_status,rights_note,status,featured,reading_minutes) VALUES
('book','Jainism: A Beginner’s Path','jainism-beginners-path','Jain AI Editorial','Beginner Guide','An original introductory reader on core Jain ideas.','original','Original educational text; not scripture or a translation.','published',TRUE,10),
('story','Mahavira and Chandakaushika','mahavira-chandakaushika','Jain AI Editorial','Values & Stories','A learner-friendly retelling centered on compassion and non-violence.','original','Original retelling of a traditional narrative.','published',TRUE,4),
('history','Mahavira in Jain Tradition','mahavira-in-jain-tradition','Jain AI Editorial','Jain History','A concise overview of Mahavira’s place in Jain tradition.','original','Original educational overview.','published',TRUE,5)
ON CONFLICT(slug) DO NOTHING;

INSERT INTO content_sections(content_id,section_index,title,body) SELECT id,1,'What is the Jain path?','Jainism presents a path of self-discipline aimed at freeing the soul from karmic bondage. Practice emphasizes careful conduct, self-awareness, restraint and compassion. This reader is an introduction, not a replacement for scripture or a teacher.' FROM content_items WHERE slug='jainism-beginners-path' ON CONFLICT DO NOTHING;
INSERT INTO content_sections(content_id,section_index,title,body) SELECT id,2,'Ahimsa — non-violence','Ahimsa means avoiding harm. In Jain practice its scope extends beyond humans and influences food, speech, occupations and everyday choices. The deeper idea is to cultivate awareness of how actions affect living beings.' FROM content_items WHERE slug='jainism-beginners-path' ON CONFLICT DO NOTHING;
INSERT INTO content_sections(content_id,section_index,title,body) SELECT id,3,'Aparigraha — limiting attachment','Aparigraha is commonly explained as non-possessiveness or non-attachment. It asks learners to examine the desire to accumulate, control and cling. Householder practice and ascetic practice differ in strictness.' FROM content_items WHERE slug='jainism-beginners-path' ON CONFLICT DO NOTHING;
INSERT INTO content_sections(content_id,section_index,title,body) SELECT id,4,'Anekantavada — many-sided understanding','Anekantavada encourages humility about complex reality. A statement may describe one aspect without exhausting the whole truth. In everyday life this can encourage careful listening and resistance to simplistic certainty.' FROM content_items WHERE slug='jainism-beginners-path' ON CONFLICT DO NOTHING;
INSERT INTO content_sections(content_id,section_index,title,body) SELECT id,1,'The encounter','Jain tradition tells of Chandakaushika, a dangerous serpent. Mahavira encounters the serpent without responding with fear or violence. The story is remembered as an illustration of calm and compassion.' FROM content_items WHERE slug='mahavira-chandakaushika' ON CONFLICT DO NOTHING;
INSERT INTO content_sections(content_id,section_index,title,body) SELECT id,2,'The lesson','Instead of meeting aggression with aggression, the story presents self-control as strength. It can be read as a lesson in ahimsa: when anger appears, a person still has a choice about how to respond.' FROM content_items WHERE slug='mahavira-chandakaushika' ON CONFLICT DO NOTHING;
INSERT INTO content_sections(content_id,section_index,title,body) SELECT id,1,'Mahavira’s place in the tradition','Mahavira is revered in Jainism as the twenty-fourth Tirthankara of the present time cycle. Jain tradition places him within a longer lineage rather than treating him as the founder of Jainism.' FROM content_items WHERE slug='mahavira-in-jain-tradition' ON CONFLICT DO NOTHING;
INSERT INTO content_sections(content_id,section_index,title,body) SELECT id,2,'Teaching and community','Accounts of Mahavira emphasize renunciation, disciplined conduct and liberation. Jain communities developed enduring traditions of monks, nuns and household followers. Later textual and institutional histories differ in detail across Jain traditions.' FROM content_items WHERE slug='mahavira-in-jain-tradition' ON CONFLICT DO NOTHING;
