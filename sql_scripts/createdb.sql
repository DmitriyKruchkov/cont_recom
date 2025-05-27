CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE channels_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_link TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    picture_link TEXT NOT NULL,
    processing_status BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    channel_id UUID NOT NULL,
    message TEXT,
    CONSTRAINT fk_channel FOREIGN KEY (channel_id) REFERENCES channels_status(id) ON DELETE CASCADE
);

CREATE TABLE post_topics (
    post_id INTEGER NOT NULL,
    topic TEXT NOT NULL,
    PRIMARY KEY (post_id, topic),
    CONSTRAINT fk_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);
