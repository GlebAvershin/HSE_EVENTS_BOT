-- Добавление тестовых событий

-- IT-мероприятия
INSERT INTO events (title, category, date_start, description, location, address, source_url, is_published, is_moderated, created_at, updated_at)
VALUES 
(
    'Python Meetup Нижний Новгород',
    'it',
    NOW() + INTERVAL '3 days 18 hours',
    'Встреча Python-разработчиков. Обсудим новые фичи Python 3.12, поделимся опытом и пообщаемся за чашкой кофе.',
    'IT-Park',
    'ул. Родионова, 165',
    'https://example.com/python-meetup',
    TRUE,
    TRUE,
    NOW(),
    NOW()
),
(
    'Хакатон: AI для бизнеса',
    'it',
    NOW() + INTERVAL '7 days 10 hours',
    '48-часовой хакатон по разработке AI-решений для бизнеса. Призовой фонд 500 000 рублей!',
    'Точка кипения',
    'Большая Покровская, 60',
    'https://example.com/ai-hackathon',
    TRUE,
    TRUE,
    NOW(),
    NOW()
),
(
    'Конференция DevOps Days',
    'it',
    NOW() + INTERVAL '14 days 9 hours',
    'Двухдневная конференция о DevOps практиках, CI/CD, контейнеризации и облачных технологиях.',
    'Конгресс-центр',
    'пл. Минина и Пожарского, 2',
    'https://example.com/devops-days',
    TRUE,
    TRUE,
    NOW(),
    NOW()
);

-- Развлекательные мероприятия
INSERT INTO events (title, category, date_start, description, location, address, source_url, is_published, is_moderated, created_at, updated_at)
VALUES 
(
    'Концерт: Би-2',
    'entertainment',
    NOW() + INTERVAL '5 days 20 hours',
    'Легендарная группа Би-2 с новой программой. Исполнят все хиты и новые песни.',
    'ДК ГАЗ',
    'пр. Ленина, 12',
    'https://example.com/bi2-concert',
    TRUE,
    TRUE,
    NOW(),
    NOW()
),
(
    'Stand-up: Слава Комиссаренко',
    'entertainment',
    NOW() + INTERVAL '10 days 19 hours',
    'Сольный концерт популярного стендап-комика. Новая программа "Всё сложно".',
    'Театр драмы',
    'ул. Большая Покровская, 13',
    'https://example.com/standup',
    TRUE,
    TRUE,
    NOW(),
    NOW()
),
(
    'Фестиваль уличной еды',
    'entertainment',
    NOW() + INTERVAL '2 days 12 hours',
    'Более 50 фудтраков с кухнями со всего мира. Живая музыка, мастер-классы и развлечения.',
    'Парк Швейцария',
    'ул. Белинского, 34',
    'https://example.com/food-fest',
    TRUE,
    TRUE,
    NOW(),
    NOW()
);
