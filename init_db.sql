-- Создание таблицы alembic_version
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Создание таблицы users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX ix_users_telegram_id ON users(telegram_id);

-- Создание таблицы events
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    date_start TIMESTAMP NOT NULL,
    date_end TIMESTAMP,
    location VARCHAR(500),
    address TEXT,
    source_url TEXT,
    image_url TEXT,
    is_moderated BOOLEAN DEFAULT FALSE NOT NULL,
    is_published BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX ix_events_category ON events(category);
CREATE INDEX ix_events_date_start ON events(date_start);
CREATE INDEX ix_events_is_published ON events(is_published);

-- Создание таблицы user_settings
CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notify_new_events BOOLEAN DEFAULT TRUE NOT NULL,
    notify_friend_going BOOLEAN DEFAULT TRUE NOT NULL,
    notify_event_reminder BOOLEAN DEFAULT TRUE NOT NULL,
    preferred_categories VARCHAR[],
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX ix_user_settings_user_id ON user_settings(user_id);

-- Создание таблицы friendships
CREATE TABLE friendships (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    friend_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, friend_id)
);
CREATE INDEX ix_friendships_user_id ON friendships(user_id);
CREATE INDEX ix_friendships_friend_id ON friendships(friend_id);

-- Создание таблицы event_attendances
CREATE TABLE event_attendances (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'going' NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, event_id)
);
CREATE INDEX ix_event_attendances_user_id ON event_attendances(user_id);
CREATE INDEX ix_event_attendances_event_id ON event_attendances(event_id);

-- Создание таблицы notifications
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    related_event_id INTEGER REFERENCES events(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX ix_notifications_user_id ON notifications(user_id);
CREATE INDEX ix_notifications_created_at ON notifications(created_at);

-- Создание таблицы event_sources
CREATE TABLE event_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url TEXT,
    parser_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    last_parsed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Вставка версии миграции
INSERT INTO alembic_version (version_num) VALUES ('001');
